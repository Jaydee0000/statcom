# Architecture — Milestone 5

## Components

The React/TypeScript frontend uses a centralized API layer for video, annotation, match analytics, player reporting, and team stat sheets. The backend is FastAPI with Pydantic request/response validation, SQLAlchemy 2 ORM, PostgreSQL 15+, psycopg 3, and Alembic migrations.

```text
HTTP request
  → api/router.py (typed routes, status codes, dependency injection)
  → schemas/entities.py (shape/type and within-record validation)
  → services/crud.py (references, custom values, history protection, transaction)
  → repositories/crud.py (SQLAlchemy queries and persistence)
  → PostgreSQL (foreign keys, uniqueness, check constraints, indexes)
```

The 16 CRUD resources share one route factory and repository, with explicit per-resource input schemas and service validation. This avoids duplicating five identical transport handlers per resource. Read/PATCH schemas are generated from explicit inputs; PATCH merges supplied fields into the stored record and validates the complete result. Omitted fields stay unchanged; explicit null is rejected for required fields. Unknown input fields are rejected.

- `app/core/config.py`: environment/.env configuration, PostgreSQL-only database URL validation.
- `app/db/base.py`: shared metadata, UUID and timestamp mixins, naming conventions.
- `app/db/session.py`: engine, session factory, per-request session dependency.
- `app/models/entities.py`: all 17 domain tables and ORM navigation relationships.
- `app/core/security.py`: Argon2id password hashing utility; no login flow.
- `app/main.py`: application, CORS, domain-error handling, startup connection check, health endpoint.
- `alembic/`: explicit versioned schema management using the application's metadata.

Startup performs `SELECT 1` and fails if PostgreSQL is unavailable. It never silently creates tables. `/health` checks connectivity and returns 503 when unavailable; migration state is checked separately with Alembic.

## Transactions and integrity

Each successful mutation commits atomically. Constraint conflicts roll back and return 409 without leaking SQL/credentials. Missing records return 404; invalid fields/references return 422. Lists are deterministic by UUID with `offset` and `limit` (default 50, maximum 100).

Parent/definition rows are locked while validating dependent records. References cannot be reassigned through PATCH: create a new record for a new parent/context. Foreign-key deletion is restrictive, not a cascade that erases annotations. Tag/skill deletion archives; annotation deletion sets `deleted_at`. Other records can be physically deleted only if no dependent rows prevent it.

PostgreSQL enforces video/session/annotation context with composite foreign keys. Cross-table semantic rules (lineup team belongs to the match, custom field belongs to the annotation's skill, value matches field type/options) are enforced by the service. All application writes must use this service. Direct SQL clients can bypass semantic validation, although foreign keys and database checks still apply.

## API resources

Each resource supports `POST /api/v1/{resource}`, `GET /api/v1/{resource}`, and `GET`, `PATCH`, `DELETE /api/v1/{resource}/{id}`:

| Resource | Purpose |
|---|---|
| `teams` | Team identity |
| `players` | Player identity independent of team |
| `memberships` | Dated team membership/jersey history |
| `seasons` | Dated seasons |
| `competitions` | Competition identity |
| `matches` | Teams, date, score, context |
| `match-participants` | Lineups and participation intervals |
| `videos` | Metadata, uploads, media delivery, and workflow listing |
| `annotation-sessions` | Persistent playback and review workflow |
| `tags` | Stable reusable tag definitions |
| `skills` | Versioned skill definitions |
| `skill-fields` | Typed field definitions |
| `annotations` | Point/range record foundations |
| `annotation-participants` | Multiple players and roles |
| `annotation-tags` | Many-to-many links |
| `annotation-field-values` | Typed custom values |

Available list filters: `match_id`, `video_id`, `player_id`, `team_id`, `annotation_id`, `annotation_session_id`, `skill_definition_id`, and `is_active`, only when the resource actually contains that field. A filter that does not apply returns 422. Deleted annotations are excluded from normal reads/lists. Archived tags/skills remain retrievable; use `is_active=true` for active lists.

User records exist for future attribution/authentication, but there is intentionally no public user/password API. Future user provisioning should use `hash_password()`; no plaintext password column exists. There are no authorization boundaries yet, and tag `scope` is a library namespace, not access control.

## Video and session integration

`api/video_workflow.py` provides thin multipart upload, media, workflow-list, and Start routes. `services/videos.py` validates and streams uploads to local disk, probes media, queries workflow rows, and creates/reuses the anonymous development session. Existing CRUD handles match creation, metadata reads, and session PATCH; there are no duplicate CRUD implementations.

The frontend service layer (`api`, `matchesApi`, `videosApi`, `annotationSessionsApi`) owns HTTP requests and errors. Upload progress uses XMLHttpRequest. `playbackPositions` serializes updates per session and survives route unmounts. The workspace uses native HTML5 video with the existing styled controls. Switching sessions waits for the outgoing save. Position restores after metadata loads without autoplay.

## Milestone 5 reporting path

`api/reporting.py` exposes frontend-shaped responses through `services/reporting.py`. A request selects matches once, then bulk-loads participants and the canonical Milestone 4 events for all selected matches. Child tags, annotation participants, custom field values, sessions, teams, and membership display data are loaded in bounded queries; the service never calls one endpoint or query per table row.

```text
Players / Profile / Match Detail / Team Stat Sheet
  → playersApi / matchesApi / analyticsApi
  → reporting endpoints
  → batched match context + metrics.load_events_for_matches
  → Milestone 4 classification and actor attribution
  → values + definitions + coverage + source annotation IDs
```

Percentage definitions include numerator and denominator semantics. Aggregations recompute the ratio from summed components. Dynamic `skill:<uuid>` and `tag:<uuid>` definitions make active coach-defined annotation categories selectable without adding React columns. There is no second frontend metric engine; React only formats returned values.

## Verification and remaining scope

PostgreSQL integration tests use real Alembic migrations and rollback-isolated transactions. Video tests create real H.264 MP4 fixtures with FFmpeg and check metadata, upload rejection, byte ranges, position persistence, and workflow transitions. The production frontend build checks TypeScript. Browser verification covers the complete upload/playback/resume/review path; see the progress log.

Authentication, a complete session transition audit log, predictive models, generated ratings, advanced reports, chatbot, and computer vision remain future work. See [video system](video-system.md) for configuration and deployment limitations.
