from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.metrics import MatchMetricsResponse, PlayerMetricsResponse
from app.services.metrics import match_metrics, player_metrics

router = APIRouter(tags=["match-analytics"])
DB = Annotated[Session, Depends(get_db)]


def filters(player_id=None, skill_id=None, tag_id=None, outcome=None, start_time=None,
            end_time=None, session_id=None, period=None):
    return {"player_id": player_id, "skill_id": skill_id, "tag_id": tag_id,
            "outcome": outcome, "start_time": start_time, "end_time": end_time,
            "session_id": session_id, "period": period}


@router.get("/matches/{match_id}/metrics", response_model=MatchMetricsResponse)
def match_analytics(match_id: UUID, db: DB, player_id: UUID | None = None, skill_id: UUID | None = None,
                    tag_id: UUID | None = None, outcome: str | None = None,
                    start_time: Annotated[float | None, Query(ge=0)] = None,
                    end_time: Annotated[float | None, Query(gt=0)] = None,
                    session_id: UUID | None = None, period: str | None = None,
                    bucket_seconds: Annotated[int, Query(ge=60, le=900)] = 300):
    return match_metrics(db, match_id, filters(player_id, skill_id, tag_id, outcome, start_time,
                                               end_time, session_id, period), bucket_seconds)


@router.get("/matches/{match_id}/players/{player_id}/metrics", response_model=PlayerMetricsResponse)
def player_analytics(match_id: UUID, player_id: UUID, db: DB, skill_id: UUID | None = None,
                     tag_id: UUID | None = None, outcome: str | None = None,
                     start_time: Annotated[float | None, Query(ge=0)] = None,
                     end_time: Annotated[float | None, Query(gt=0)] = None,
                     session_id: UUID | None = None, period: str | None = None,
                     bucket_seconds: Annotated[int, Query(ge=60, le=900)] = 300):
    return player_metrics(db, match_id, player_id,
                          filters(None, skill_id, tag_id, outcome, start_time, end_time, session_id, period),
                          bucket_seconds)
