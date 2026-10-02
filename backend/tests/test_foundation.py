from uuid import UUID, uuid4

import pytest
from argon2 import PasswordHasher
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models import Annotation, AnnotationSession, Tag, Team, User


def test_database_connectivity(client, db):
    assert db.scalar(text("SELECT version()" )).startswith("PostgreSQL")
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}
    assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0002"
    assert len(inspect(db.bind).get_table_names()) == 18  # 17 domain tables + Alembic


@pytest.mark.parametrize("resource,payload,patch", [
    ("teams", {"name": "Riverside"}, {"city": "Austin"}),
    ("players", {"first_name": "Alex", "last_name": "Rivera"}, {"primary_position": "CM"}),
    ("seasons", {"name": "Fall", "start_date": "2026-08-01", "end_date": "2026-12-01"}, {"name": "Autumn"}),
    ("competitions", {"name": "League"}, {"name": "Cup"}),
])
def test_create_read_update_and_delete(client, create, resource, payload, patch):
    record = create(resource, **payload)
    path = f"/api/v1/{resource}/{record['id']}"
    assert client.get(path).json()["id"] == record["id"]
    response = client.patch(path, json=patch)
    assert response.status_code == 200, response.text
    assert all(response.json()[key] == value for key, value in patch.items())
    assert len(client.get(f"/api/v1/{resource}").json()) == 1
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404


def test_create_match_and_lineup(client, create, graph):
    record = create("match-participants", match_id=graph["match"]["id"],
                    player_id=graph["player"]["id"], team_id=graph["home"]["id"],
                    starter=True, start_minute=0, end_minute=90)
    assert record["end_minute"] == 90
    assert client.get("/api/v1/match-participants", params={"match_id": graph["match"]["id"]}).json()[0]["id"] == record["id"]
    response = client.patch(f"/api/v1/matches/{graph['match']['id']}", json={"home_score": 2, "away_score": 1})
    assert response.status_code == 200
    assert response.json()["home_score"] == 2


def test_historical_memberships(client, create, graph):
    old = create("memberships", player_id=graph["player"]["id"], team_id=graph["home"]["id"],
                 start_date="2025-01-01", end_date="2025-12-31", jersey_number=7)
    create("memberships", player_id=graph["player"]["id"], team_id=graph["away"]["id"],
           start_date="2026-01-01", jersey_number=10)
    assert client.get(f"/api/v1/memberships/{old['id']}").json()["jersey_number"] == 7
    assert len(client.get("/api/v1/memberships", params={"player_id": graph["player"]["id"]}).json()) == 2


def test_video_metadata_multiple_files_and_session(client, create, graph):
    second = create("videos", match_id=graph["match"]["id"], original_filename="second.mov",
                    storage_key="matches/second.mov", mime_type="video/quicktime", file_size=9000,
                    duration_seconds=2700, period="second_half", video_time_offset=0, match_time_offset=2700)
    assert second["match_time_offset"] != second["video_time_offset"]
    assert len(client.get("/api/v1/videos", params={"match_id": graph["match"]["id"]}).json()) == 2
    response = client.patch(f"/api/v1/annotation-sessions/{graph['session']['id']}",
                            json={"last_playback_position": 125, "status": "IN_PROGRESS"})
    assert response.status_code == 200, response.text
    assert client.get(f"/api/v1/annotation-sessions/{graph['session']['id']}").json()["last_playback_position"] == 125
    duplicate = client.post("/api/v1/annotation-sessions", json={"video_id": graph["video"]["id"], "match_id": graph["match"]["id"]})
    assert duplicate.status_code == 409


def test_tags_normalize_and_archive(client, create, db):
    tag = create("tags", name="  Progressive   PASS  ")
    assert tag["normalized_name"] == "progressive pass"
    duplicate = client.post("/api/v1/tags", json={"name": "progressive pass"})
    assert duplicate.status_code == 409
    assert client.delete(f"/api/v1/tags/{tag['id']}").status_code == 204
    stored = db.get(Tag, UUID(tag["id"]))
    assert not stored.is_active and stored.archived_at
    assert client.get("/api/v1/tags", params={"is_active": True}).json() == []
    assert client.post("/api/v1/tags", json={"name": "progressive pass"}).status_code == 409
    create("tags", name="progressive pass", scope="another-library")


def test_annotation_multiple_tags_players_and_soft_delete(client, create, graph, annotation_data, db):
    annotation = create("annotations", **annotation_data)
    second_player = create("players", first_name="Sam", last_name="Lee")
    for player, role in [(graph["player"], "passer"), (second_player, "receiver")]:
        create("annotation-participants", annotation_id=annotation["id"], player_id=player["id"], role=role)
    tags = [create("tags", name=name) for name in ("Pass", "Build Up")]
    for tag in tags:
        create("annotation-tags", annotation_id=annotation["id"], tag_id=tag["id"])
    record = db.get(Annotation, UUID(annotation["id"]))
    assert len(record.tags) == len(record.participants) == 2
    assert client.patch(f"/api/v1/tags/{tags[0]['id']}", json={"name": "Passing"}).status_code == 200
    assert client.delete(f"/api/v1/tags/{tags[0]['id']}").status_code == 204
    assert len(client.get("/api/v1/annotation-tags", params={"annotation_id": annotation["id"]}).json()) == 2
    assert client.delete(f"/api/v1/annotations/{annotation['id']}").status_code == 204
    assert client.get(f"/api/v1/annotations/{annotation['id']}").status_code == 404
    assert client.get("/api/v1/annotations").json() == []
    db.refresh(record)
    assert record.deleted_at is not None
    assert len(record.tags) == 2


def test_point_annotation_without_players(create, annotation_data):
    annotation_data.pop("video_end_time")
    annotation_data.pop("skill_definition_id")
    assert create("annotations", **annotation_data)["video_end_time"] is None


@pytest.mark.parametrize("data_type,value,bad,options", [
    ("boolean", True, "true", None),
    ("number", 12.5, True, None),
    ("rating", 4, "four", None),
    ("text", "Observed", 1, None),
    ("single_select", "complete", "unknown", ["complete", "incomplete"]),
    ("multi_select", ["left", "forward"], ["left", "left"], ["left", "forward"]),
])
def test_custom_field_types(client, create, graph, annotation_data, data_type, value, bad, options):
    field = create("skill-fields", skill_definition_id=graph["skill"]["id"], key="outcome", label="Outcome",
                   data_type=data_type, options=options)
    annotation = create("annotations", **annotation_data)
    recorded = create("annotation-field-values", annotation_id=annotation["id"], field_definition_id=field["id"], value=value)
    assert recorded["value"] == value
    response = client.patch(f"/api/v1/annotation-field-values/{recorded['id']}", json={"value": bad})
    assert response.status_code == 422
    assert client.get(f"/api/v1/annotation-field-values/{recorded['id']}").json()["value"] == value


@pytest.mark.parametrize("kind,entity", [("player_reference", "player"), ("team_reference", "home")])
def test_reference_values(client, create, graph, annotation_data, kind, entity):
    field = create("skill-fields", skill_definition_id=graph["skill"]["id"], key="target", label="Target", data_type=kind)
    annotation = create("annotations", **annotation_data)
    record = create("annotation-field-values", annotation_id=annotation["id"], field_definition_id=field["id"], value=graph[entity]["id"])
    assert client.patch(f"/api/v1/annotation-field-values/{record['id']}", json={"value": str(uuid4())}).status_code == 422
    resource = "players" if entity == "player" else "teams"
    assert client.delete(f"/api/v1/{resource}/{graph[entity]['id']}").status_code == 409


def test_required_values_and_version_protection(client, create, graph, annotation_data):
    field = create("skill-fields", skill_definition_id=graph["skill"]["id"], key="success", label="Success", data_type="boolean", required=True)
    annotation = create("annotations", **annotation_data)
    path = f"/api/v1/annotations/{annotation['id']}"
    assert client.patch(path, json={"review_status": "REVIEWED"}).status_code == 422
    value = create("annotation-field-values", annotation_id=annotation["id"], field_definition_id=field["id"], value=False)
    assert client.patch(path, json={"review_status": "REVIEWED"}).status_code == 200
    assert client.delete(f"/api/v1/annotation-field-values/{value['id']}").status_code == 409
    assert client.patch(f"/api/v1/skill-fields/{field['id']}", json={"data_type": "text"}).status_code == 409
    assert client.delete(f"/api/v1/skill-fields/{field['id']}").status_code == 409
    assert client.patch(f"/api/v1/skills/{graph['skill']['id']}", json={"version": 2}).status_code == 409
    create("skills", name="Passing", version=2)


def test_wrong_skill_value_rejected(client, create, graph, annotation_data):
    other = create("skills", name="Pressing")
    field = create("skill-fields", skill_definition_id=other["id"], key="rating", label="Rating", data_type="rating")
    annotation = create("annotations", **annotation_data)
    assert client.post("/api/v1/annotation-field-values", json={"annotation_id": annotation["id"], "field_definition_id": field["id"], "value": 3}).status_code == 422


def test_mismatched_context_rejected(client, create, graph, annotation_data):
    other = create("matches", home_team_id=graph["away"]["id"], away_team_id=graph["home"]["id"], match_date="2026-09-24")
    assert client.post("/api/v1/annotation-sessions", json={"video_id": graph["video"]["id"], "match_id": other["id"]}).status_code == 422
    annotation_data["match_id"] = other["id"]
    assert client.post("/api/v1/annotations", json=annotation_data).status_code == 422


def test_database_enforces_context_without_api(db, graph, create):
    other = create("matches", home_team_id=graph["away"]["id"], away_team_id=graph["home"]["id"], match_date="2026-09-24")
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(AnnotationSession(match_id=UUID(other["id"]), video_id=UUID(graph["video"]["id"])))
        db.flush()


def test_referenced_records_cannot_be_deleted(client, graph, create, annotation_data):
    create("annotations", **annotation_data)
    for resource, key in [("teams", "home"), ("matches", "match"), ("videos", "video"), ("annotation-sessions", "session")]:
        assert client.delete(f"/api/v1/{resource}/{graph[key]['id']}").status_code == 409


@pytest.mark.parametrize("payload", [{"name": " "}, {"name": None}, {"name": "Club", "unexpected": 1}])
def test_team_validation(client, payload):
    assert client.post("/api/v1/teams", json=payload).status_code == 422


def test_patch_revalidates_complete_record(client, graph):
    assert client.patch(f"/api/v1/teams/{graph['home']['id']}", json={"name": None}).status_code == 422
    assert client.patch(f"/api/v1/seasons/{graph['season']['id']}", json={"end_date": "2020-01-01"}).status_code == 422
    assert client.patch(f"/api/v1/annotation-sessions/{graph['session']['id']}", json={"last_playback_position": 5401}).status_code == 422
    assert client.patch(f"/api/v1/annotation-sessions/{graph['session']['id']}", json={"progress": 101}).status_code == 422


def test_duration_cannot_invalidate_existing_annotation(client, create, graph, annotation_data):
    create("annotations", **annotation_data)
    assert client.patch(f"/api/v1/videos/{graph['video']['id']}", json={"duration_seconds": 5}).status_code == 422


def test_lineup_wrong_team(client, create, graph):
    third = create("teams", name="Other")
    assert client.post("/api/v1/match-participants", json={"match_id": graph["match"]["id"], "player_id": graph["player"]["id"], "team_id": third["id"]}).status_code == 422


def test_missing_references_and_bad_identifiers(client):
    assert client.post("/api/v1/videos", json={"match_id": str(uuid4()), "original_filename": "match.mp4"}).status_code == 422
    assert client.get("/api/v1/teams/not-a-uuid").status_code == 422
    assert client.get(f"/api/v1/teams/{uuid4()}").status_code == 404
    assert client.get("/api/v1/teams?limit=101").status_code == 422


def test_unique_links(client, create, annotation_data):
    annotation = create("annotations", **annotation_data)
    tag = create("tags", name="Pass")
    payload = {"annotation_id": annotation["id"], "tag_id": tag["id"]}
    create("annotation-tags", **payload)
    assert client.post("/api/v1/annotation-tags", json=payload).status_code == 409


def test_users_hash_passwords_and_unique_email(db):
    password = "only-for-this-test"
    user = User(first_name="Test", last_name="Coach", email="coach@example.test", password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.password_hash != password
    assert PasswordHasher().verify(user.password_hash, password)
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(User(first_name="Other", last_name="Coach", email="COACH@example.test", password_hash=hash_password(password)))
        db.flush()


def test_openapi_exposes_typed_crud_without_user_secrets(client):
    schema = client.get("/openapi.json").json()
    assert "/api/v1/teams" in schema["paths"]
    assert "password_hash" not in str(schema)
    assert "multipart/form-data" in schema["paths"]["/api/v1/videos/upload"]["post"]["requestBody"]["content"]
