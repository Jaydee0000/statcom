from datetime import datetime, timezone
import math
import unicodedata
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    Annotation, AnnotationFieldValue, AnnotationSession,
    AnnotationTag, FieldType, Match, MatchParticipant, Player, SkillDefinition,
    SkillFieldDefinition, Tag, Team, Video,
)
from app.repositories.crud import Repository
from app.services.errors import DomainError


def normalize_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


class CrudService:
    def __init__(self, db: Session, model, schema):
        self.db, self.model, self.schema = db, model, schema
        self.repo = Repository(db, model)

    def get(self, record_id):
        row = self.repo.get(record_id)
        if row is None or getattr(row, "deleted_at", None) is not None:
            raise DomainError("Record not found", 404)
        return row

    def list(self, offset, limit, filters):
        for key in filters:
            if key not in self.model.__table__.columns:
                raise DomainError(f"Filter '{key}' does not apply to this resource")
        return self.repo.list(offset, limit, filters)

    def _reference(self, model, record_id):
        # Locks serialize edits to definitions/parents against new dependent records.
        record = self.db.scalar(select(model).where(model.id == record_id).with_for_update())
        if record is None or getattr(record, "deleted_at", None) is not None:
            raise DomainError(f"{model.__name__} reference does not exist")
        return record

    def _validate(self, values, existing=None):
        # Validate all FK targets, including nullable creator/user references.
        by_table = {mapper.local_table.name: mapper.class_ for mapper in Base.registry.mappers}
        for column in self.model.__table__.columns:
            if column.name not in values or values[column.name] is None:
                continue
            for fk in column.foreign_keys:
                if fk.column.name == "id":
                    self._reference(by_table[fk.column.table.name], values[column.name])

        if existing:
            # Reparenting a historical record is not a basic edit: create a new record.
            for column in self.model.__table__.columns:
                if column.foreign_keys and column.name in values and values[column.name] != getattr(existing, column.name):
                    raise DomainError(f"{column.name} cannot be reassigned; create a new record")

        if self.model is Tag:
            values["normalized_name"] = normalize_name(values["name"])
            values["scope"] = normalize_name(values["scope"])
            values["archived_at"] = None if values["is_active"] else (
                getattr(existing, "archived_at", None) or datetime.now(timezone.utc)
            )

        if self.model is MatchParticipant:
            match = self._reference(Match, values["match_id"])
            if values["team_id"] not in (match.home_team_id, match.away_team_id):
                raise DomainError("Participant team must be a team in this match")

        if self.model is AnnotationSession:
            video = self._reference(Video, values["video_id"])
            if video.match_id != values["match_id"]:
                raise DomainError("Session match must match the video's match")
            self._check_duration(video, values["last_playback_position"])
            transitions = {
                "NOT_STARTED": {"IN_PROGRESS"},
                "IN_PROGRESS": {"READY_FOR_REVIEW"},
                "READY_FOR_REVIEW": {"IN_PROGRESS", "REVIEWED"},
                "REVIEWED": {"IN_PROGRESS"},
            }
            if existing and values["status"] != existing.status:
                if values["status"] not in transitions[existing.status]:
                    raise DomainError(f"Cannot change session from {existing.status} to {values['status']}", 409)
            elif not existing and values["status"] not in ("NOT_STARTED", "IN_PROGRESS"):
                raise DomainError("New sessions must be Not Started or In Progress", 409)
            # Preserve the last review timestamp when reopening for corrections.
            if values["status"] == "REVIEWED" and (not existing or existing.status != "REVIEWED"):
                values["completed_at"] = datetime.now(timezone.utc)
            elif existing:
                values["completed_at"] = existing.completed_at

        if self.model is Annotation:
            session = self._reference(AnnotationSession, values["annotation_session_id"])
            if (session.video_id, session.match_id) != (values["video_id"], values["match_id"]):
                raise DomainError("Annotation video and match must match its session")
            video = self._reference(Video, values["video_id"])
            self._check_duration(video, values["video_start_time"], values["video_end_time"])
            if values["skill_definition_id"]:
                skill = self._reference(SkillDefinition, values["skill_definition_id"])
                if not existing and not skill.is_active:
                    raise DomainError("Archived skills cannot be used for new annotations")
            if values["review_status"] != "DRAFT":
                self._check_required_fields(values["skill_definition_id"], existing)

        if self.model is Video and existing and values["duration_seconds"] is not None:
            duration = values["duration_seconds"]
            session = self.db.scalar(select(AnnotationSession.id).where(
                AnnotationSession.video_id == existing.id,
                AnnotationSession.last_playback_position > duration))
            annotation = self.db.scalar(select(Annotation.id).where(
                Annotation.video_id == existing.id,
                (Annotation.video_start_time > duration) | (Annotation.video_end_time > duration)))
            if session or annotation:
                raise DomainError("Duration would invalidate saved session/annotation timestamps")

        if self.model is SkillDefinition and existing:
            used = self.db.scalar(select(Annotation.id).where(Annotation.skill_definition_id == existing.id).limit(1))
            if used and any(values[key] != getattr(existing, key) for key in ("name", "description", "category", "version")):
                raise DomainError("Used skills are immutable; create a new skill version", 409)

        if self.model is SkillFieldDefinition:
            used = self.db.scalar(select(Annotation.id).where(
                Annotation.skill_definition_id == values["skill_definition_id"]).limit(1))
            structural = ("key", "data_type", "required", "options")
            if used and (existing is None or any(values[key] != getattr(existing, key) for key in structural)):
                raise DomainError("Fields of a used skill are immutable; create a new skill version", 409)

        if self.model is AnnotationTag:
            tag = self._reference(Tag, values["tag_id"])
            if not existing and not tag.is_active:
                raise DomainError("Archived tags cannot be attached to new annotations")

        if self.model is AnnotationFieldValue:
            annotation = self._reference(Annotation, values["annotation_id"])
            field = self._reference(SkillFieldDefinition, values["field_definition_id"])
            if annotation.skill_definition_id != field.skill_definition_id:
                raise DomainError("Field definition must belong to the annotation's skill")
            self._validate_value(field, values["value"])
            values["player_value_id"] = None
            values["team_value_id"] = None
            if field.data_type in (FieldType.PLAYER_REFERENCE, FieldType.TEAM_REFERENCE):
                reference_id = UUID(values["value"])
                values["value"] = str(reference_id)
                key = "player_value_id" if field.data_type == FieldType.PLAYER_REFERENCE else "team_value_id"
                values[key] = reference_id

    @staticmethod
    def _check_duration(video, *positions):
        if video.duration_seconds is not None and any(p is not None and p > video.duration_seconds for p in positions):
            raise DomainError("Timestamp cannot exceed video duration")

    def _check_required_fields(self, skill_id, annotation):
        if skill_id is None:
            return
        required = set(self.db.scalars(select(SkillFieldDefinition.id).where(
            SkillFieldDefinition.skill_definition_id == skill_id,
            SkillFieldDefinition.required.is_(True))))
        recorded = set() if annotation is None else set(self.db.scalars(select(AnnotationFieldValue.field_definition_id).where(
            AnnotationFieldValue.annotation_id == annotation.id)))
        if required - recorded:
            raise DomainError("Required skill fields must have values before review")

    def _validate_value(self, field, value):
        kind = field.data_type
        valid = False
        if kind == FieldType.BOOLEAN:
            valid = type(value) is bool
        elif kind in (FieldType.NUMBER, FieldType.RATING):
            valid = type(value) in (int, float) and math.isfinite(value)
        elif kind == FieldType.TEXT:
            valid = isinstance(value, str)
        elif kind == FieldType.SINGLE_SELECT:
            valid = isinstance(value, str) and value in (field.options or [])
        elif kind == FieldType.MULTI_SELECT:
            valid = (isinstance(value, list) and all(isinstance(v, str) and v in (field.options or []) for v in value)
                     and len(set(value)) == len(value))
        elif kind in (FieldType.PLAYER_REFERENCE, FieldType.TEAM_REFERENCE):
            try:
                reference_id = UUID(value) if isinstance(value, str) else None
            except ValueError:
                reference_id = None
            if reference_id:
                self._reference(Player if kind == FieldType.PLAYER_REFERENCE else Team, reference_id)
                valid = True
        if not valid:
            raise DomainError(f"Value is invalid for field type '{kind.value}'")

    def _commit(self, record=None):
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainError("Record conflicts with an existing record or a relationship constraint", 409) from exc
        if record is not None:
            self.db.refresh(record)
        return record

    def create(self, payload):
        values = payload.model_dump()
        self._validate(values)
        return self._commit(self.repo.add(values))

    def update(self, record_id, payload):
        record = self.repo.get(record_id, lock=True)
        if record is None or getattr(record, "deleted_at", None) is not None:
            raise DomainError("Record not found", 404)
        merged = {key: getattr(record, key) for key in self.schema.model_fields}
        merged.update(payload.model_dump(exclude_unset=True))
        try:
            values = self.schema.model_validate(merged).model_dump()
        except ValidationError as exc:
            raise DomainError("; ".join(error["msg"] for error in exc.errors())) from exc
        self._validate(values, record)
        for key, value in values.items():
            setattr(record, key, value)
        return self._commit(record)

    def delete(self, record_id):
        record = self.repo.get(record_id, lock=True)
        if record is None or getattr(record, "deleted_at", None) is not None:
            raise DomainError("Record not found", 404)
        if self.model is Annotation:
            record.deleted_at = datetime.now(timezone.utc)
        elif self.model in (Tag, SkillDefinition):
            record.is_active = False
            if self.model is Tag:
                record.archived_at = record.archived_at or datetime.now(timezone.utc)
        else:
            if self.model is SkillFieldDefinition:
                self._reference(SkillDefinition, record.skill_definition_id)
                if self.db.scalar(select(Annotation.id).where(Annotation.skill_definition_id == record.skill_definition_id).limit(1)):
                    raise DomainError("Cannot delete fields from a used skill", 409)
            if self.model is AnnotationFieldValue:
                annotation = self._reference(Annotation, record.annotation_id)
                field = self._reference(SkillFieldDefinition, record.field_definition_id)
                if field.required and annotation.review_status != "DRAFT":
                    raise DomainError("Return the annotation to DRAFT before removing a required value", 409)
            self.repo.delete(record)
        self._commit()
