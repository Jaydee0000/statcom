# Video system — Milestone 2

## Setup and storage

Install FFmpeg with `ffprobe` available on PATH (for example, `sudo apt install ffmpeg` on Ubuntu). The server requires ffprobe to validate containers and extract duration. Missing ffprobe returns a useful HTTP 503; unreadable media returns 422. Integration tests also require the ffmpeg executable to generate real video fixtures.

| Variable | Default / meaning |
|---|---|
| `DATABASE_URL` | Required PostgreSQL URL; see README |
| `TEST_DATABASE_URL` | Explicit, separate database ending in `_test` |
| `VIDEO_STORAGE_PATH` | Backend `storage/videos` by default; `.env.example` uses `./storage/videos` |
| `VIDEO_MAX_UPLOAD_BYTES` | 5368709120 (5 GiB) |
| `FFPROBE_PATH` | `ffprobe` |
| `CORS_ORIGINS` | JSON array allowing localhost/127.0.0.1 port 5173 |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000/api/v1` |

Relative media paths resolve from the backend process working directory. Use an absolute path if starting the API from different directories. Ensure that directory is writable and persistent; back up it and PostgreSQL together. Storage is excluded from Git.

Uploads use generated UUID filenames and retain the original filename only as metadata. The service rejects path separators, control characters, unsupported extensions, invalid media, missing matches, and oversized files. It copies the spooled upload in 1 MiB chunks, probes the stored file, and commits metadata only after successful validation. Failed validation/database writes remove the new file. A process crash between disk and database writes can leave an orphan; automatic orphan cleanup is not implemented.

MP4, MOV, and WebM are accepted. Use H.264 MP4 for broad browser compatibility. Container validation does not guarantee browser codec support, and no transcoding is performed. AVI is deliberately unsupported because this workflow cannot reliably play it in browsers.

## API and upload flow

All paths below are relative to `/api/v1`.

| Method / endpoint | Purpose |
|---|---|
| Existing `POST/GET /teams`, `POST/GET /matches` | Create/select match context |
| `POST /videos/upload` | Multipart file, required match_id, optional period/offsets/uploaded_by |
| `GET /videos/workflow?completed=false` | Uploaded/ready videos with null, Not Started, In Progress, or Ready for Review session |
| `GET /videos/workflow?completed=true` | Reviewed sessions/videos only |
| Existing `GET /videos/{id}` | Persisted video metadata |
| `GET/HEAD /videos/{id}/media` | Range-aware local media |
| `POST /videos/{id}/start` | Idempotently create/start or return existing anonymous session |
| Existing `GET/PATCH /annotation-sessions/{id}` | Read position/status; update position or transition status |

Workflow lists support offset/limit pagination; frontend services retrieve all pages. The UI creates/selects a match, picks/drops a file, displays transfer progress and processing feedback, and refreshes awaiting rows after success. One match can contain multiple files. Advanced upload metadata is exposed by the API; the simple intake UI uses default offsets and period.

## Serving and playback

The media route resolves only generated storage keys beneath the configured root. It returns Starlette/FastAPI `FileResponse`, which handles HTTP byte ranges, partial 206 responses, HEAD, and invalid-range 416 responses without loading the whole file into memory. CORS allows Range and exposes relevant response headers. Paths outside the media root and missing files are rejected.

The existing workspace uses an HTML5 video element and styled play/pause, seek, time, volume, mute, and speed controls. Speeds are 0.25, 0.5, 0.75, 1, 1.25, 1.5, and 2. Media errors identify unavailable files or unsupported browser codecs.

## Resume and review

Start creates/reuses the null-annotator session and changes Not Started to In Progress. Repeated starts reuse its UUID. Resume fetches its latest persisted position and restores it after loadedmetadata, clamped to valid duration, without autoplay.

Position is saved every five seconds during playback, on pause, 350 ms after seeking settles, on status changes, and on exit. Per-session queues preserve ordering; identical successful positions are skipped. Switching waits for the outgoing save. Failed saves show retry feedback; page-hide/unmount failures are retained for the next workspace opening. Hard refresh may close the UI; Resume recovers backend state. Abrupt termination or network loss can prevent the final best-effort save.

Ready for Review and Mark Reviewed are explicit actions. Reviewed rows move exclusively to Completed Videos. Review/Open preserves status; Reopen for correction returns to In Progress and preserves the last completed_at timestamp. There is no full status-history table in this milestone.

Video time and match time remain separate:

```text
match_time = video_time - video_time_offset + match_time_offset
```

For second-half offsets 0 and 2700 seconds, video 12:30 is match 57:30. This mapping describes continuous footage, not gaps or multiple timeline segments.

## Development boundaries

This is local development storage with no authentication, transcoding, resumable uploads, or object storage. The workflow uses anonymous sessions; uploaded_by is optional attribution, not authentication. Generic metadata CRUD does not manage physical file deletion. Large multipart bodies may spool to temporary disk before the service's size check; a production deployment needs request limits and authenticated media access. No annotation event/tag/skill UI or analytics work is included.
