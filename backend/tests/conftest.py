import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

# Never silently fall back to the application's database or SQLite.
TEST_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_URL:
    raise RuntimeError("Set TEST_DATABASE_URL to a dedicated PostgreSQL database ending in _test")
url = make_url(TEST_URL)
if url.get_backend_name() != "postgresql" or not (url.database or "").endswith("_test"):
    raise RuntimeError("Tests require a dedicated PostgreSQL database ending in _test")
if os.environ.get("DATABASE_URL") and make_url(os.environ["DATABASE_URL"]) == url:
    raise RuntimeError("TEST_DATABASE_URL must differ from DATABASE_URL")
os.environ["DATABASE_URL"] = TEST_URL

from fastapi.testclient import TestClient
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="session")
def engine():
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    engine = create_engine(TEST_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as session:
            yield session
        transaction.rollback()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def create(client):
    def make(resource, **data):
        response = client.post(f"/api/v1/{resource}", json=data)
        assert response.status_code == 201, response.text
        return response.json()
    return make


@pytest.fixture
def graph(create):
    home = create("teams", name="Riverside")
    away = create("teams", name="Eastwood")
    player = create("players", first_name="Alex", last_name="Rivera")
    season = create("seasons", name="2026", start_date="2026-01-01", end_date="2026-12-31")
    competition = create("competitions", name="League")
    match = create("matches", home_team_id=home["id"], away_team_id=away["id"],
                   season_id=season["id"], competition_id=competition["id"], match_date="2026-09-23")
    video = create("videos", match_id=match["id"], original_filename="match.mp4", duration_seconds=5400)
    session = create("annotation-sessions", video_id=video["id"], match_id=match["id"])
    skill = create("skills", name="Passing")
    return dict(home=home, away=away, player=player, season=season, competition=competition,
                match=match, video=video, session=session, skill=skill)


@pytest.fixture
def annotation_data(graph):
    return dict(annotation_session_id=graph["session"]["id"], match_id=graph["match"]["id"],
                video_id=graph["video"]["id"], skill_definition_id=graph["skill"]["id"],
                video_start_time=10, video_end_time=15, match_period="first_half", match_time=10)
