"""Stable response contracts for annotation-derived match analytics."""
from uuid import UUID

from pydantic import BaseModel


class MetricValues(BaseModel):
    total_actions: int = 0
    passes: int = 0
    completed_passes: int = 0
    incomplete_passes: int = 0
    pass_completion_pct: float | None = None
    progressive_passes: int = 0
    shots: int = 0
    shots_on_target: int = 0
    goals: int = 0
    assists: int = 0
    tackles: int = 0
    interceptions: int = 0
    turnovers: int = 0


class AppliedFilters(BaseModel):
    player_id: UUID | None = None
    skill_id: UUID | None = None
    tag_id: UUID | None = None
    outcome: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    session_id: UUID | None = None
    period: str | None = None
    bucket_seconds: int


class BreakdownItem(BaseModel):
    id: UUID | None = None
    label: str
    count: int


class TimelineBucket(BaseModel):
    start_time: float
    end_time: float
    count: int


class MetricEvent(BaseModel):
    annotation_id: UUID
    annotation_session_id: UUID
    video_id: UUID
    skill_id: UUID | None
    skill: str
    video_start_time: float
    video_end_time: float | None
    match_time: float
    period: str | None
    player_ids: list[UUID]
    tag_ids: list[UUID]
    outcomes: list[str]


class Breakdowns(BaseModel):
    actions_by_skill: list[BreakdownItem]
    actions_by_outcome: list[BreakdownItem]
    actions_by_player: list[BreakdownItem]
    actions_by_tag: list[BreakdownItem]
    timeline_buckets: list[TimelineBucket]
    events: list[MetricEvent]


class UnattributedCounts(BaseModel):
    unknown_participant_actions: int
    no_player_actions: int
    ambiguous_team_actions: int


class TeamMetrics(BaseModel):
    team_id: UUID
    team_name: str
    side: str
    metrics: MetricValues


class PlayerSummary(BaseModel):
    player_id: UUID
    team_id: UUID
    first_name: str
    last_name: str
    jersey_number: int | None = None
    metrics: MetricValues


class MatchMetricsResponse(BaseModel):
    match_id: UUID
    home_team_id: UUID
    away_team_id: UUID
    filters: AppliedFilters
    metrics: MetricValues
    teams: list[TeamMetrics]
    players: list[PlayerSummary]
    breakdowns: Breakdowns
    unattributed: UnattributedCounts


class PlayerMetricsResponse(BaseModel):
    match_id: UUID
    player_id: UUID
    team_id: UUID
    player_name: str
    filters: AppliedFilters
    metrics: MetricValues
    breakdowns: Breakdowns
