from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Video
from app.schemas.entities import VideoCreate
from app.schemas.video_workflow import VideoRead, SessionRead, WorkflowRow
from app.services.crud import CrudService
from app.services.videos import upload_video, media_path, start_session, workflow

router = APIRouter(tags=["video-workflow"])
DB = Annotated[Session, Depends(get_db)]


@router.post("/videos/upload", response_model=VideoRead, status_code=201)
def upload(db: DB, file: Annotated[UploadFile, File()], match_id: Annotated[UUID, Form()],
           period: Annotated[str | None, Form(max_length=50)] = None,
           video_time_offset: Annotated[float, Form(ge=0, allow_inf_nan=False)] = 0,
           match_time_offset: Annotated[float, Form(ge=0, allow_inf_nan=False)] = 0,
           uploaded_by: Annotated[UUID | None, Form()] = None):
    return upload_video(db, file, dict(match_id=match_id, period=period,
        video_time_offset=video_time_offset, match_time_offset=match_time_offset, uploaded_by=uploaded_by))


@router.get("/videos/workflow", response_model=list[WorkflowRow])
def list_workflow(db: DB, completed: bool = False, offset: Annotated[int, Query(ge=0)] = 0,
                  limit: Annotated[int, Query(ge=1, le=100)] = 50):
    return workflow(db, completed, offset, limit)


@router.get("/videos/{video_id}/media")
@router.head("/videos/{video_id}/media", include_in_schema=False)
def media(video_id: UUID, db: DB):
    video = CrudService(db, Video, VideoCreate).get(video_id)
    return FileResponse(media_path(video), media_type=video.mime_type,
                        headers={"X-Content-Type-Options": "nosniff"})


@router.post("/videos/{video_id}/start", response_model=SessionRead)
def start(video_id: UUID, db: DB):
    return start_session(db, video_id)
