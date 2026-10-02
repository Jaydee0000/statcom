"""Milestone 3 aggregate annotation workflow integration tests."""
from uuid import UUID, uuid4

from sqlalchemy import select

from app.models import Annotation, AnnotationFieldValue, AnnotationParticipant, AnnotationTag


def setup_library(create, graph):
    create("match-participants", match_id=graph["match"]["id"], player_id=graph["player"]["id"],
           team_id=graph["home"]["id"], starter=True)
    recipient = create("players", first_name="Sam", last_name="Lee")
    create("match-participants", match_id=graph["match"]["id"], player_id=recipient["id"],
           team_id=graph["home"]["id"], starter=False)
    outcome = create("skill-fields", skill_definition_id=graph["skill"]["id"], key="outcome",
                     label="Outcome", data_type="single_select", options=["Completed", "Incomplete"], required=True)
    distance = create("skill-fields", skill_definition_id=graph["skill"]["id"], key="distance",
                      label="Distance", data_type="number")
    tags = [create("tags", name="Progressive Pass", category="Passing", color="#20b876"),
            create("tags", name="Build Up", category="Phase")]
    return recipient, outcome, distance, tags


def aggregate_payload(graph, outcome, **changes):
    payload = {
        "match_id": graph["match"]["id"], "video_id": graph["video"]["id"],
        "skill_definition_id": graph["skill"]["id"], "video_start_time": 724.3,
        "video_end_time": None, "match_period": "first_half", "match_time": 724.3,
        "notes": "Good decision", "review_status": "DRAFT", "created_by": None,
        "tag_ids": [], "participants": [],
        "field_values": [{"field_definition_id": outcome["id"], "value": "Completed"}],
    }
    payload.update(changes)
    return payload


def post_annotation(client, graph, payload):
    return client.post(f"/api/v1/annotation-sessions/{graph['session']['id']}/annotations", json=payload)


def test_create_point_annotation_and_list_by_session(client, create, graph):
    _, outcome, _, _ = setup_library(create, graph)
    response = post_annotation(client, graph, aggregate_payload(graph, outcome))
    assert response.status_code == 201, response.text
    annotation = response.json()
    assert annotation["video_end_time"] is None and annotation["video_start_time"] == 724.3
    listed = client.get(f"/api/v1/annotation-sessions/{graph['session']['id']}/annotations").json()
    assert [item["id"] for item in listed] == [annotation["id"]]


def test_range_multitag_multiplayer_and_custom_values(client, create, graph, db):
    recipient, outcome, distance, tags = setup_library(create, graph)
    payload = aggregate_payload(graph, outcome, video_end_time=728.9,
        tag_ids=[tag["id"] for tag in tags],
        participants=[{"player_id": graph["player"]["id"], "role": "Passer"},
                      {"player_id": recipient["id"], "role": "Receiver"},
                      {"player_id": None, "role": "Unknown defender"}],
        field_values=[{"field_definition_id": outcome["id"], "value": "Completed"},
                      {"field_definition_id": distance["id"], "value": 22.5}])
    response = post_annotation(client, graph, payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["video_end_time"] == 728.9
    assert len(body["tags"]) == 2 and len(body["participants"]) == 3 and len(body["field_values"]) == 2
    annotation_id = UUID(body["id"])
    assert len(db.scalars(select(AnnotationTag).where(AnnotationTag.annotation_id == annotation_id)).all()) == 2
    assert len(db.scalars(select(AnnotationParticipant).where(AnnotationParticipant.annotation_id == annotation_id)).all()) == 3


def test_invalid_timestamps_and_missing_required_field_are_atomic(client, create, graph, db):
    _, outcome, _, tags = setup_library(create, graph)
    missing = aggregate_payload(graph, outcome, tag_ids=[tags[0]["id"]], field_values=[])
    assert post_annotation(client, graph, missing).status_code == 422
    backwards = aggregate_payload(graph, outcome, video_start_time=20, video_end_time=10)
    assert post_annotation(client, graph, backwards).status_code == 422
    past_duration = aggregate_payload(graph, outcome, video_start_time=5401)
    assert post_annotation(client, graph, past_duration).status_code == 422
    assert db.scalars(select(Annotation)).all() == []
    assert db.scalars(select(AnnotationTag)).all() == []


def test_dynamic_field_validation_and_match_participant_context(client, create, graph):
    _, outcome, distance, _ = setup_library(create, graph)
    bad_option = aggregate_payload(graph, outcome,
        field_values=[{"field_definition_id": outcome["id"], "value": "Maybe"}])
    assert post_annotation(client, graph, bad_option).status_code == 422
    bad_number = aggregate_payload(graph, outcome,
        field_values=[{"field_definition_id": outcome["id"], "value": "Completed"},
                      {"field_definition_id": distance["id"], "value": "far"}])
    assert post_annotation(client, graph, bad_number).status_code == 422
    outsider = create("players", first_name="Not", last_name="Selected")
    invalid_player = aggregate_payload(graph, outcome,
        participants=[{"player_id": outsider["id"], "role": "Passer"}])
    assert post_annotation(client, graph, invalid_player).status_code == 422


def test_required_text_and_multiselect_fields_reject_empty_values(client, create, graph):
    create("match-participants", match_id=graph["match"]["id"], player_id=graph["player"]["id"],
           team_id=graph["home"]["id"])
    skill = client.post("/api/v1/annotation-library/skills", json={
        "name": "Decision Detail",
        "fields": [
            {"key": "detail", "label": "Detail", "data_type": "text", "required": True,
             "options": None, "display_order": 0},
            {"key": "qualities", "label": "Qualities", "data_type": "multi_select", "required": True,
             "options": ["Fast", "Accurate"], "display_order": 1},
        ],
    }).json()
    payload = aggregate_payload(
        graph, skill["fields"][0], skill_definition_id=skill["id"],
        field_values=[
            {"field_definition_id": skill["fields"][0]["id"], "value": ""},
            {"field_definition_id": skill["fields"][1]["id"], "value": []},
        ],
    )
    response = post_annotation(client, graph, payload)
    assert response.status_code == 422
    assert "Detail" in response.json()["detail"] and "Qualities" in response.json()["detail"]

    payload["field_values"] = [
        {"field_definition_id": skill["fields"][0]["id"], "value": "   \t"},
        {"field_definition_id": skill["fields"][1]["id"], "value": ["Fast"]},
    ]
    response = post_annotation(client, graph, payload)
    assert response.status_code == 422
    assert "Detail" in response.json()["detail"]


def test_edit_replaces_children_without_creating_second_annotation(client, create, graph, db):
    recipient, outcome, distance, tags = setup_library(create, graph)
    created = post_annotation(client, graph, aggregate_payload(graph, outcome,
        tag_ids=[tags[0]["id"]], participants=[{"player_id": graph["player"]["id"], "role": "Passer"}])).json()
    update = aggregate_payload(graph, outcome, video_start_time=800, video_end_time=802,
        notes="Edited", tag_ids=[tags[1]["id"]],
        participants=[{"player_id": recipient["id"], "role": "Receiver"}],
        field_values=[{"field_definition_id": outcome["id"], "value": "Incomplete"},
                      {"field_definition_id": distance["id"], "value": 10}])
    response = client.patch(f"/api/v1/annotations/{created['id']}/aggregate", json=update)
    assert response.status_code == 200, response.text
    edited = response.json()
    assert edited["id"] == created["id"] and edited["notes"] == "Edited"
    assert [tag["id"] for tag in edited["tags"]] == [tags[1]["id"]]
    assert db.scalar(select(Annotation).where(Annotation.id == UUID(created["id"]))).video_start_time == 800
    assert len(db.scalars(select(Annotation)).all()) == 1
    assert len(db.scalars(select(AnnotationFieldValue)).all()) == 2


def test_archive_removes_from_active_listing_and_can_restore(client, create, graph):
    _, outcome, _, _ = setup_library(create, graph)
    annotation = post_annotation(client, graph, aggregate_payload(graph, outcome)).json()
    assert client.delete(f"/api/v1/annotations/{annotation['id']}/archive").status_code == 204
    assert client.get(f"/api/v1/annotation-sessions/{graph['session']['id']}/annotations").json() == []
    assert client.get(f"/api/v1/annotations/{annotation['id']}/aggregate").status_code == 404
    restored = client.post(f"/api/v1/annotations/{annotation['id']}/restore")
    assert restored.status_code == 200 and restored.json()["id"] == annotation["id"]


def test_duplicate_copies_content_but_uses_requested_time(client, create, graph):
    recipient, outcome, _, tags = setup_library(create, graph)
    original = post_annotation(client, graph, aggregate_payload(graph, outcome,
        tag_ids=[tags[0]["id"]], participants=[{"player_id": recipient["id"], "role": "Receiver"}])).json()
    response = client.post(f"/api/v1/annotations/{original['id']}/duplicate",
        json={"video_start_time": 900, "video_end_time": 905, "match_time": 900, "match_period": "first_half"})
    assert response.status_code == 201, response.text
    copy = response.json()
    assert copy["id"] != original["id"] and copy["video_start_time"] == 900 and copy["video_end_time"] == 905
    assert [tag["id"] for tag in copy["tags"]] == [tag["id"] for tag in original["tags"]]
    assert [(item["player_id"], item["role"]) for item in copy["participants"]] == [(item["player_id"], item["role"]) for item in original["participants"]]
    assert copy["review_status"] == "DRAFT"


def test_create_tag_and_normalized_duplicate_rejection(client):
    first = client.post("/api/v1/tags", json={"name": "  Scanning   Before Receiving ", "category": "Awareness"})
    assert first.status_code == 201
    duplicate = client.post("/api/v1/tags", json={"name": "SCANNING BEFORE RECEIVING", "category": "Other"})
    assert duplicate.status_code == 409


def test_create_skill_with_fields_and_use_immediately(client, create, graph):
    payload = {"name": "Scanning Before Receiving", "category": "Awareness", "fields": [
        {"key": "observed", "label": "Observed", "data_type": "single_select", "required": True,
         "options": ["Yes", "No", "Unclear"], "display_order": 0},
        {"key": "rating", "label": "Rating", "data_type": "rating", "required": False,
         "options": None, "display_order": 1}]}
    response = client.post("/api/v1/annotation-library/skills", json=payload)
    assert response.status_code == 201, response.text
    skill = response.json()
    assert [field["key"] for field in skill["fields"]] == ["observed", "rating"]
    assert any(item["id"] == skill["id"] for item in client.get("/api/v1/annotation-library/skills").json())
    create("match-participants", match_id=graph["match"]["id"], player_id=graph["player"]["id"], team_id=graph["home"]["id"])
    annotation = aggregate_payload(graph, skill["fields"][0], skill_definition_id=skill["id"],
        field_values=[{"field_definition_id": skill["fields"][0]["id"], "value": "Yes"},
                      {"field_definition_id": skill["fields"][1]["id"], "value": 4}])
    assert post_annotation(client, graph, annotation).status_code == 201


def test_skill_definition_rejects_invalid_dynamic_options(client):
    response = client.post("/api/v1/annotation-library/skills", json={"name": "Bad Skill", "fields": [
        {"key": "outcome", "label": "Outcome", "data_type": "single_select", "required": True,
         "options": [], "display_order": 0}]})
    assert response.status_code == 422


def test_annotation_context_contains_only_match_players(client, create, graph):
    setup_library(create, graph)
    outsider = create("players", first_name="Outside", last_name="Roster")
    context = client.get(f"/api/v1/matches/{graph['match']['id']}/annotation-context").json()
    ids = {player["player_id"] for player in context["players"]}
    assert graph["player"]["id"] in ids and outsider["id"] not in ids
    assert {team["id"] for team in context["teams"]} == {graph["home"]["id"], graph["away"]["id"]}


def test_duplicate_rejects_invalid_requested_range(client, create, graph):
    _, outcome, _, _ = setup_library(create, graph)
    original = post_annotation(client, graph, aggregate_payload(graph, outcome)).json()
    response = client.post(f"/api/v1/annotations/{original['id']}/duplicate",
                           json={"video_start_time": 20, "video_end_time": 10})
    assert response.status_code == 422


def test_wrong_session_and_unknown_ids_are_rejected(client, create, graph):
    _, outcome, _, _ = setup_library(create, graph)
    payload = aggregate_payload(graph, outcome)
    assert client.post(f"/api/v1/annotation-sessions/{uuid4()}/annotations", json=payload).status_code == 404
    payload["tag_ids"] = [str(uuid4())]
    assert post_annotation(client, graph, payload).status_code == 422
