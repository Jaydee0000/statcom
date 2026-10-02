from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.annotations import (
    AnnotationRead, AnnotationWrite, DuplicateAnnotation, MatchContextRead,
    SkillRead, SkillWrite,
)
from app.services.annotations import (
    archive_annotation, create_skill, duplicate_annotation, get_annotation,
    list_annotations, list_skills, match_context, restore_annotation, save_annotation,
)

router = APIRouter(tags=["annotations"])
DB = Annotated[Session, Depends(get_db)]


@router.get("/annotation-library/skills", response_model=list[SkillRead])
def skills(db: DB):
    return list_skills(db)


@router.post("/annotation-library/skills", response_model=SkillRead, status_code=201)
def add_skill(payload: SkillWrite, db: DB):
    return create_skill(db, payload)


@router.get("/matches/{match_id}/annotation-context", response_model=MatchContextRead)
def context(match_id: UUID, db: DB):
    return match_context(db, match_id)


@router.get("/annotation-sessions/{session_id}/annotations", response_model=list[AnnotationRead])
def session_annotations(session_id: UUID, db: DB):
    return list_annotations(db, session_id)


@router.post("/annotation-sessions/{session_id}/annotations", response_model=AnnotationRead, status_code=201)
def create_annotation(session_id: UUID, payload: AnnotationWrite, db: DB):
    return save_annotation(db, session_id, payload)


@router.get("/annotations/{annotation_id}/aggregate", response_model=AnnotationRead)
def annotation(annotation_id: UUID, db: DB):
    return get_annotation(db, annotation_id)


@router.patch("/annotations/{annotation_id}/aggregate", response_model=AnnotationRead)
def update_annotation(annotation_id: UUID, payload: AnnotationWrite, db: DB):
    current = get_annotation(db, annotation_id)
    return save_annotation(db, current["annotation_session_id"], payload, annotation_id)


@router.post("/annotations/{annotation_id}/duplicate", response_model=AnnotationRead, status_code=201)
def duplicate(annotation_id: UUID, payload: DuplicateAnnotation, db: DB):
    return duplicate_annotation(db, annotation_id, payload)


@router.delete("/annotations/{annotation_id}/archive", status_code=204)
def archive(annotation_id: UUID, db: DB):
    archive_annotation(db, annotation_id)
    return Response(status_code=204)


@router.post("/annotations/{annotation_id}/restore", response_model=AnnotationRead)
def restore(annotation_id: UUID, db: DB):
    return restore_annotation(db, annotation_id)
