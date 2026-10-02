"""Local media and the anonymous development annotation workflow."""
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import aliased
from app.core.config import get_settings
from app.models import Video, Match, Team, AnnotationSession
from app.schemas.entities import VideoCreate, SessionCreate
from app.schemas.video_workflow import VideoRead, SessionRead
from app.services.crud import CrudService
from app.services.errors import DomainError

FORMATS = {".mp4": ("video/mp4", "mov"), ".mov": ("video/quicktime", "mov"),
           ".webm": ("video/webm", "webm")}


def media_path(video):
    key = video.storage_key or ""
    if not re.fullmatch(r"[0-9a-f]{32}\.(mp4|mov|webm)", key):
        raise DomainError("Video file is unavailable", 404)
    root = get_settings().video_storage_path.resolve()
    path = (root / key).resolve()
    if path.parent != root or not path.is_file():
        raise DomainError("Video file is unavailable", 404)
    return path


def upload_video(db, file, metadata):
    settings = get_settings()
    original = file.filename or ""
    # Treat all client filenames as untrusted metadata, including Windows paths.
    if (not original or len(original) > 255 or any(c in original for c in "/\\")
            or any(ord(c) < 32 for c in original)):
        raise DomainError("Choose a video with a plain filename, without paths")
    suffix = Path(original).suffix.lower()
    if suffix not in FORMATS:
        raise DomainError("Unsupported video format. Use MP4, MOV, or WebM", 415)
    try:
        VideoCreate(**metadata, original_filename=original)
    except ValidationError as exc:
        raise DomainError("Invalid video metadata: " + "; ".join(e["msg"] for e in exc.errors())) from exc
    crud = CrudService(db, Video, VideoCreate)
    crud._reference(Match, metadata["match_id"])
    root = settings.video_storage_path.resolve()
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DomainError("Video storage is unavailable; check VIDEO_STORAGE_PATH permissions", 503) from exc
    key = uuid4().hex + suffix
    path = root / key
    try:
        size = 0
        with path.open("xb") as target:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.video_max_upload_bytes:
                    raise DomainError("Video exceeds the configured upload size limit", 413)
                target.write(chunk)
        try:
            result = subprocess.run(
                [settings.ffprobe_path, "-v", "error", "-protocol_whitelist", "file,pipe",
                 "-show_entries", "format=duration,format_name:stream=codec_type",
                 "-of", "json", str(path)], capture_output=True, text=True, timeout=30)
        except FileNotFoundError as exc:
            raise DomainError("Video validation requires FFmpeg/ffprobe. Install it or configure FFPROBE_PATH", 503) from exc
        except subprocess.TimeoutExpired as exc:
            raise DomainError("Video validation timed out; try another file", 422) from exc
        try:
            info = json.loads(result.stdout)
            duration = float(info["format"]["duration"])
            valid = (result.returncode == 0 and math.isfinite(duration) and duration > 0
                     and FORMATS[suffix][1] in info["format"]["format_name"]
                     and any(s["codec_type"] == "video" for s in info["streams"]))
        except (ValueError, KeyError, TypeError):
            valid = False
        if not valid:
            raise DomainError("File is not a valid supported video with a readable duration", 422)
        return crud.create(VideoCreate(**metadata, original_filename=original, storage_key=key,
            mime_type=FORMATS[suffix][0], file_size=size, duration_seconds=duration,
            upload_status="UPLOADED", processing_status="READY", uploaded_at=datetime.now(timezone.utc)))
    except OSError as exc:
        path.unlink(missing_ok=True)
        raise DomainError("Video storage or ffprobe is unavailable; check server configuration", 503) from exc
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        file.file.close()


def start_session(db, video_id):
    crud = CrudService(db, AnnotationSession, SessionCreate)
    video = crud._reference(Video, video_id)  # Parent lock serializes concurrent starts.
    media_path(video)
    session = db.scalar(select(AnnotationSession).where(
        AnnotationSession.video_id == video.id, AnnotationSession.annotator_id.is_(None)))
    if session is None:
        return crud.create(SessionCreate(video_id=video.id, match_id=video.match_id, status="IN_PROGRESS"))
    if session.status == "NOT_STARTED":
        session.status = "IN_PROGRESS"
    return crud._commit(session)


def workflow(db, completed, offset, limit):
    home, away = aliased(Team), aliased(Team)
    query = (select(Video, AnnotationSession, home.name, away.name, Match.match_date)
        .join(Match, Video.match_id == Match.id)
        .join(home, Match.home_team_id == home.id).join(away, Match.away_team_id == away.id)
        .outerjoin(AnnotationSession, (AnnotationSession.video_id == Video.id)
                   & AnnotationSession.annotator_id.is_(None))
        .where(Video.upload_status == "UPLOADED", Video.processing_status == "READY"))
    query = query.where(AnnotationSession.status == "REVIEWED") if completed else query.where(
        (AnnotationSession.id.is_(None)) | (AnnotationSession.status != "REVIEWED"))
    rows = db.execute(query.order_by(Video.created_at.desc(), Video.id).offset(offset).limit(limit))
    return [dict(video=VideoRead.model_validate(v), session=SessionRead.model_validate(s) if s else None,
                 match_name=f"{h} vs {a}", match_date=str(d)) for v, s, h, a, d in rows]
