"""Transactional annotation aggregates and definition/context queries."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Annotation, AnnotationFieldValue, AnnotationParticipant, AnnotationSession,
    AnnotationTag, Match, MatchParticipant, Player, PlayerTeamMembership,
    SkillDefinition, SkillFieldDefinition, Tag, Team, Video,
)
from app.schemas.annotations import AnnotationWrite, DuplicateAnnotation, SkillWrite
from app.services.crud import CrudService
from app.services.errors import DomainError


def _commit(db: Session, record=None):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError("Record conflicts with an existing record or relationship constraint", 409) from exc
    if record is not None:
        db.refresh(record)
    return record


def _annotation(db: Session, annotation_id: UUID, *, lock=False, include_deleted=False):
    statement = select(Annotation).where(Annotation.id == annotation_id)
    if lock:
        statement = statement.with_for_update()
    record = db.scalar(statement)
    if record is None or (record.deleted_at is not None and not include_deleted):
        raise DomainError("Annotation not found", 404)
    return record


def annotation_dict(db: Session, record: Annotation):
    tags = db.execute(select(Tag).join(AnnotationTag, AnnotationTag.tag_id == Tag.id).where(
        AnnotationTag.annotation_id == record.id).order_by(Tag.name)).scalars().all()
    participants = db.execute(select(AnnotationParticipant, Player).outerjoin(
        Player, Player.id == AnnotationParticipant.player_id).where(
        AnnotationParticipant.annotation_id == record.id).order_by(
        AnnotationParticipant.role, Player.last_name, Player.first_name)).all()
    values = db.scalars(select(AnnotationFieldValue).where(
        AnnotationFieldValue.annotation_id == record.id).order_by(AnnotationFieldValue.field_definition_id)).all()
    return {
        "id": record.id, "annotation_session_id": record.annotation_session_id,
        "match_id": record.match_id, "video_id": record.video_id,
        "skill_definition_id": record.skill_definition_id,
        "video_start_time": record.video_start_time, "video_end_time": record.video_end_time,
        "match_period": record.match_period, "match_time": record.match_time,
        "notes": record.notes, "review_status": record.review_status,
        "created_by": record.created_by, "created_at": record.created_at, "updated_at": record.updated_at,
        "tags": [{"id": tag.id, "name": tag.name, "category": tag.category, "color": tag.color} for tag in tags],
        "participants": [{"id": link.id, "player_id": player.id if player else None,
                          "first_name": player.first_name if player else None,
                          "last_name": player.last_name if player else None, "role": link.role}
                         for link, player in participants],
        "field_values": [{"id": value.id, "field_definition_id": value.field_definition_id,
                          "value": value.value} for value in values],
    }


def list_annotations(db: Session, session_id: UUID):
    session = db.get(AnnotationSession, session_id)
    if session is None:
        raise DomainError("Annotation session not found", 404)
    records = db.scalars(select(Annotation).where(
        Annotation.annotation_session_id == session_id, Annotation.deleted_at.is_(None)).order_by(
        Annotation.video_start_time, Annotation.created_at, Annotation.id)).all()
    return [annotation_dict(db, record) for record in records]


def get_annotation(db: Session, annotation_id: UUID):
    return annotation_dict(db, _annotation(db, annotation_id))


def _validated_parts(db: Session, session: AnnotationSession, payload: AnnotationWrite, existing=None):
    if (payload.video_id, payload.match_id) != (session.video_id, session.match_id):
        raise DomainError("Annotation video and match must match its session")
    video = db.get(Video, payload.video_id)
    if video is None:
        raise DomainError("Video reference does not exist")
    CrudService._check_duration(video, payload.video_start_time, payload.video_end_time)
    skill = db.get(SkillDefinition, payload.skill_definition_id)
    if skill is None or (not skill.is_active and (existing is None or existing.skill_definition_id != skill.id)):
        raise DomainError("Active skill definition does not exist")
    fields = {field.id: field for field in db.scalars(select(SkillFieldDefinition).where(
        SkillFieldDefinition.skill_definition_id == skill.id)).all()}
    values = {item.field_definition_id: item.value for item in payload.field_values}
    unknown = set(values) - set(fields)
    if unknown:
        raise DomainError("Every custom value must belong to the selected skill")
    missing = {
        field.label for field in fields.values()
        if field.required and (
            field.id not in values
            or (isinstance(values[field.id], str) and not values[field.id].strip())
            or values[field.id] == []
        )
    }
    if missing:
        raise DomainError("Required skill fields are missing: " + ", ".join(sorted(missing)))
    validator = CrudService(db, AnnotationFieldValue, None)
    match_player_ids = set(db.scalars(select(MatchParticipant.player_id).where(
        MatchParticipant.match_id == payload.match_id)))
    match = db.get(Match, payload.match_id)
    match_team_ids = {match.home_team_id, match.away_team_id}
    prepared_values = []
    for field_id, value in values.items():
        field = fields[field_id]
        validator._validate_value(field, value)
        player_value_id = team_value_id = None
        if field.data_type.value == "player_reference":
            player_value_id = UUID(value)
            if player_value_id not in match_player_ids:
                raise DomainError("Referenced player must be a participant in this match")
            value = str(player_value_id)
        elif field.data_type.value == "team_reference":
            team_value_id = UUID(value)
            if team_value_id not in match_team_ids:
                raise DomainError("Referenced team must belong to this match")
            value = str(team_value_id)
        prepared_values.append((field_id, value, player_value_id, team_value_id))
    participant_ids = {item.player_id for item in payload.participants if item.player_id is not None}
    if participant_ids - match_player_ids:
        raise DomainError("Annotation participants must belong to the match")
    tags = []
    for tag_id in payload.tag_ids:
        tag = db.get(Tag, tag_id)
        existing_tag = existing and db.scalar(select(AnnotationTag.id).where(
            AnnotationTag.annotation_id == existing.id, AnnotationTag.tag_id == tag_id))
        if tag is None or (not tag.is_active and not existing_tag):
            raise DomainError("Tag reference is missing or archived")
        tags.append(tag)
    return prepared_values


def save_annotation(db: Session, session_id: UUID, payload: AnnotationWrite, annotation_id: UUID | None = None):
    session = db.scalar(select(AnnotationSession).where(AnnotationSession.id == session_id).with_for_update())
    if session is None:
        raise DomainError("Annotation session not found", 404)
    existing = _annotation(db, annotation_id, lock=True) if annotation_id else None
    if existing is not None and existing.annotation_session_id != session.id:
        raise DomainError("Annotation does not belong to this session")
    prepared_values = _validated_parts(db, session, payload, existing)
    if existing is None:
        record = Annotation(annotation_session_id=session.id)
        db.add(record)
    else:
        record = existing
    for key in ("match_id", "video_id", "skill_definition_id", "video_start_time", "video_end_time",
                "match_period", "match_time", "notes", "review_status"):
        setattr(record, key, getattr(payload, key))
    if existing is None:
        record.created_by = payload.created_by
    db.flush()
    if existing is not None:
        db.execute(delete(AnnotationFieldValue).where(AnnotationFieldValue.annotation_id == record.id))
        db.execute(delete(AnnotationParticipant).where(AnnotationParticipant.annotation_id == record.id))
        db.execute(delete(AnnotationTag).where(AnnotationTag.annotation_id == record.id))
    db.add_all(AnnotationTag(annotation_id=record.id, tag_id=tag_id) for tag_id in payload.tag_ids)
    db.add_all(AnnotationParticipant(annotation_id=record.id, player_id=item.player_id, role=item.role)
               for item in payload.participants)
    db.add_all(AnnotationFieldValue(annotation_id=record.id, field_definition_id=field_id, value=value,
                                    player_value_id=player_id, team_value_id=team_id)
               for field_id, value, player_id, team_id in prepared_values)
    _commit(db, record)
    return annotation_dict(db, record)


def duplicate_annotation(db: Session, annotation_id: UUID, payload: DuplicateAnnotation):
    original = _annotation(db, annotation_id)
    aggregate = annotation_dict(db, original)
    write = AnnotationWrite(
        match_id=original.match_id, video_id=original.video_id,
        skill_definition_id=original.skill_definition_id,
        video_start_time=payload.video_start_time, video_end_time=payload.video_end_time,
        match_time=payload.match_time, match_period=payload.match_period or original.match_period,
        notes=original.notes, review_status="DRAFT", created_by=original.created_by,
        tag_ids=[tag["id"] for tag in aggregate["tags"]],
        participants=[{"player_id": item["player_id"], "role": item["role"]} for item in aggregate["participants"]],
        field_values=[{"field_definition_id": item["field_definition_id"], "value": item["value"]}
                      for item in aggregate["field_values"]],
    )
    return save_annotation(db, original.annotation_session_id, write)


def archive_annotation(db: Session, annotation_id: UUID):
    record = _annotation(db, annotation_id, lock=True)
    record.deleted_at = datetime.now(timezone.utc)
    _commit(db)


def restore_annotation(db: Session, annotation_id: UUID):
    record = _annotation(db, annotation_id, lock=True, include_deleted=True)
    record.deleted_at = None
    _commit(db, record)
    return annotation_dict(db, record)


def list_skills(db: Session):
    skills = db.scalars(select(SkillDefinition).where(SkillDefinition.is_active.is_(True)).order_by(
        SkillDefinition.category, SkillDefinition.name, SkillDefinition.version.desc())).all()
    return [skill_dict(db, skill) for skill in skills]


def skill_dict(db: Session, skill: SkillDefinition):
    fields = db.scalars(select(SkillFieldDefinition).where(
        SkillFieldDefinition.skill_definition_id == skill.id).order_by(
        SkillFieldDefinition.display_order, SkillFieldDefinition.id)).all()
    return {"id": skill.id, "name": skill.name, "description": skill.description,
            "category": skill.category, "version": skill.version, "is_active": skill.is_active,
            "fields": [{"id": field.id, "key": field.key, "label": field.label,
                        "data_type": field.data_type, "required": field.required,
                        "description": field.description, "options": field.options,
                        "display_order": field.display_order} for field in fields]}


def create_skill(db: Session, payload: SkillWrite):
    skill = SkillDefinition(name=payload.name, description=payload.description, category=payload.category,
                            version=payload.version, is_active=True, created_by=payload.created_by)
    db.add(skill)
    try:
        db.flush()
        db.add_all(SkillFieldDefinition(skill_definition_id=skill.id, **field.model_dump()) for field in payload.fields)
        _commit(db, skill)
    except IntegrityError as exc:
        db.rollback()
        raise DomainError("Skill name/version or field key already exists", 409) from exc
    return skill_dict(db, skill)


def match_context(db: Session, match_id: UUID):
    match = db.get(Match, match_id)
    if match is None:
        raise DomainError("Match not found", 404)
    teams = db.scalars(select(Team).where(Team.id.in_([match.home_team_id, match.away_team_id])).order_by(Team.name)).all()
    rows = db.execute(select(MatchParticipant, Player).join(Player, Player.id == MatchParticipant.player_id).where(
        MatchParticipant.match_id == match_id).order_by(Player.last_name, Player.first_name)).all()
    memberships = {(membership.player_id, membership.team_id): membership.jersey_number for membership in db.scalars(
        select(PlayerTeamMembership).where(PlayerTeamMembership.player_id.in_([player.id for _, player in rows]),
                                           PlayerTeamMembership.team_id.in_([match.home_team_id, match.away_team_id]),
                                           PlayerTeamMembership.start_date <= match.match_date,
                                           (PlayerTeamMembership.end_date.is_(None)) |
                                           (PlayerTeamMembership.end_date >= match.match_date))).all()}
    return {"match_id": match.id, "teams": [{"id": team.id, "name": team.name} for team in teams],
            "players": [{"participant_id": participant.id, "player_id": player.id,
                         "team_id": participant.team_id, "first_name": player.first_name,
                         "last_name": player.last_name,
                         "jersey_number": memberships.get((player.id, participant.team_id)),
                         "starter": participant.starter, "position_played": participant.position_played}
                        for participant, player in rows]}
