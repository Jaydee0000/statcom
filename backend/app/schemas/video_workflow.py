from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.schemas.entities import VideoCreate, SessionCreate


class VideoRead(VideoCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime


class SessionRead(SessionCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime


class WorkflowRow(BaseModel):
    video: VideoRead
    session: SessionRead | None
    match_name: str
    match_date: str
