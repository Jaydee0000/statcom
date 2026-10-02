from datetime import date, time
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import (AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl,
                      StringConstraints, field_validator, model_validator)

from app.models import FieldType, SessionStatus

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Position = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Nonnegative = Annotated[float, Field(ge=0)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True, allow_inf_nan=False, str_strip_whitespace=True)


class TeamCreate(Input):
    name: Name
    short_name: Annotated[str, Field(max_length=50)] | None = None
    city: Short | None = None
    state: Short | None = None
    age_group: Position | None = None


class PlayerCreate(Input):
    first_name: Short
    last_name: Short
    date_of_birth: date | None = None
    primary_position: Position | None = None
    secondary_position: Position | None = None
    preferred_foot: Literal["left", "right", "both"] | None = None
    photo_url: str | None = None

    @field_validator("photo_url")
    @classmethod
    def valid_url(cls, value):
        if value is not None:
            HttpUrl(value)
        return value

    @field_validator("date_of_birth")
    @classmethod
    def not_in_future(cls, value):
        if value and value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value


class MembershipCreate(Input):
    player_id: UUID
    team_id: UUID
    start_date: date
    end_date: date | None = None
    jersey_number: Annotated[int, Field(ge=0)] | None = None
    status: Literal["active", "inactive", "loan"] = "active"

    @model_validator(mode="after")
    def date_order(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class SeasonCreate(Input):
    name: Name
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def date_order(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class CompetitionCreate(Input):
    name: Name


class MatchCreate(Input):
    season_id: UUID | None = None
    competition_id: UUID | None = None
    home_team_id: UUID
    away_team_id: UUID
    match_date: date
    start_time: time | None = None
    location: Name | None = None
    weather: Name | None = None
    home_score: Annotated[int, Field(ge=0)] | None = None
    away_score: Annotated[int, Field(ge=0)] | None = None
    status: Literal["scheduled", "in_progress", "completed", "cancelled", "postponed"] = "scheduled"

    @model_validator(mode="after")
    def different_teams(self):
        if self.home_team_id == self.away_team_id:
            raise ValueError("Home and away teams must differ")
        return self


class MatchParticipantCreate(Input):
    match_id: UUID
    player_id: UUID
    team_id: UUID
    starter: bool = False
    position_played: Position | None = None
    start_minute: Nonnegative | None = None
    end_minute: Nonnegative | None = None

    @model_validator(mode="after")
    def minute_order(self):
        if self.end_minute is not None and (self.start_minute is None or self.end_minute < self.start_minute):
            raise ValueError("end_minute requires start_minute and must not precede it")
        return self


class VideoCreate(Input):
    match_id: UUID
    original_filename: Annotated[str, Field(min_length=1, max_length=255)]
    storage_key: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    mime_type: Short | None = None
    file_size: Annotated[int, Field(ge=0)] | None = None
    duration_seconds: Nonnegative | None = None
    upload_status: Literal["PENDING", "UPLOADING", "UPLOADED", "FAILED"] = "PENDING"
    processing_status: Literal["PENDING", "PROCESSING", "READY", "FAILED"] = "PENDING"
    period: Position | None = None
    video_time_offset: Nonnegative = 0
    match_time_offset: Nonnegative = 0
    uploaded_by: UUID | None = None
    uploaded_at: AwareDatetime | None = None


class SessionCreate(Input):
    match_id: UUID
    video_id: UUID
    annotator_id: UUID | None = None
    status: SessionStatus = SessionStatus.NOT_STARTED
    progress: Annotated[float, Field(ge=0, le=100)] = 0
    last_playback_position: Nonnegative = 0
    completed_at: AwareDatetime | None = None


class TagCreate(Input):
    name: Name
    description: str | None = None
    category: Short | None = None
    color: Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")] | None = None
    scope: Short = "global"
    is_active: bool = True
    created_by: UUID | None = None


class SkillCreate(Input):
    name: Name
    description: str | None = None
    category: Short | None = None
    version: Annotated[int, Field(ge=1)] = 1
    is_active: bool = True
    created_by: UUID | None = None


class SkillFieldCreate(Input):
    skill_definition_id: UUID
    key: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=100)]
    label: Name
    data_type: FieldType
    required: bool = False
    description: str | None = None
    options: list[Short] | None = None
    display_order: Annotated[int, Field(ge=0)] = 0

    @model_validator(mode="after")
    def options_match_type(self):
        if self.data_type in (FieldType.SINGLE_SELECT, FieldType.MULTI_SELECT):
            if not self.options or len(set(self.options)) != len(self.options):
                raise ValueError("Select fields require nonempty, unique options")
        elif self.options is not None:
            raise ValueError("Only select fields accept options")
        return self


class AnnotationCreate(Input):
    annotation_session_id: UUID
    match_id: UUID
    video_id: UUID
    skill_definition_id: UUID | None = None
    video_start_time: Nonnegative
    video_end_time: Nonnegative | None = None
    match_period: Position | None = None
    match_time: Nonnegative | None = None
    notes: str | None = None
    review_status: Literal["DRAFT", "READY_FOR_REVIEW", "REVIEWED"] = "DRAFT"
    created_by: UUID | None = None

    @model_validator(mode="after")
    def time_order(self):
        if self.video_end_time is not None and self.video_end_time < self.video_start_time:
            raise ValueError("video_end_time must not precede video_start_time")
        return self


class AnnotationParticipantCreate(Input):
    annotation_id: UUID
    player_id: UUID | None = None
    role: Position = "player"


class AnnotationTagCreate(Input):
    annotation_id: UUID
    tag_id: UUID


class FieldValueCreate(Input):
    annotation_id: UUID
    field_definition_id: UUID
    value: Any
