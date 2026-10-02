# StatCom

Soccer performance tracking, match annotation, and annotation-derived player, match, and team analytics. Milestone 5 connects the core frontend pages to PostgreSQL and the deterministic metric engine, including season history, result comparisons, dynamic stat sheets, coverage warnings, and annotation/video traceability.

## Backend setup

Requires Python 3.12+ and PostgreSQL 15+ (the migration uses `UNIQUE NULLS NOT DISTINCT`).

1. Provision a PostgreSQL role and two databases: an application database and a **separate** disposable test database whose name ends in `_test`. Grant that role ownership/migration privileges for these databases.
2. From the repository root:

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   cp .env.example .env
   ```

3. Edit `.env` with your database URLs. Use `postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE`; URL-encode special characters in credentials. Configuration reads `backend/.env` regardless of the working directory; exported environment variables take precedence. No database or credentials are created automatically.
4. Apply migrations, then start the API:

   ```bash
   alembic upgrade head
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

- Health/database check: <http://127.0.0.1:8000/health>
- Interactive API and complete request/response schemas: <http://127.0.0.1:8000/docs>
- OpenAPI: <http://127.0.0.1:8000/openapi.json>
- API prefix: `/api/v1`

Authentication/authorization is not implemented. Run this foundation locally; user IDs are optional attribution references, not authenticated identities. Password hashes are never exposed by these endpoints.

## Tests and migrations

From `backend/`, with the virtual environment active:

```bash
# Set this to your separate test database, not the application database.
export TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:PORT/statcom_test'
pytest -q
alembic current
alembic check
```

Tests explicitly require `TEST_DATABASE_URL` in the process environment, apply the real migration, and roll back each test's changes. They do not use SQLite or `create_all()`. Do not run tests against valuable data. `.env` is used for application/Alembic configuration; the test URL must be exported explicitly.

For later model changes, generate and review a **new** revision with `alembic revision --autogenerate -m "description"`, then run `alembic upgrade head`. `alembic downgrade base` removes all domain tables and their data; use only in a disposable database.

## Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1` in `frontend/.env`. Run the frontend on port 5173, or add its actual origin to backend `CORS_ORIGINS`. The allowlisted origins also support modern browser local/private-network preflights used by the separate frontend and API development ports. Install FFmpeg (including `ffprobe`) before uploading; configure `FFPROBE_PATH` if it is not on PATH. Configure `VIDEO_STORAGE_PATH` in `backend/.env`; relative paths resolve from the backend process working directory. Videos are stored on disk, never as database bytes. See [video setup and workflow](docs/video-system.md).

## Implemented scope

- Seventeen persistent domain tables, UUID identities, foreign keys, checks, indexes, and historical membership.
- Typed create/list/read/patch/delete API foundations, pagination, relationship filters, and clear validation/conflict responses.
- Validated MP4/MOV/WebM uploads, range-aware media delivery, and persistent start/resume/review workflows.
- Atomic annotation create/edit/duplicate operations with point/range timestamps, match time, multiple tags/players, typed custom values, and archive/restore behavior.
- Active tag search/filter/create, dynamic skill/field creation, match-only participant selection, timeline markers, compact session list, dirty-state warnings, and keyboard shortcuts.
- New clean drafts follow the current playhead, while an explicitly marked point/range remains fixed; recent-tag preferences recover safely if browser storage is malformed.
- Read-only match/player metrics derived from active annotations, with team attribution, exact structured classification, filters, breakdowns, timeline buckets, and a responsive Match Analytics page.
- Real Players, Player Profile, Matches, Match Detail, and Team Stat Sheet pages backed by batched reporting endpoints rather than mock statistics.
- Dynamic backend metric definitions, correct ratio aggregation, win/draw/loss comparison, annotation completeness, and source links that open the original video at the saved annotation timestamp.

Predictive modeling, generated player ratings, advanced reports/PDFs, authentication UI, recommendations, chatbot, scouting marketplace, and computer vision remain future work.

See [architecture](docs/architecture.md), [database design](docs/database-design.md), [annotation system](docs/annotation-system.md), [metric definitions](docs/metric-definitions.md), [player analytics](docs/player-analytics.md), [team stat sheet](docs/team-stat-sheet.md), [match analytics](docs/match-analytics.md), [tags and skills](docs/tag-and-skill-system.md), and [progress log](docs/progress-log.md).
