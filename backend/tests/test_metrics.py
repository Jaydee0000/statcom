"""Milestone 4 annotation-derived match analytics integration tests."""
from uuid import uuid4

import pytest


@pytest.fixture
def analytics_data(client, create, graph):
    alex = graph["player"]
    sam = create("players", first_name="Sam", last_name="Lee")
    opponent = create("players", first_name="Jordan", last_name="West")
    for player, team, role in ((alex, graph["home"], True), (sam, graph["home"], True),
                               (opponent, graph["away"], True)):
        create("match-participants", match_id=graph["match"]["id"], player_id=player["id"],
               team_id=team["id"], starter=role)
    outcome = create("skill-fields", skill_definition_id=graph["skill"]["id"], key="outcome",
                     label="Outcome", data_type="single_select", required=True,
                     options=["Completed", "Incomplete"])
    skills = {"pass": graph["skill"]}
    for name in ("Shot", "Tackle", "Interception", "Turnover", "Assist"):
        skills[name.casefold()] = create("skills", name=name)
    shot_outcome = create("skill-fields", skill_definition_id=skills["shot"]["id"], key="outcome",
                          label="Outcome", data_type="single_select", required=True,
                          options=["Off Target", "On Target", "Goal"])
    progressive = create("tags", name="Progressive Pass", category="Passing")

    def annotation(skill, timestamp, *, player=None, role="Player", result=None, tag_ids=None,
                   end=None, period="first_half", unknown=False):
        definition = outcome if skill == "pass" else shot_outcome if skill == "shot" else None
        participants = ([{"player_id": None, "role": role}] if unknown else
                        ([{"player_id": player["id"], "role": role}] if player else []))
        payload = {"match_id": graph["match"]["id"], "video_id": graph["video"]["id"],
                   "skill_definition_id": skills[skill]["id"], "video_start_time": timestamp,
                   "video_end_time": end, "match_period": period, "match_time": timestamp,
                   "notes": None, "review_status": "DRAFT", "created_by": None,
                   "tag_ids": tag_ids or [], "participants": participants,
                   "field_values": ([{"field_definition_id": definition["id"], "value": result}]
                                    if definition else [])}
        response = client.post(f"/api/v1/annotation-sessions/{graph['session']['id']}/annotations", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    annotations = [
        annotation("pass", 100, player=alex, role="Passer", result="Completed", tag_ids=[progressive["id"]]),
        annotation("pass", 200, player=alex, role="Passer", result="Incomplete", end=205),
        annotation("pass", 250, player=sam, role="Passer", result="Completed"),
        annotation("shot", 300, player=alex, role="Shooter", result="On Target"),
        annotation("shot", 350, player=alex, role="Scorer", result="Goal"),
        annotation("turnover", 400, player=alex, role="Player"),
        annotation("tackle", 450, player=alex, role="Tackler"),
        annotation("interception", 500, player=sam, role="Interceptor"),
        annotation("assist", 350, player=sam, role="Assister"),
        annotation("turnover", 600),
        annotation("tackle", 650, role="Unknown defender", unknown=True),
        annotation("pass", 700, player=opponent, role="Passer", result="Completed", period="second_half"),
    ]
    archived = annotation("shot", 800, player=alex, role="Scorer", result="Goal")
    assert client.delete(f"/api/v1/annotations/{archived['id']}/archive").status_code == 204
    return {"graph": graph, "alex": alex, "sam": sam, "opponent": opponent, "skills": skills,
            "outcome": outcome, "progressive": progressive, "annotations": annotations}


def metrics(client, data, **params):
    response = client.get(f"/api/v1/matches/{data['graph']['match']['id']}/metrics", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_match_and_team_metrics(client, analytics_data):
    body = metrics(client, analytics_data)
    values = body["metrics"]
    assert values == {"total_actions": 12, "passes": 4, "completed_passes": 3,
        "incomplete_passes": 1, "pass_completion_pct": 75.0, "progressive_passes": 1,
        "shots": 2, "shots_on_target": 2, "goals": 1, "assists": 1,
        "tackles": 2, "interceptions": 1, "turnovers": 2}
    teams = {item["team_id"]: item["metrics"] for item in body["teams"]}
    home = teams[analytics_data["graph"]["home"]["id"]]
    away = teams[analytics_data["graph"]["away"]["id"]]
    assert home["passes"] == 3 and home["pass_completion_pct"] == pytest.approx(66.67)
    assert home["goals"] == 1 and home["tackles"] == 1 and home["interceptions"] == 1
    assert away["passes"] == 1 and away["completed_passes"] == 1
    assert body["unattributed"] == {"unknown_participant_actions": 1, "no_player_actions": 1,
                                    "ambiguous_team_actions": 2}


def test_player_metrics_and_role_attribution(client, analytics_data):
    match_id, player_id = analytics_data["graph"]["match"]["id"], analytics_data["alex"]["id"]
    response = client.get(f"/api/v1/matches/{match_id}/players/{player_id}/metrics")
    assert response.status_code == 200, response.text
    values = response.json()["metrics"]
    assert values["total_actions"] == 6
    assert (values["passes"], values["completed_passes"], values["incomplete_passes"]) == (2, 1, 1)
    assert values["pass_completion_pct"] == 50.0 and values["progressive_passes"] == 1
    assert values["shots"] == 2 and values["shots_on_target"] == 2 and values["goals"] == 1
    assert values["tackles"] == 1 and values["interceptions"] == 0 and values["turnovers"] == 1


def test_progressive_pass_shots_goals_turnovers_and_defense(client, analytics_data):
    body = metrics(client, analytics_data)
    values = body["metrics"]
    assert values["progressive_passes"] == 1
    assert (values["shots"], values["shots_on_target"], values["goals"]) == (2, 2, 1)
    assert (values["turnovers"], values["tackles"], values["interceptions"]) == (2, 2, 1)
    assert values["assists"] == 1


def test_skill_tag_and_outcome_filters(client, analytics_data):
    passing = metrics(client, analytics_data, skill_id=analytics_data["skills"]["pass"]["id"])
    assert passing["metrics"]["total_actions"] == passing["metrics"]["passes"] == 4
    progressive = metrics(client, analytics_data, tag_id=analytics_data["progressive"]["id"])
    assert progressive["metrics"]["total_actions"] == progressive["metrics"]["progressive_passes"] == 1
    completed = metrics(client, analytics_data, outcome=" completed ")
    assert completed["metrics"]["total_actions"] == completed["metrics"]["completed_passes"] == 3


def test_player_period_session_and_time_filters(client, analytics_data):
    data = analytics_data
    player = metrics(client, data, player_id=data["alex"]["id"])
    assert player["metrics"]["total_actions"] == 6
    period = metrics(client, data, period="SECOND_HALF")
    assert period["metrics"]["total_actions"] == period["metrics"]["passes"] == 1
    session = metrics(client, data, session_id=data["graph"]["session"]["id"])
    assert session["metrics"]["total_actions"] == 12
    window = metrics(client, data, start_time=200, end_time=400)
    assert window["metrics"]["total_actions"] == 5
    assert window["metrics"]["passes"] == 2 and window["metrics"]["shots"] == 2


def test_archived_unknown_and_no_player_behavior(client, analytics_data):
    body = metrics(client, analytics_data)
    assert body["metrics"]["goals"] == 1  # Archived second goal is excluded.
    player_totals = sum(item["metrics"]["tackles"] for item in body["players"])
    assert player_totals == 1  # Unknown tackler is not attributed.
    assert sum(item["metrics"]["turnovers"] for item in body["players"]) == 1
    assert body["metrics"]["turnovers"] == 2  # No-player action still counts in match total.


def test_breakdowns_and_timeline_buckets_with_point_and_range(client, analytics_data):
    body = metrics(client, analytics_data, bucket_seconds=300)
    assert sum(item["count"] for item in body["breakdowns"]["actions_by_skill"]) == 12
    assert {item["label"]: item["count"] for item in body["breakdowns"]["actions_by_outcome"]}["Completed"] == 3
    assert {item["label"]: item["count"] for item in body["breakdowns"]["actions_by_tag"]}["Progressive Pass"] == 1
    assert body["breakdowns"]["timeline_buckets"] == [
        {"start_time": 0.0, "end_time": 300.0, "count": 3},
        {"start_time": 300.0, "end_time": 600.0, "count": 6},
        {"start_time": 600.0, "end_time": 900.0, "count": 3},
    ]
    range_event = next(item for item in body["breakdowns"]["events"] if item["video_end_time"] == 205)
    assert range_event["match_time"] == 200  # Ranges bucket/filter by their start instant.


def test_invalid_filter_and_bucket_validation(client, analytics_data):
    match_id = analytics_data["graph"]["match"]["id"]
    assert client.get(f"/api/v1/matches/{match_id}/metrics", params={"start_time": 20, "end_time": 10}).status_code == 422
    assert client.get(f"/api/v1/matches/{match_id}/metrics", params={"bucket_seconds": 7}).status_code == 422
    assert client.get(f"/api/v1/matches/{match_id}/metrics", params={"tag_id": uuid4()}).status_code == 404


def test_wrong_match_and_missing_player_match_access(client, create, analytics_data):
    data = analytics_data
    outsider = create("players", first_name="Outside", last_name="Player")
    path = f"/api/v1/matches/{data['graph']['match']['id']}/players/{outsider['id']}/metrics"
    assert client.get(path).status_code == 422
    assert client.get(f"/api/v1/matches/{data['graph']['match']['id']}/players/{uuid4()}/metrics").status_code == 404
    assert client.get(f"/api/v1/matches/{uuid4()}/metrics").status_code == 404


def test_empty_match_returns_zero_metrics(client, create, graph):
    empty = create("matches", home_team_id=graph["away"]["id"], away_team_id=graph["home"]["id"],
                   match_date="2026-09-24")
    response = client.get(f"/api/v1/matches/{empty['id']}/metrics")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["metrics"]["total_actions"] == 0 and body["metrics"]["passes"] == 0
    assert body["metrics"]["pass_completion_pct"] is None
    assert len(body["teams"]) == 2 and body["players"] == []
    assert body["breakdowns"]["timeline_buckets"] == []
