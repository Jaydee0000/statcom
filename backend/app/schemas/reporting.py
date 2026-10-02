"""Milestone 5 contracts for frontend-ready player, match, and team analytics."""
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class MetricDefinitionRead(BaseModel):
    key: str
    label: str
    format: Literal["count", "percent", "minutes", "rate"]
    aggregation: Literal["sum", "ratio"]
    numerator_key: str | None = None
    denominator_key: str | None = None
    traceable: bool = False
    supports_per_90: bool = False
    custom: bool = False


class MetricValueRead(BaseModel):
    key: str
    value: float | None = None
    numerator: float | None = None
    denominator: float | None = None
    annotation_count: int = 0


class CoverageRead(BaseModel):
    status: Literal["NOT_STARTED", "IN_PROGRESS", "READY_FOR_REVIEW", "REVIEWED"]
    complete: bool
    session_count: int
    reviewed_sessions: int


class PlayerIdentityRead(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    primary_position: str | None = None
    secondary_position: str | None = None
    preferred_foot: str | None = None
    photo_url: str | None = None
    team_id: UUID | None = None
    team_name: str | None = None
    jersey_number: int | None = None
    availability: str | None = None


class RosterPlayerRead(PlayerIdentityRead):
    appearances: int
    minutes: float | None = None
    recent_form: list[str]
    metrics: list[MetricValueRead]
    incomplete_matches: int


class RosterResponse(BaseModel):
    metric_definitions: list[MetricDefinitionRead]
    players: list[RosterPlayerRead]


class MatchReferenceRead(BaseModel):
    id: UUID
    match_date: date
    home_team_id: UUID
    home_team: str
    away_team_id: UUID
    away_team: str
    home_score: int | None = None
    away_score: int | None = None
    result: str | None = None
    opponent: str | None = None
    season_id: UUID | None = None
    season: str | None = None
    competition_id: UUID | None = None
    competition: str | None = None
    location: str | None = None
    status: str
    coverage: CoverageRead


class PlayerHistoryRowRead(BaseModel):
    match: MatchReferenceRead
    team_id: UUID
    starter: bool
    position: str | None = None
    minutes: float | None = None
    metrics: list[MetricValueRead]


class PlayerHistoryResponse(BaseModel):
    player: PlayerIdentityRead
    metric_definitions: list[MetricDefinitionRead]
    matches: list[PlayerHistoryRowRead]


class PlayerSummaryResponse(BaseModel):
    player: PlayerIdentityRead
    appearances: int
    minutes: float | None = None
    metrics: list[MetricValueRead]
    coverage: CoverageRead


class ResultGroupRead(BaseModel):
    result: Literal["W", "D", "L"]
    match_count: int
    complete_match_count: int
    metrics: list[MetricValueRead]


class ResultComparisonResponse(BaseModel):
    player_id: UUID
    metric_definitions: list[MetricDefinitionRead]
    groups: list[ResultGroupRead]


class SourceAnnotationRead(BaseModel):
    annotation_id: UUID
    annotation_session_id: UUID
    video_id: UUID
    match_id: UUID
    match_date: date
    opponent: str | None = None
    player_id: UUID | None = None
    player_name: str | None = None
    skill: str
    tags: list[str]
    outcomes: list[str]
    match_time: float
    video_start_time: float
    video_end_time: float | None = None
    period: str | None = None


class MetricSourcesResponse(BaseModel):
    metric: MetricDefinitionRead
    value: MetricValueRead
    sources: list[SourceAnnotationRead]


class VideoSummaryRead(BaseModel):
    id: UUID
    original_filename: str
    period: str | None = None
    duration_seconds: float | None = None
    session_id: UUID | None = None
    annotation_status: str


class MatchListResponse(BaseModel):
    matches: list[MatchReferenceRead]


class MatchPlayerStatsRead(BaseModel):
    player: PlayerIdentityRead
    team_id: UUID
    starter: bool
    position: str | None = None
    minutes: float | None = None
    metrics: list[MetricValueRead]


class MatchStatsResponse(BaseModel):
    match: MatchReferenceRead
    videos: list[VideoSummaryRead]
    metric_definitions: list[MetricDefinitionRead]
    participants: list[MatchPlayerStatsRead]


class TeamTotalRead(BaseModel):
    team_id: UUID
    metrics: list[MetricValueRead]


class TeamStatSheetResponse(BaseModel):
    metric_definitions: list[MetricDefinitionRead]
    players: list[RosterPlayerRead]
    totals: TeamTotalRead
    match_count: int
    incomplete_matches: int
