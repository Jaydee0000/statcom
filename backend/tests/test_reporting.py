"""Milestone 5 frontend reporting and traceability integration tests."""
import pytest


@pytest.fixture
def reporting_data(client, create, graph):
    player = graph["player"]
    create("memberships", player_id=player["id"], team_id=graph["home"]["id"],
           start_date="2026-01-01", jersey_number=8)
    outcome = create("skill-fields", skill_definition_id=graph["skill"]["id"], key="outcome",
                     label="Outcome", data_type="single_select", required=True,
                     options=["Completed", "Incomplete"])
    recovery = create("skills", name="Successful Recovery", category="Coach Metric")
    progressive = create("tags", name="Progressive Pass")

    matches = [graph["match"]]
    assert client.patch(f"/api/v1/matches/{graph['match']['id']}", json={
        "home_score": 2, "away_score": 0, "status": "completed"}).status_code == 200
    create("match-participants", match_id=graph["match"]["id"], player_id=player["id"],
           team_id=graph["home"]["id"], starter=True, position_played="CM",
           start_minute=0, end_minute=90)

    def extra_match(day, home_score, away_score, session_status):
        match = create("matches", season_id=graph["season"]["id"],
            competition_id=graph["competition"]["id"], home_team_id=graph["home"]["id"],
            away_team_id=graph["away"]["id"], match_date=day, home_score=home_score,
            away_score=away_score, status="completed")
        participant = create("match-participants", match_id=match["id"], player_id=player["id"],
            team_id=graph["home"]["id"], starter=session_status != "READY_FOR_REVIEW",
            position_played="CM", start_minute=10 if session_status == "READY_FOR_REVIEW" else 0,
            end_minute=70 if session_status == "READY_FOR_REVIEW" else 90)
        video = create("videos", match_id=match["id"], original_filename=f"{day}.mp4", duration_seconds=5400)
        session = create("annotation-sessions", match_id=match["id"], video_id=video["id"],
            status="IN_PROGRESS")
        if session_status in {"READY_FOR_REVIEW", "REVIEWED"}:
            response = client.patch(f"/api/v1/annotation-sessions/{session['id']}",
                                    json={"status": "READY_FOR_REVIEW"})
            assert response.status_code == 200, response.text
            session = response.json()
        if session_status == "REVIEWED":
            response = client.patch(f"/api/v1/annotation-sessions/{session['id']}",
                                    json={"status": "REVIEWED"})
            assert response.status_code == 200, response.text
            session = response.json()
        matches.append(match)
        return match, participant, video, session

    loss, _, loss_video, loss_session = extra_match("2026-09-24", 0, 1, "REVIEWED")
    draw, _, _, _ = extra_match("2026-09-25", 1, 1, "READY_FOR_REVIEW")

    def annotate(match, video, session, skill, at, *, result=None, tags=None):
        fields = ([{"field_definition_id": outcome["id"], "value": result}] if result else [])
        response = client.post(f"/api/v1/annotation-sessions/{session['id']}/annotations", json={
            "match_id": match["id"], "video_id": video["id"], "skill_definition_id": skill["id"],
            "video_start_time": at, "video_end_time": None, "match_period": "full_match",
            "match_time": at, "notes": None, "review_status": "REVIEWED", "created_by": None,
            "tag_ids": tags or [], "participants": [{"player_id": player["id"], "role": "Player"}],
            "field_values": fields})
        assert response.status_code == 201, response.text
        return response.json()

    win_annotations = [
        annotate(graph["match"], graph["video"], graph["session"], graph["skill"], 100,
                 result="Completed", tags=[progressive["id"]]),
        annotate(graph["match"], graph["video"], graph["session"], graph["skill"], 200, result="Incomplete"),
        annotate(graph["match"], graph["video"], graph["session"], graph["skill"], 300, result="Incomplete"),
        annotate(graph["match"], graph["video"], graph["session"], recovery, 400),
    ]
    annotate(loss, loss_video, loss_session, graph["skill"], 100, result="Completed")
    return {"player": player, "loss": loss, "draw": draw, "recovery": recovery,
            "progressive": progressive, "win_annotations": win_annotations}


def test_player_summary_real_totals_minutes_and_missing_coverage(client, graph, reporting_data):
    response = client.get(f"/api/v1/players/{reporting_data['player']['id']}/summary",
                          params=[("season_id", graph["season"]["id"]), ("metrics", "passes"),
                                  ("metrics", "pass_completion_pct"), ("metrics", "minutes_played")])
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["appearances"] == 3 and body["minutes"] == 240
    values = {item["key"]: item for item in body["metrics"]}
    assert values["passes"]["value"] == 4
    assert values["pass_completion_pct"] == {"key": "pass_completion_pct", "value": 50.0,
        "numerator": 2.0, "denominator": 4.0, "annotation_count": 4}
    assert body["coverage"]["complete"] is False


def test_player_history_is_chronological_and_preserves_draw(client, reporting_data):
    response = client.get(f"/api/v1/players/{reporting_data['player']['id']}/metrics/history",
                          params={"metrics": "passes"})
    assert response.status_code == 200, response.text
    rows = response.json()["matches"]
    assert [row["match"]["match_date"] for row in rows] == ["2026-09-23", "2026-09-24", "2026-09-25"]
    assert [row["match"]["result"] for row in rows] == ["W", "L", "D"]
    assert [row["metrics"][0]["value"] for row in rows] == [3, 1, 0]
    assert rows[-1]["match"]["coverage"]["status"] == "READY_FOR_REVIEW"


def test_result_comparison_groups_draws_and_recalculates_percentages(client, reporting_data):
    response = client.get(f"/api/v1/players/{reporting_data['player']['id']}/metrics/by-result",
                          params=[("metrics", "passes"), ("metrics", "pass_completion_pct")])
    assert response.status_code == 200, response.text
    groups = {item["result"]: item for item in response.json()["groups"]}
    assert set(groups) == {"W", "D", "L"} and groups["D"]["match_count"] == 1
    win = {item["key"]: item for item in groups["W"]["metrics"]}
    assert win["passes"]["value"] == 3  # Per-match observed value.
    assert win["pass_completion_pct"]["value"] == pytest.approx(33.33)
    assert win["pass_completion_pct"]["denominator"] == 3


def test_match_stats_returns_lineup_minutes_metrics_and_status(client, reporting_data):
    response = client.get(f"/api/v1/matches/{reporting_data['loss']['id']}/stats",
                          params={"metrics": "passes"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["participants"][0]["starter"] is True
    assert body["participants"][0]["minutes"] == 90
    assert body["participants"][0]["metrics"][0]["value"] == 1
    assert body["match"]["coverage"]["status"] == "REVIEWED"


def test_team_sheet_dynamic_custom_metric_and_ratio_total(client, graph, reporting_data):
    custom = f"skill:{reporting_data['recovery']['id']}"
    response = client.get("/api/v1/team-stats", params=[("team_id", graph["home"]["id"]),
        ("season_id", graph["season"]["id"]), ("metrics", "pass_completion_pct"), ("metrics", custom)])
    assert response.status_code == 200, response.text
    body = response.json()
    assert [item["key"] for item in body["metric_definitions"]] == ["pass_completion_pct", custom]
    assert body["metric_definitions"][1]["label"] == "Successful Recovery"
    totals = {item["key"]: item for item in body["totals"]["metrics"]}
    assert totals["pass_completion_pct"]["value"] == 50.0
    assert totals["pass_completion_pct"]["numerator"] == 2
    assert totals[custom]["value"] == 1
    assert body["incomplete_matches"] == 2


def test_traceable_metric_returns_annotation_video_and_timestamp(client, reporting_data):
    response = client.get(f"/api/v1/players/{reporting_data['player']['id']}/metrics/sources",
                          params={"metric": "progressive_passes"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["value"]["value"] == 1 and len(body["sources"]) == 1
    source = body["sources"][0]
    assert source["annotation_id"] == reporting_data["win_annotations"][0]["id"]
    assert source["video_id"] and source["video_start_time"] == 100 and source["match_time"] == 100
