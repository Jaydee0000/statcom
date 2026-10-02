"""Shared CRUD transport; resource schemas stay explicit and business rules live in services."""
from copy import deepcopy
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, create_model
from sqlalchemy.orm import Session

from app.db.session import get_db
from app import models as m
from app.schemas import entities as s
from app.services.crud import CrudService

RESOURCES = (
    ("teams", m.Team, s.TeamCreate),
    ("players", m.Player, s.PlayerCreate),
    ("memberships", m.PlayerTeamMembership, s.MembershipCreate),
    ("seasons", m.Season, s.SeasonCreate),
    ("competitions", m.Competition, s.CompetitionCreate),
    ("matches", m.Match, s.MatchCreate),
    ("match-participants", m.MatchParticipant, s.MatchParticipantCreate),
    ("videos", m.Video, s.VideoCreate),
    ("annotation-sessions", m.AnnotationSession, s.SessionCreate),
    ("tags", m.Tag, s.TagCreate),
    ("skills", m.SkillDefinition, s.SkillCreate),
    ("skill-fields", m.SkillFieldDefinition, s.SkillFieldCreate),
    ("annotations", m.Annotation, s.AnnotationCreate),
    ("annotation-participants", m.AnnotationParticipant, s.AnnotationParticipantCreate),
    ("annotation-tags", m.AnnotationTag, s.AnnotationTagCreate),
    ("annotation-field-values", m.AnnotationFieldValue, s.FieldValueCreate),
)


class PatchBase(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


def resource_router(path, model, schema):
    # PATCH keeps field constraints, while merged records undergo complete create-schema validation.
    patch_fields = {}
    for name, field in schema.model_fields.items():
        copied = deepcopy(field)
        copied.default = None
        patch_fields[name] = (field.annotation | None, copied)
    patch_schema = create_model(f"{model.__name__}Update", __base__=PatchBase, **patch_fields)
    read_fields = {"id": (UUID, ...)}
    for name in ("created_at", "updated_at", "deleted_at", "archived_at"):
        if hasattr(model, name):
            read_fields[name] = (datetime | None, None)
    if model is m.Tag:
        read_fields["normalized_name"] = (str, ...)
    read_schema = create_model(f"{model.__name__}Read", __base__=schema, **read_fields)
    router = APIRouter(prefix=f"/{path}", tags=[path])

    def service(db: Annotated[Session, Depends(get_db)]):
        return CrudService(db, model, schema)

    @router.post("", response_model=read_schema, status_code=201, name=f"create_{path}")
    def create(payload: schema, crud: Annotated[CrudService, Depends(service)]):
        return crud.create(payload)

    @router.get("", response_model=list[read_schema], name=f"list_{path}")
    def list_records(
        crud: Annotated[CrudService, Depends(service)],
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        match_id: UUID | None = None,
        video_id: UUID | None = None,
        player_id: UUID | None = None,
        team_id: UUID | None = None,
        annotation_id: UUID | None = None,
        annotation_session_id: UUID | None = None,
        skill_definition_id: UUID | None = None,
        is_active: bool | None = None,
    ):
        filters = dict(match_id=match_id, video_id=video_id, player_id=player_id,
                       team_id=team_id, annotation_id=annotation_id,
                       annotation_session_id=annotation_session_id,
                       skill_definition_id=skill_definition_id, is_active=is_active)
        return crud.list(offset, limit, {key: value for key, value in filters.items() if value is not None})

    @router.get("/{record_id}", response_model=read_schema, name=f"get_{path}")
    def get(record_id: UUID, crud: Annotated[CrudService, Depends(service)]):
        return crud.get(record_id)

    @router.patch("/{record_id}", response_model=read_schema, name=f"update_{path}")
    def update(record_id: UUID, payload: patch_schema, crud: Annotated[CrudService, Depends(service)]):
        return crud.update(record_id, payload)

    @router.delete("/{record_id}", status_code=204, name=f"delete_{path}")
    def delete(record_id: UUID, crud: Annotated[CrudService, Depends(service)]):
        crud.delete(record_id)
        return Response(status_code=204)

    return router


api_router = APIRouter(prefix="/api/v1")
from app.api.video_workflow import router as video_workflow_router
from app.api.annotations import router as annotations_router
from app.api.metrics import router as metrics_router
from app.api.reporting import router as reporting_router
api_router.include_router(video_workflow_router)
api_router.include_router(annotations_router)
api_router.include_router(metrics_router)
api_router.include_router(reporting_router)
for resource in RESOURCES:
    api_router.include_router(resource_router(*resource))
