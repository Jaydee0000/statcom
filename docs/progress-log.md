# Progress log

## 2026-10-01 — Milestone 5: real-data frontend reporting

### Delivered

- Replaced core Players and Player Profile mock records, fake ratings/form, fake match history, and fake clips with PostgreSQL-backed player identity, memberships, participation, match results, coverage, and annotation-derived metrics.
- Added batched player summary/history/result comparison, match overview/detail statistics, team stat-sheet, metric catalog, and metric-source endpoints on top of the Milestone 4 event classifier.
- Preserved wins, draws, and losses; reports count metrics as observed per-match values while percentage metrics are recalculated from summed numerators and denominators.
- Added dynamic standard/skill/tag metric definitions with backend labels and a Select Metrics control. Coach-created skills/tags can become columns without editing React.
- Added real Matches and Match Detail pages with lineup role, position, recorded minutes, videos, session coverage, and per-player match metrics.
- Added incomplete-data states throughout. Unknown minutes remain blank, no-session data is Not Started, and partial session work is never presented as reviewed.
- Added traceable player metric sources and real Video Clips links. Video Analysis accepts match/video/annotation query parameters, resumes the existing session, selects the annotation, and seeks the original media timestamp.
- Removed the unused `mockPlayers` dataset and its mock-only player types. No rating is shown because no legitimate rating definition exists.
- Added Milestone 5 metric, player analytics, and team stat-sheet documentation. No database migration or persisted summary table was added.

### Verification

- 74 backend PostgreSQL integration tests passed (68 existing plus 6 reporting tests).
- Alembic current is `0002 (head)` and `alembic check` reports no drift.
- Frontend TypeScript/Vite production build passed; no frontend test runner is configured.
- Backend and frontend startup passed against an isolated PostgreSQL 16 application database.
- Live browser workflow passed with real team/player/matches/uploaded videos/annotations: roster → profile totals/history/result groups → recent match detail/lineup → dynamic Team Stat Sheet/custom metric → source list → existing video/session at the exact annotation timestamp.

### Scope boundary

Milestone 5 does not add predictive models, generated ratings, chatbot/natural-language analytics, computer vision, automatic annotations, scouting marketplace, public player database, report/PDF generation, or the final advanced Analytics dashboard.

## 2026-09-29 — Milestone 4: match analytics and metrics

### Delivered

- Added a centralized, deterministic metrics service deriving player, team, and overall match statistics from active persisted annotations.
- Added exact skill/tag/structured-outcome classification for passes and completion, progressive passes, shots/on-target/goals, assists, tackles, interceptions, and turnovers.
- Added role-aware player attribution, unambiguous team attribution, explicit unknown/no-player/team-unassigned counts, and immediate archive exclusion.
- Added player, skill, tag, outcome, match-time, session, and period filters; 1/5/10/15-minute buckets; skill/outcome/player/tag breakdowns; and event metadata.
- Added `GET /matches/{match_id}/metrics` and `GET /matches/{match_id}/players/{player_id}/metrics`.
- Replaced the Analytics placeholder with a backend-powered match overview, team comparison, compact player table, filters, timeline buckets, and breakdown cards without changing the annotation workspace.
- Added ten PostgreSQL integration tests covering all required metric, filtering, data-quality, empty-match, access, archive, and point/range cases.
- No migration or duplicate statistics table was added.

### Verification

- 67 backend integration tests passed against PostgreSQL 16.
- Frontend TypeScript/Vite production build passed.

### Scope boundary

Analytics is single-match only. Historical/season trends, win/loss correlation, longitudinal development, ratings, reports, recommendations, predictive ML, chatbot features, and authentication redesign remain outside Milestone 4.

## 2026-09-28 — Milestone 3: functional annotation system

### Delivered

- Preserved the Video Analysis page structure while making the workspace/editor functional for point and range annotations.
- Added transactional aggregate create/edit/duplicate APIs, active session listing, soft archive/restore, server-side duration/context/type/required validation, and rich aggregate responses.
- Added backend-driven dynamic fields for all eight supported types, inline atomic skill creation, reusable/searchable/category-filtered tags, normalized duplicate protection, and recent tag ordering.
- Added current-match-only participant selection, multiple roles/players, no-player state, and persistent explicit unknown participants through migration `0002`.
- Added point/range timeline markers, click-to-seek/edit behavior, a compact saved annotation list, duplicate-at-current-time, save/retry states, dirty-state warnings, and keyboard shortcuts.
- Remembered the active session across browser refreshes so its persisted timeline/list rebuild automatically, and guarded in-app navigation when the editor is dirty.
- Added PostgreSQL integration coverage for create/list/point/range/tags/players/custom values/timestamps/required fields/edit/archive/restore/duplicate/tag normalization/skill creation/dynamic validation/context.
- Updated README and annotation/database/tag-skill documentation. No metric calculation or analytics-page integration was added.

### Verification

- 57 backend integration tests passed against disposable PostgreSQL 16.
- Alembic current is `0002 (head)` and `alembic check` reports no drift.
- Frontend TypeScript/Vite production build passed.
- Reverified on 2026-09-30 with the current full suite (68 passing tests), a clean Alembic drift check, and a live browser create/edit/tag/skill/refresh/archive workflow.

### Scope boundary

Metric calculation, `PlayerMatchStats`, profiles/team analytics, comparisons, reports, ML, chatbot, and computer vision remain for later milestones.

## 2026-09-27 — Milestone 1: backend/database foundation

Starting state: existing React prototype, empty backend directory, no database models or migrations. Implemented FastAPI, SQLAlchemy, PostgreSQL/psycopg, Alembic, Pydantic/settings, and an Argon2id hashing utility.

### Delivered

- Environment-based database and CORS configuration, engine/session dependency, startup/health connectivity checks.
- Seventeen domain tables covering users, teams, players, roster history, seasons, competitions, matches, lineup participants, video metadata, sessions, tags, skills/fields, annotations, participant/tag links, and custom field values.
- Initial explicit Alembic revision `0001`, using the same metadata as the application.
- Sixteen resources with typed create/list/read/patch/delete endpoints; reference validation, pagination, context checks, normalized tag uniqueness, soft deletion and archival.
- JSONB custom values with type/option validation and real foreign keys for player/team reference values. Historical used skills/structural fields are protected against incompatible edits.
- PostgreSQL integration tests and setup/architecture/database/annotation documentation.

### Verification

- Initial migration applied to an isolated PostgreSQL 16 database.
- Migration downgrade/upgrade exercised on disposable databases.
- `alembic check`: no schema differences between migrated PostgreSQL and SQLAlchemy metadata.
- 34 integration tests passed against actual PostgreSQL, not SQLite. One upstream Starlette warning concerns its current httpx TestClient adapter; tests pass.
- Live Uvicorn startup completed; `/health`, `/docs`, and OpenAPI responded successfully (81 API operations).
- HTTP create/read/update was checked against an independent PostgreSQL connection. The API process was stopped/restarted, and the same committed record was retrieved. HTTP delete/read-after-delete also passed; the temporary smoke record was removed.
- Verification used an isolated PostgreSQL 16 cluster and Python virtual environment under `/tmp`, with an application database and separate test database. These are development verification resources, not a production deployment; follow README setup for a durable installation.

### Scope boundary

Frontend code was unchanged. No media upload/playback, annotation UI/timeline, session workflow automation, metric summaries, analytics, reports, authentication UI, ML, chatbot, or computer vision was added. The API is local development CRUD without authentication/authorization. Milestone 2 has not started.
