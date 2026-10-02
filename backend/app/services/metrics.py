"""Deterministic, read-only metrics derived from persisted annotations."""
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import unicodedata
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Annotation, AnnotationFieldValue, AnnotationParticipant, AnnotationSession,
    AnnotationTag, Match, MatchParticipant, Player, PlayerTeamMembership,
    SkillDefinition, SkillFieldDefinition, Tag, Team, Video,
)
from app.services.errors import DomainError


PASS_NAMES = {"pass", "passes", "passing", "progressive pass", "progressive passes"}
SHOT_NAMES = {"shot", "shots", "shooting", "shot on target", "shots on target", "goal", "goals"}
COMPLETED = {"complete", "completed", "success", "successful"}
INCOMPLETE = {"incomplete", "failed", "failure", "unsuccessful"}
ON_TARGET = {"on target", "shot on target", "goal", "scored"}
GOAL_VALUES = {"goal", "scored"}
OUTCOME_FIELDS = {"outcome", "result", "shot outcome", "pass outcome"}
TEAM_FIELDS = {"team", "team id", "acting team", "possessing team"}
METRIC_ROLE_NAMES = {
    "passes": {"passer"},
    "progressive_passes": {"passer"},
    "shots": {"shooter"},
    "shots_on_target": {"shooter"},
    "goals": {"scorer", "shooter"},
    "assists": {"assister", "provider"},
    "tackles": {"tackler", "defender"},
    "interceptions": {"interceptor", "defender"},
    "turnovers": {"turnover", "loser", "player"},
}
GENERIC_ACTOR_ROLES = {"actor", "player", "primary"}
METRIC_KEYS = ("passes", "completed_passes", "incomplete_passes", "progressive_passes", "shots",
               "shots_on_target", "goals", "assists", "tackles", "interceptions", "turnovers")


def norm(value: str | None) -> str:
    return " ".join(unicodedata.normalize("NFKC", value or "").casefold().replace("_", " ").split())


@dataclass
class Event:
    annotation: Annotation
    skill_id: UUID | None
    skill_name: str
    match_time: float
    tags: list[tuple[UUID, str]] = field(default_factory=list)
    participants: list[tuple[UUID | None, str]] = field(default_factory=list)
    values: list[tuple[SkillFieldDefinition, object]] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)
    explicit_team_ids: set[UUID] = field(default_factory=set)
    flags: dict[str, int] = field(default_factory=dict)


def _classify(event: Event) -> dict[str, int]:
    names = {norm(event.skill_name), *(norm(name) for _, name in event.tags)}
    outcomes = {norm(value) for value in event.outcomes}
    is_pass = bool(names & PASS_NAMES)
    completed = is_pass and bool(outcomes & COMPLETED or names & {"completed pass", "successful pass"})
    incomplete = is_pass and bool(outcomes & INCOMPLETE or names & {"incomplete pass", "failed pass", "unsuccessful pass"})
    is_shot = bool(names & SHOT_NAMES)
    on_target = is_shot and bool(outcomes & ON_TARGET or names & {"shot on target", "goal"})
    goal = bool(names & {"goal", "goals"}) or (is_shot and bool(outcomes & GOAL_VALUES))
    return {
        "passes": int(is_pass), "completed_passes": int(completed), "incomplete_passes": int(incomplete),
        "progressive_passes": int(is_pass and bool(names & {"progressive pass", "progressive passes"})),
        "shots": int(is_shot), "shots_on_target": int(on_target), "goals": int(goal),
        "assists": int(bool(names & {"assist", "assists"})), "tackles": int(bool(names & {"tackle", "tackles"})),
        "interceptions": int(bool(names & {"interception", "interceptions"})),
        "turnovers": int(bool(names & {"turnover", "turnovers"})),
    }


def _metric_dict(events: list[Event], player_id: UUID | None = None) -> dict:
    values = {key: 0 for key in METRIC_KEYS}
    values["total_actions"] = len(events)
    for event in events:
        for key in METRIC_KEYS:
            if not event.flags[key]:
                continue
            if player_id is None or _player_is_actor(event, player_id, key):
                values[key] += event.flags[key]
    decided = values["completed_passes"] + values["incomplete_passes"]
    values["pass_completion_pct"] = round(values["completed_passes"] / decided * 100, 2) if decided else None
    return values


def _player_is_actor(event: Event, player_id: UUID, metric: str) -> bool:
    roles = {norm(role) for participant_id, role in event.participants if participant_id == player_id}
    if not roles:
        return False
    base = "passes" if metric in {"completed_passes", "incomplete_passes"} else metric
    if roles & (METRIC_ROLE_NAMES.get(base, set()) | GENERIC_ACTOR_ROLES):
        return True
    identified = {participant_id for participant_id, _ in event.participants if participant_id is not None}
    return identified == {player_id}


def _event_actor_players(event: Event) -> set[UUID]:
    actors = set()
    active_metrics = {key for key, value in event.flags.items() if value}
    for player_id, role in event.participants:
        if player_id is None:
            continue
        normalized_role = norm(role)
        expected = GENERIC_ACTOR_ROLES.copy()
        for metric in active_metrics:
            base = "passes" if metric in {"completed_passes", "incomplete_passes"} else metric
            expected |= METRIC_ROLE_NAMES.get(base, set())
        if normalized_role in expected:
            actors.add(player_id)
    identified = {player_id for player_id, _ in event.participants if player_id is not None}
    return actors or (identified if len(identified) == 1 else set())


def _team_for_event(event: Event, player_teams: dict[UUID, UUID]) -> UUID | None:
    if len(event.explicit_team_ids) == 1:
        return next(iter(event.explicit_team_ids))
    if len(event.explicit_team_ids) > 1:
        return None
    actor_teams = {player_teams[player_id] for player_id in _event_actor_players(event) if player_id in player_teams}
    return next(iter(actor_teams)) if len(actor_teams) == 1 else None


def load_events_for_matches(db: Session, match_ids: list[UUID]) -> tuple[dict[UUID, list[Event]], dict[UUID, list], dict[UUID, dict[UUID, UUID]]]:
    """Bulk-load and classify the canonical Milestone 4 events for several matches.

    Reporting endpoints use this instead of invoking the single-match loader in a
    loop.  Keeping classification here ensures every consumer uses identical
    metric definitions and actor attribution.
    """
    if not match_ids:
        return {}, {}, {}
    rows = db.execute(select(Annotation, SkillDefinition, AnnotationSession, Video)
        .outerjoin(SkillDefinition, Annotation.skill_definition_id == SkillDefinition.id)
        .join(AnnotationSession, Annotation.annotation_session_id == AnnotationSession.id)
        .join(Video, Annotation.video_id == Video.id)
        .where(Annotation.match_id.in_(match_ids), Annotation.deleted_at.is_(None))
        .order_by(Annotation.match_id, Annotation.match_time, Annotation.video_start_time, Annotation.id)).all()
    events = {}
    for annotation, skill, session, video in rows:
        timestamp = annotation.match_time
        if timestamp is None:
            timestamp = max(0, annotation.video_start_time - video.video_time_offset + video.match_time_offset)
        events[annotation.id] = Event(annotation=annotation, skill_id=skill.id if skill else None,
                                      skill_name=skill.name if skill else "Unclassified", match_time=timestamp)
    ids = list(events)
    if ids:
        for annotation_id, tag_id, tag_name in db.execute(select(AnnotationTag.annotation_id, Tag.id, Tag.name)
                .join(Tag, AnnotationTag.tag_id == Tag.id).where(AnnotationTag.annotation_id.in_(ids))):
            events[annotation_id].tags.append((tag_id, tag_name))
        for annotation_id, player_id, role in db.execute(select(
                AnnotationParticipant.annotation_id, AnnotationParticipant.player_id, AnnotationParticipant.role)
                .where(AnnotationParticipant.annotation_id.in_(ids))):
            events[annotation_id].participants.append((player_id, role))
        for field_value, definition in db.execute(select(AnnotationFieldValue, SkillFieldDefinition)
                .join(SkillFieldDefinition, AnnotationFieldValue.field_definition_id == SkillFieldDefinition.id)
                .where(AnnotationFieldValue.annotation_id.in_(ids))):
            annotation_id, value = field_value.annotation_id, field_value.value
            event = events[annotation_id]
            event.values.append((definition, value))
            field_name = norm(definition.key) or norm(definition.label)
            label_name = norm(definition.label)
            if field_name in OUTCOME_FIELDS or label_name in OUTCOME_FIELDS:
                if isinstance(value, str):
                    event.outcomes.append(value)
            if field_name in TEAM_FIELDS or label_name in TEAM_FIELDS:
                if field_value.team_value_id is not None:
                    event.explicit_team_ids.add(field_value.team_value_id)
                elif isinstance(value, str):
                    try: event.explicit_team_ids.add(UUID(value))
                    except ValueError: pass
    participants = db.execute(select(MatchParticipant, Player).join(Player, MatchParticipant.player_id == Player.id)
        .where(MatchParticipant.match_id.in_(match_ids))
        .order_by(MatchParticipant.match_id, Player.last_name, Player.first_name)).all()
    loaded = list(events.values())
    for event in loaded:
        event.outcomes = list(dict.fromkeys(event.outcomes))
        event.flags = _classify(event)
    events_by_match = {match_id: [] for match_id in match_ids}
    participants_by_match = {match_id: [] for match_id in match_ids}
    teams_by_match = {match_id: {} for match_id in match_ids}
    for event in loaded:
        events_by_match[event.annotation.match_id].append(event)
    for participant, player in participants:
        participants_by_match[participant.match_id].append((participant, player))
        teams_by_match[participant.match_id][participant.player_id] = participant.team_id
    return events_by_match, participants_by_match, teams_by_match


def _load(db: Session, match: Match) -> tuple[list[Event], list, dict[UUID, UUID]]:
    events, participants, teams = load_events_for_matches(db, [match.id])
    return events[match.id], participants[match.id], teams[match.id]


def _validate_filters(db: Session, match: Match, filters: dict):
    player_id = filters.get("player_id")
    if player_id is not None:
        if db.get(Player, player_id) is None:
            raise DomainError("Player not found", 404)
        if not db.scalar(select(MatchParticipant.id).where(
                MatchParticipant.match_id == match.id, MatchParticipant.player_id == player_id)):
            raise DomainError("Player did not participate in this match")
    for key, model, message in (("skill_id", SkillDefinition, "Skill not found"), ("tag_id", Tag, "Tag not found")):
        if filters.get(key) is not None and db.get(model, filters[key]) is None:
            raise DomainError(message, 404)
    session_id = filters.get("session_id")
    if session_id is not None:
        session = db.get(AnnotationSession, session_id)
        if session is None:
            raise DomainError("Annotation session not found", 404)
        if session.match_id != match.id:
            raise DomainError("Annotation session does not belong to this match")
    if filters.get("start_time") is not None and filters.get("end_time") is not None:
        if filters["end_time"] <= filters["start_time"]:
            raise DomainError("end_time must be greater than start_time")


def _filtered(events: list[Event], filters: dict) -> list[Event]:
    result = []
    expected_outcome = norm(filters.get("outcome"))
    expected_period = norm(filters.get("period"))
    for event in events:
        annotation = event.annotation
        player_ids = {player_id for player_id, _ in event.participants if player_id is not None}
        if filters.get("player_id") is not None and filters["player_id"] not in player_ids:
            continue
        if filters.get("skill_id") is not None and event.skill_id != filters["skill_id"]:
            continue
        if filters.get("tag_id") is not None and filters["tag_id"] not in {tag_id for tag_id, _ in event.tags}:
            continue
        if expected_outcome and expected_outcome not in {norm(value) for value in event.outcomes}:
            continue
        if filters.get("start_time") is not None and event.match_time < filters["start_time"]:
            continue
        if filters.get("end_time") is not None and event.match_time >= filters["end_time"]:
            continue
        if filters.get("session_id") is not None and annotation.annotation_session_id != filters["session_id"]:
            continue
        if expected_period and norm(annotation.match_period) != expected_period:
            continue
        result.append(event)
    return result


def _breakdowns(events: list[Event], players: dict[UUID, Player], bucket_seconds: int) -> dict:
    skills, outcomes, player_counts, tags, buckets = Counter(), Counter(), Counter(), Counter(), Counter()
    skill_ids, tag_ids = {}, {}
    for event in events:
        skills[event.skill_name] += 1
        skill_ids[event.skill_name] = event.skill_id
        for outcome in set(event.outcomes):
            outcomes[outcome] += 1
        for player_id in {value for value, _ in event.participants if value is not None}:
            player_counts[player_id] += 1
        for tag_id, name in set(event.tags):
            tags[name] += 1
            tag_ids[name] = tag_id
        buckets[int(event.match_time // bucket_seconds) * bucket_seconds] += 1
    def items(counter, identifiers=None):
        return [{"id": identifiers.get(label) if identifiers else None, "label": str(label), "count": count}
                for label, count in sorted(counter.items(), key=lambda item: (-item[1], str(item[0]).casefold()))]
    player_items = [{"id": player_id, "label": f"{players[player_id].first_name} {players[player_id].last_name}", "count": count}
                    for player_id, count in sorted(player_counts.items(), key=lambda item: (-item[1], str(item[0]))) if player_id in players]
    return {"actions_by_skill": items(skills, skill_ids), "actions_by_outcome": items(outcomes),
            "actions_by_player": player_items, "actions_by_tag": items(tags, tag_ids),
            "timeline_buckets": [{"start_time": start, "end_time": start + bucket_seconds, "count": count}
                                 for start, count in sorted(buckets.items())],
            "events": [{"annotation_id": event.annotation.id,
                        "annotation_session_id": event.annotation.annotation_session_id,
                        "video_id": event.annotation.video_id, "skill_id": event.skill_id,
                        "skill": event.skill_name, "video_start_time": event.annotation.video_start_time,
                        "video_end_time": event.annotation.video_end_time, "match_time": event.match_time,
                        "period": event.annotation.match_period,
                        "player_ids": sorted({value for value, _ in event.participants if value is not None}, key=str),
                        "tag_ids": sorted({value for value, _ in event.tags}, key=str),
                        "outcomes": event.outcomes} for event in events]}


def _jerseys(db: Session, match: Match, player_ids: list[UUID]) -> dict[tuple[UUID, UUID], int | None]:
    if not player_ids:
        return {}
    memberships = db.scalars(select(PlayerTeamMembership).where(
        PlayerTeamMembership.player_id.in_(player_ids),
        PlayerTeamMembership.team_id.in_([match.home_team_id, match.away_team_id]),
        PlayerTeamMembership.start_date <= match.match_date,
        (PlayerTeamMembership.end_date.is_(None)) | (PlayerTeamMembership.end_date >= match.match_date))).all()
    return {(item.player_id, item.team_id): item.jersey_number for item in memberships}


def match_metrics(db: Session, match_id: UUID, filters: dict, bucket_seconds: int = 300) -> dict:
    if bucket_seconds not in (60, 300, 600, 900):
        raise DomainError("bucket_seconds must be 60, 300, 600, or 900")
    match = db.get(Match, match_id)
    if match is None:
        raise DomainError("Match not found", 404)
    filters = {**filters, "bucket_seconds": bucket_seconds}
    _validate_filters(db, match, filters)
    all_events, participant_rows, player_teams = _load(db, match)
    events = _filtered(all_events, filters)
    player_models = {player.id: player for _, player in participant_rows}
    teams = {team.id: team for team in db.scalars(select(Team).where(
        Team.id.in_([match.home_team_id, match.away_team_id])))}
    by_team = defaultdict(list)
    ambiguous = 0
    for event in events:
        team_id = _team_for_event(event, player_teams)
        if team_id in teams:
            by_team[team_id].append(event)
        else:
            ambiguous += 1
    jerseys = _jerseys(db, match, list(player_models))
    return {"match_id": match.id, "home_team_id": match.home_team_id, "away_team_id": match.away_team_id,
            "filters": filters, "metrics": _metric_dict(events),
            "teams": [{"team_id": team_id, "team_name": teams[team_id].name,
                       "side": "home" if team_id == match.home_team_id else "away",
                       "metrics": _metric_dict(by_team[team_id])}
                      for team_id in (match.home_team_id, match.away_team_id)],
            "players": [{"player_id": participant.player_id, "team_id": participant.team_id,
                         "first_name": player.first_name, "last_name": player.last_name,
                         "jersey_number": jerseys.get((player.id, participant.team_id)),
                         "metrics": _metric_dict([event for event in events if any(
                             value == player.id for value, _ in event.participants)], player.id)}
                        for participant, player in participant_rows],
            "breakdowns": _breakdowns(events, player_models, bucket_seconds),
            "unattributed": {"unknown_participant_actions": sum(any(player_id is None for player_id, _ in event.participants) for event in events),
                             "no_player_actions": sum(not event.participants for event in events),
                             "ambiguous_team_actions": ambiguous}}


def player_metrics(db: Session, match_id: UUID, player_id: UUID, filters: dict, bucket_seconds: int = 300) -> dict:
    if bucket_seconds not in (60, 300, 600, 900):
        raise DomainError("bucket_seconds must be 60, 300, 600, or 900")
    match = db.get(Match, match_id)
    if match is None:
        raise DomainError("Match not found", 404)
    filters = {**filters, "player_id": player_id, "bucket_seconds": bucket_seconds}
    _validate_filters(db, match, filters)
    all_events, participant_rows, _ = _load(db, match)
    events = _filtered(all_events, filters)
    participant, player = next((item for item in participant_rows if item[0].player_id == player_id), (None, None))
    player_models = {item.id: item for _, item in participant_rows}
    return {"match_id": match.id, "player_id": player.id, "team_id": participant.team_id,
            "player_name": f"{player.first_name} {player.last_name}", "filters": filters,
            "metrics": _metric_dict(events, player.id),
            "breakdowns": _breakdowns(events, player_models, bucket_seconds)}
