"""Frontend-oriented Milestone 5 analytics endpoints."""
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reporting import (MatchListResponse, MatchStatsResponse,
    MetricDefinitionRead, MetricSourcesResponse, PlayerHistoryResponse,
    PlayerSummaryResponse, ResultComparisonResponse, RosterResponse,
    TeamStatSheetResponse)
from app.services import reporting

router = APIRouter(tags=["reporting"])
DB = Annotated[Session, Depends(get_db)]


def _metrics(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    return [item.strip() for value in values for item in value.split(",") if item.strip()]


@router.get("/metric-definitions", response_model=list[MetricDefinitionRead])
def definitions(db: DB):
    return reporting.metric_catalog(db)


@router.get("/players/summary", response_model=RosterResponse)
def roster_summary(db: DB, team_id: UUID | None = None, season_id: UUID | None = None,
                   position: str | None = None, metrics: Annotated[list[str] | None, Query()] = None):
    return reporting.roster(db, team_id=team_id, season_id=season_id, position=position,
                            metrics=_metrics(metrics))


@router.get("/players/{player_id}/summary", response_model=PlayerSummaryResponse)
def player_summary(player_id: UUID, db: DB, season_id: UUID | None = None,
                   competition_id: UUID | None = None,
                   metrics: Annotated[list[str] | None, Query()] = None):
    return reporting.player_summary(db, player_id, season_id=season_id,
        competition_id=competition_id, metrics=_metrics(metrics))


@router.get("/players/{player_id}/metrics/history", response_model=PlayerHistoryResponse)
def player_history(player_id: UUID, db: DB, season_id: UUID | None = None,
                   competition_id: UUID | None = None,
                   metrics: Annotated[list[str] | None, Query()] = None):
    return reporting.player_history(db, player_id, season_id=season_id,
        competition_id=competition_id, metrics=_metrics(metrics))


@router.get("/players/{player_id}/metrics/by-result", response_model=ResultComparisonResponse)
def player_by_result(player_id: UUID, db: DB, season_id: UUID | None = None,
                     competition_id: UUID | None = None,
                     metrics: Annotated[list[str] | None, Query()] = None):
    return reporting.result_comparison(db, player_id, season_id=season_id,
        competition_id=competition_id, metrics=_metrics(metrics))


@router.get("/players/{player_id}/metrics/sources", response_model=MetricSourcesResponse)
def player_sources(player_id: UUID, metric: str, db: DB, season_id: UUID | None = None,
                   competition_id: UUID | None = None, match_id: UUID | None = None):
    return reporting.metric_sources(db, player_id, metric, season_id=season_id,
                                    competition_id=competition_id, match_id=match_id)


@router.get("/matches/overview", response_model=MatchListResponse)
def matches_overview(db: DB, team_id: UUID | None = None, season_id: UUID | None = None,
                     competition_id: UUID | None = None):
    return reporting.list_matches(db, team_id=team_id, season_id=season_id,
                                  competition_id=competition_id)


@router.get("/matches/{match_id}/stats", response_model=MatchStatsResponse)
def match_statistics(match_id: UUID, db: DB,
                     metrics: Annotated[list[str] | None, Query()] = None):
    return reporting.match_stats(db, match_id, metrics=_metrics(metrics))


@router.get("/team-stats", response_model=TeamStatSheetResponse)
def team_statistics(team_id: UUID, db: DB, season_id: UUID | None = None,
                    competition_id: UUID | None = None, match_id: UUID | None = None,
                    date_from: date | None = None, date_to: date | None = None,
                    position: str | None = None,
                    metrics: Annotated[list[str] | None, Query()] = None):
    return reporting.team_stat_sheet(db, team_id, season_id=season_id,
        competition_id=competition_id, match_id=match_id, date_from=date_from,
        date_to=date_to, position=position, metrics=_metrics(metrics))
