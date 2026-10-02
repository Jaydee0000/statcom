"""Batched Milestone 5 reporting built on the canonical Milestone 4 events."""
from collections import defaultdict
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.models import (AnnotationSession, Competition, Match, MatchParticipant, Player,
                        PlayerTeamMembership, Season, SessionStatus, SkillDefinition, Tag,
                        Team, Video)
from app.services.errors import DomainError
from app.services.metrics import (_event_actor_players, _player_is_actor,
                                  load_events_for_matches)


STANDARD_METRICS = (
    dict(key="appearances", label="Matches Played", format="count", aggregation="sum", traceable=False),
    dict(key="minutes_played", label="Minutes", format="minutes", aggregation="sum", traceable=False),
    dict(key="total_actions", label="Actions", format="count", aggregation="sum", traceable=True),
    dict(key="passes", label="Pass Attempts", format="count", aggregation="sum", traceable=True),
    dict(key="completed_passes", label="Completed Passes", format="count", aggregation="sum", traceable=True),
    dict(key="pass_completion_pct", label="Pass Completion", format="percent", aggregation="ratio",
         numerator_key="completed_passes", denominator_key="decided_passes", traceable=True),
    dict(key="progressive_passes", label="Progressive Passes", format="count", aggregation="sum", traceable=True),
    dict(key="shots", label="Shots", format="count", aggregation="sum", traceable=True),
    dict(key="shots_on_target", label="Shots on Target", format="count", aggregation="sum", traceable=True),
    dict(key="goals", label="Goals", format="count", aggregation="sum", traceable=True),
    dict(key="assists", label="Assists", format="count", aggregation="sum", traceable=True),
    dict(key="tackles", label="Tackles", format="count", aggregation="sum", traceable=True),
    dict(key="interceptions", label="Interceptions", format="count", aggregation="sum", traceable=True),
    dict(key="turnovers", label="Turnovers", format="count", aggregation="sum", traceable=True),
)
DEFAULT_ROSTER = ("goals", "assists")
DEFAULT_PROFILE = ("minutes_played", "goals", "assists", "passes", "completed_passes",
                   "pass_completion_pct", "progressive_passes", "tackles", "interceptions", "turnovers")
DEFAULT_MATCH = ("passes", "pass_completion_pct", "progressive_passes", "tackles", "interceptions", "turnovers")


def _definition(item: dict) -> dict:
    return {"numerator_key": None, "denominator_key": None, "supports_per_90": False,
            "custom": False, **item}


def metric_catalog(db: Session) -> list[dict]:
    definitions = [_definition(item) for item in STANDARD_METRICS]
    skills = db.scalars(select(SkillDefinition).where(SkillDefinition.is_active.is_(True))
                       .order_by(SkillDefinition.name, SkillDefinition.version)).all()
    definitions.extend(_definition(dict(key=f"skill:{skill.id}", label=skill.name,
        format="count", aggregation="sum", traceable=True, custom=True)) for skill in skills)
    tags = db.scalars(select(Tag).where(Tag.is_active.is_(True)).order_by(Tag.name)).all()
    definitions.extend(_definition(dict(key=f"tag:{tag.id}", label=tag.name,
        format="count", aggregation="sum", traceable=True, custom=True)) for tag in tags)
    return definitions


def _select_definitions(db: Session, keys: list[str] | None, defaults: tuple[str, ...]) -> list[dict]:
    catalog = metric_catalog(db)
    indexed = {item["key"]: item for item in catalog}
    requested = list(dict.fromkeys(keys or defaults))
    unknown = [key for key in requested if key not in indexed]
    if unknown:
        raise DomainError(f"Unknown metric: {unknown[0]}")
    return [indexed[key] for key in requested]


def _minutes(participant: MatchParticipant) -> float | None:
    if participant.start_minute is None or participant.end_minute is None:
        return None
    return round(participant.end_minute - participant.start_minute, 2)


def _coverage(statuses: list[SessionStatus]) -> dict:
    if not statuses or all(status == SessionStatus.NOT_STARTED for status in statuses):
        status = "NOT_STARTED"
    elif all(status == SessionStatus.REVIEWED for status in statuses):
        status = "REVIEWED"
    elif all(status in (SessionStatus.READY_FOR_REVIEW, SessionStatus.REVIEWED) for status in statuses):
        status = "READY_FOR_REVIEW"
    else:
        status = "IN_PROGRESS"
    reviewed = sum(item == SessionStatus.REVIEWED for item in statuses)
    return {"status": status, "complete": bool(statuses) and reviewed == len(statuses),
            "session_count": len(statuses), "reviewed_sessions": reviewed}


def _result(match: Match, team_id: UUID) -> str | None:
    if match.home_score is None or match.away_score is None:
        return None
    own, other = ((match.home_score, match.away_score) if match.home_team_id == team_id
                  else (match.away_score, match.home_score))
    return "W" if own > other else "L" if own < other else "D"


def _event_matches_metric(event, player_id: UUID | None, key: str) -> bool:
    if player_id is not None:
        if key == "total_actions":
            if player_id not in {value for value, _ in event.participants}:
                return False
        elif key.startswith(("skill:", "tag:")):
            if player_id not in _event_actor_players(event):
                return False
        elif not _player_is_actor(event, player_id, key if key != "pass_completion_pct" else "passes"):
            return False
    if key == "total_actions":
        return True
    if key == "pass_completion_pct":
        return bool(event.flags["completed_passes"] or event.flags["incomplete_passes"])
    if key.startswith("skill:"):
        return event.skill_id == UUID(key.split(":", 1)[1])
    if key.startswith("tag:"):
        expected = UUID(key.split(":", 1)[1])
        return any(tag_id == expected for tag_id, _ in event.tags)
    return bool(event.flags.get(key, 0))


def _metric_value(definition: dict, events: list, player_id: UUID | None = None,
                  minutes: float | None = None, appearances: int = 0) -> dict:
    key = definition["key"]
    if key == "appearances":
        return {"key": key, "value": float(appearances), "numerator": None, "denominator": None, "annotation_count": 0}
    if key == "minutes_played":
        return {"key": key, "value": minutes, "numerator": None, "denominator": None, "annotation_count": 0}
    contributors = [event for event in events if _event_matches_metric(event, player_id, key)]
    if key == "pass_completion_pct":
        completed = sum(_event_matches_metric(event, player_id, "completed_passes") for event in events)
        incomplete = sum(_event_matches_metric(event, player_id, "incomplete_passes") for event in events)
        denominator = completed + incomplete
        value = round(completed / denominator * 100, 2) if denominator else None
        return {"key": key, "value": value, "numerator": float(completed),
                "denominator": float(denominator), "annotation_count": len(contributors)}
    return {"key": key, "value": float(len(contributors)), "numerator": None,
            "denominator": None, "annotation_count": len(contributors)}


def _values(definitions: list[dict], events: list, player_id: UUID | None = None,
            minutes: float | None = None, appearances: int = 0) -> list[dict]:
    return [_metric_value(item, events, player_id, minutes, appearances) for item in definitions]


class ReportingData:
    def __init__(self, db: Session, *, season_id=None, competition_id=None, team_id=None,
                 match_id=None, date_from=None, date_to=None):
        home, away = aliased(Team), aliased(Team)
        query = (select(Match, home, away, Season, Competition)
                 .join(home, Match.home_team_id == home.id).join(away, Match.away_team_id == away.id)
                 .outerjoin(Season, Match.season_id == Season.id)
                 .outerjoin(Competition, Match.competition_id == Competition.id))
        if season_id: query = query.where(Match.season_id == season_id)
        if competition_id: query = query.where(Match.competition_id == competition_id)
        if team_id: query = query.where((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
        if match_id: query = query.where(Match.id == match_id)
        if date_from: query = query.where(Match.match_date >= date_from)
        if date_to: query = query.where(Match.match_date <= date_to)
        self.rows = db.execute(query.order_by(Match.match_date, Match.id)).all()
        self.matches = {row[0].id: row[0] for row in self.rows}
        ids = list(self.matches)
        self.events, self.participants, self.player_teams = load_events_for_matches(db, ids)
        sessions = db.execute(select(AnnotationSession.match_id, AnnotationSession.status)
                              .where(AnnotationSession.match_id.in_(ids))).all() if ids else []
        self.statuses = defaultdict(list)
        for mid, status in sessions: self.statuses[mid].append(status)
        self.coverage = {mid: _coverage(self.statuses[mid]) for mid in ids}
        self.row_by_id = {row[0].id: row for row in self.rows}

    def reference(self, match_id: UUID, team_id: UUID | None = None) -> dict:
        match, home, away, season, competition = self.row_by_id[match_id]
        opponent = None
        result = None
        if team_id:
            opponent = away.name if match.home_team_id == team_id else home.name
            result = _result(match, team_id)
        return {"id": match.id, "match_date": match.match_date,
                "home_team_id": match.home_team_id, "home_team": home.name,
                "away_team_id": match.away_team_id, "away_team": away.name,
                "home_score": match.home_score, "away_score": match.away_score,
                "result": result, "opponent": opponent,
                "season_id": match.season_id, "season": season.name if season else None,
                "competition_id": match.competition_id, "competition": competition.name if competition else None,
                "location": match.location, "status": match.status, "coverage": self.coverage[match.id]}


def _current_memberships(db: Session, player_ids: list[UUID] | None = None, team_id: UUID | None = None):
    query = (select(PlayerTeamMembership, Team).join(Team, PlayerTeamMembership.team_id == Team.id)
             .where(PlayerTeamMembership.status == "active",
                    (PlayerTeamMembership.end_date.is_(None)) | (PlayerTeamMembership.end_date >= date.today()))
             .order_by(PlayerTeamMembership.player_id, PlayerTeamMembership.start_date.desc()))
    if player_ids is not None: query = query.where(PlayerTeamMembership.player_id.in_(player_ids))
    if team_id: query = query.where(PlayerTeamMembership.team_id == team_id)
    result = {}
    for membership, team in db.execute(query):
        result.setdefault(membership.player_id, (membership, team))
    return result


def _identity(player: Player, membership=None) -> dict:
    row, team = membership or (None, None)
    return {"id": player.id, "first_name": player.first_name, "last_name": player.last_name,
            "date_of_birth": player.date_of_birth, "primary_position": player.primary_position,
            "secondary_position": player.secondary_position, "preferred_foot": player.preferred_foot,
            "photo_url": player.photo_url, "team_id": team.id if team else None,
            "team_name": team.name if team else None, "jersey_number": row.jersey_number if row else None,
            "availability": row.status if row else None}


def _sum_minutes(rows) -> float | None:
    values = [_minutes(participant) for participant, _ in rows]
    return round(sum(value for value in values if value is not None), 2) if values and all(value is not None for value in values) else None


def roster(db: Session, *, team_id=None, season_id=None, position=None, metrics=None) -> dict:
    definitions = _select_definitions(db, metrics, DEFAULT_ROSTER)
    data = ReportingData(db, team_id=team_id, season_id=season_id)
    participation = defaultdict(list)
    for mid, rows in data.participants.items():
        for participant, player in rows:
            if team_id and participant.team_id != team_id: continue
            participation[player.id].append((mid, participant, player))
    query = select(Player).order_by(Player.last_name, Player.first_name)
    if position: query = query.where(Player.primary_position == position)
    players = db.scalars(query).all()
    memberships = _current_memberships(db, [player.id for player in players], team_id)
    if team_id: players = [player for player in players if player.id in memberships]
    output = []
    for player in players:
        appearances = participation[player.id]
        match_ids = [mid for mid, _, _ in appearances]
        events = [event for mid in match_ids for event in data.events[mid]]
        minutes = _sum_minutes([(part, p) for _, part, p in appearances])
        recent = [_result(data.matches[mid], part.team_id) for mid, part, _ in sorted(
            appearances, key=lambda item: data.matches[item[0]].match_date, reverse=True)[:5]]
        output.append({**_identity(player, memberships.get(player.id)), "appearances": len(appearances),
            "minutes": minutes, "recent_form": [item for item in recent if item],
            "metrics": _values(definitions, events, player.id, minutes, len(appearances)),
            "incomplete_matches": sum(not data.coverage[mid]["complete"] for mid in match_ids)})
    return {"metric_definitions": definitions, "players": output}


def _player_or_404(db: Session, player_id: UUID) -> Player:
    player = db.get(Player, player_id)
    if player is None: raise DomainError("Player not found", 404)
    return player


def player_history(db: Session, player_id: UUID, *, season_id=None, competition_id=None, metrics=None) -> dict:
    player = _player_or_404(db, player_id)
    definitions = _select_definitions(db, metrics, DEFAULT_PROFILE)
    data = ReportingData(db, season_id=season_id, competition_id=competition_id)
    rows = []
    for mid in sorted(data.matches, key=lambda value: (data.matches[value].match_date, str(value))):
        found = next(((part, p) for part, p in data.participants[mid] if part.player_id == player_id), None)
        if not found: continue
        participant, _ = found
        minutes = _minutes(participant)
        rows.append({"match": data.reference(mid, participant.team_id), "team_id": participant.team_id,
            "starter": participant.starter, "position": participant.position_played, "minutes": minutes,
            "metrics": _values(definitions, data.events[mid], player_id, minutes, 1)})
    membership = _current_memberships(db, [player_id]).get(player_id)
    return {"player": _identity(player, membership), "metric_definitions": definitions, "matches": rows}


def player_summary(db: Session, player_id: UUID, **filters) -> dict:
    history = player_history(db, player_id, **filters)
    definitions = history["metric_definitions"]
    match_ids = [row["match"]["id"] for row in history["matches"]]
    data = ReportingData(db, match_id=None, season_id=filters.get("season_id"), competition_id=filters.get("competition_id"))
    events = [event for mid in match_ids for event in data.events.get(mid, [])]
    minute_values = [row["minutes"] for row in history["matches"]]
    minutes = sum(minute_values) if minute_values and all(value is not None for value in minute_values) else None
    statuses = [status for mid in match_ids for status in data.statuses[mid]]
    return {"player": history["player"], "appearances": len(history["matches"]), "minutes": minutes,
            "metrics": _values(definitions, events, player_id, minutes, len(history["matches"])),
            "coverage": _coverage(statuses)}


def result_comparison(db: Session, player_id: UUID, *, season_id=None, competition_id=None, metrics=None) -> dict:
    _player_or_404(db, player_id)
    definitions = _select_definitions(db, metrics, DEFAULT_PROFILE)
    data = ReportingData(db, season_id=season_id, competition_id=competition_id)
    appearances = []
    for mid in data.matches:
        participant = next((part for part, _ in data.participants[mid] if part.player_id == player_id), None)
        if participant:
            appearances.append((mid, participant))
    groups = []
    for result in ("W", "D", "L"):
        rows = [(mid, participant) for mid, participant in appearances if _result(data.matches[mid], participant.team_id) == result]
        combined = [event for mid, _ in rows for event in data.events[mid]]
        minute_values = [_minutes(participant) for _, participant in rows]
        minutes = sum(minute_values) if rows and all(value is not None for value in minute_values) else None
        values = _values(definitions, combined, player_id, minutes, len(rows))
        # Result comparison reports observed per-match values. Ratio metrics keep
        # their summed numerator/denominator so percentages are never averaged.
        for value, definition in zip(values, definitions):
            if rows and definition["aggregation"] == "sum" and value["value"] is not None:
                value["value"] = round(value["value"] / len(rows), 2)
        groups.append({"result": result, "match_count": len(rows),
            "complete_match_count": sum(data.coverage[mid]["complete"] for mid, _ in rows),
            "metrics": values})
    return {"player_id": player_id, "metric_definitions": definitions, "groups": groups}


def list_matches(db: Session, *, team_id=None, season_id=None, competition_id=None) -> dict:
    data = ReportingData(db, team_id=team_id, season_id=season_id, competition_id=competition_id)
    return {"matches": [data.reference(mid) for mid in sorted(data.matches,
        key=lambda value: (data.matches[value].match_date, str(value)), reverse=True)]}


def match_stats(db: Session, match_id: UUID, *, metrics=None) -> dict:
    definitions = _select_definitions(db, metrics, DEFAULT_MATCH)
    data = ReportingData(db, match_id=match_id)
    if match_id not in data.matches: raise DomainError("Match not found", 404)
    memberships = _current_memberships(db, [participant.player_id for participant, _ in data.participants[match_id]])
    participants = []
    for participant, player in data.participants[match_id]:
        minutes = _minutes(participant)
        participants.append({"player": _identity(player, memberships.get(player.id)), "team_id": participant.team_id,
            "starter": participant.starter, "position": participant.position_played, "minutes": minutes,
            "metrics": _values(definitions, data.events[match_id], player.id, minutes, 1)})
    videos = db.scalars(select(Video).where(Video.match_id == match_id).order_by(Video.created_at)).all()
    sessions = {item.video_id: item for item in db.scalars(select(AnnotationSession).where(
        AnnotationSession.match_id == match_id)).all()}
    return {"match": data.reference(match_id), "metric_definitions": definitions, "participants": participants,
            "videos": [{"id": video.id, "original_filename": video.original_filename, "period": video.period,
                "duration_seconds": video.duration_seconds, "session_id": sessions.get(video.id).id if sessions.get(video.id) else None,
                "annotation_status": sessions.get(video.id).status.value if sessions.get(video.id) else "NOT_STARTED"}
                for video in videos]}


def team_stat_sheet(db: Session, team_id: UUID, *, season_id=None, competition_id=None, match_id=None,
                    date_from=None, date_to=None, position=None, metrics=None) -> dict:
    if db.get(Team, team_id) is None: raise DomainError("Team not found", 404)
    definitions = _select_definitions(db, metrics, DEFAULT_MATCH)
    data = ReportingData(db, team_id=team_id, season_id=season_id, competition_id=competition_id,
                         match_id=match_id, date_from=date_from, date_to=date_to)
    by_player = defaultdict(list)
    for mid, rows in data.participants.items():
        for participant, player in rows:
            if participant.team_id == team_id and (not position or (participant.position_played or player.primary_position) == position):
                by_player[player.id].append((mid, participant, player))
    memberships = _current_memberships(db, list(by_player), team_id)
    players = []
    for player_id, rows in by_player.items():
        player = rows[0][2]
        minutes = _sum_minutes([(part, p) for _, part, p in rows])
        events = [event for mid, _, _ in rows for event in data.events[mid]]
        recent = [_result(data.matches[mid], team_id) for mid, _, _ in sorted(
            rows, key=lambda item: data.matches[item[0]].match_date, reverse=True)[:5]]
        players.append({**_identity(player, memberships.get(player_id)), "appearances": len(rows), "minutes": minutes,
            "recent_form": [item for item in recent if item],
            "metrics": _values(definitions, events, player_id, minutes, len(rows)),
            "incomplete_matches": sum(not data.coverage[mid]["complete"] for mid, _, _ in rows)})
    players.sort(key=lambda item: (item["last_name"].casefold(), item["first_name"].casefold()))
    team_events = []
    team_minutes = 0.0
    minutes_known = True
    appearances = 0
    for item in players:
        appearances += item["appearances"]
        if item["minutes"] is None: minutes_known = False
        else: team_minutes += item["minutes"]
    for mid, events in data.events.items():
        actors = data.player_teams[mid]
        team_events.extend(event for event in events if any(actors.get(pid) == team_id for pid in _event_actor_players(event)))
    return {"metric_definitions": definitions, "players": players,
            "totals": {"team_id": team_id, "metrics": _values(definitions, team_events, None,
                team_minutes if minutes_known else None, appearances)},
            "match_count": len(data.matches),
            "incomplete_matches": sum(not item["complete"] for item in data.coverage.values())}


def metric_sources(db: Session, player_id: UUID, metric: str, *, season_id=None, competition_id=None,
                   match_id=None) -> dict:
    player = _player_or_404(db, player_id)
    definition = _select_definitions(db, [metric], ())[0]
    if not definition["traceable"]: raise DomainError("This metric has no annotation sources")
    data = ReportingData(db, season_id=season_id, competition_id=competition_id, match_id=match_id)
    relevant = []
    for mid, events in data.events.items():
        participant = next((part for part, _ in data.participants[mid] if part.player_id == player_id), None)
        if not participant: continue
        for event in events:
            if _event_matches_metric(event, player_id, metric): relevant.append((mid, participant.team_id, event))
    value = _metric_value(definition, [event for _, _, event in relevant], player_id)
    sources = []
    for mid, team_id, event in relevant:
        ref = data.reference(mid, team_id)
        sources.append({"annotation_id": event.annotation.id,
            "annotation_session_id": event.annotation.annotation_session_id, "video_id": event.annotation.video_id,
            "match_id": mid, "match_date": data.matches[mid].match_date, "opponent": ref["opponent"],
            "player_id": player.id, "player_name": f"{player.first_name} {player.last_name}",
            "skill": event.skill_name, "tags": [name for _, name in event.tags], "outcomes": event.outcomes,
            "match_time": event.match_time, "video_start_time": event.annotation.video_start_time,
            "video_end_time": event.annotation.video_end_time, "period": event.annotation.match_period})
    return {"metric": definition, "value": value, "sources": sources}
