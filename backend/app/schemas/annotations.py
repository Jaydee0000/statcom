"""Aggregate request/response contracts for the Milestone 3 annotation editor."""
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models import FieldType


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ParticipantInput(StrictModel):
    player_id: UUID | None = None
    role: Annotated[str, StringConstraints(min_length=1, max_length=50)] = "player"


class FieldValueInput(StrictModel):
    field_definition_id: UUID
    value: Any


class AnnotationWrite(StrictModel):
    match_id: UUID
    video_id: UUID
    skill_definition_id: UUID
    video_start_time: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    video_end_time: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None
    match_period: Annotated[str, StringConstraints(min_length=1, max_length=50)] | None = None
    match_time: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None
    notes: str | None = None
    review_status: Literal["DRAFT", "READY_FOR_REVIEW", "REVIEWED"] = "DRAFT"
    created_by: UUID | None = None
    tag_ids: list[UUID] = Field(default_factory=list)
    participants: list[ParticipantInput] = Field(default_factory=list)
    field_values: list[FieldValueInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_collections_and_time(self):
        if self.video_end_time is not None and self.video_end_time < self.video_start_time:
            raise ValueError("video_end_time must not precede video_start_time")
        if len(self.tag_ids) != len(set(self.tag_ids)):
            raise ValueError("tag_ids must be unique")
        participant_keys = [(item.player_id, item.role.casefold()) for item in self.participants]
        if len(participant_keys) != len(set(participant_keys)):
            raise ValueError("participant player/role pairs must be unique")
        field_ids = [item.field_definition_id for item in self.field_values]
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("field values must be unique per field")
        return self


class DuplicateAnnotation(StrictModel):
    video_start_time: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    video_end_time: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None
    match_time: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None
    match_period: Annotated[str, StringConstraints(min_length=1, max_length=50)] | None = None

    @model_validator(mode="after")
    def time_order(self):
        if self.video_end_time is not None and self.video_end_time < self.video_start_time:
            raise ValueError("video_end_time must not precede video_start_time")
        return self


class TagSummary(BaseModel):
    id: UUID
    name: str
    category: str | None
    color: str | None


class ParticipantRead(BaseModel):
    id: UUID
    player_id: UUID | None
    first_name: str | None
    last_name: str | None
    role: str


class FieldValueRead(BaseModel):
    id: UUID
    field_definition_id: UUID
    value: Any


class AnnotationRead(BaseModel):
    id: UUID
    annotation_session_id: UUID
    match_id: UUID
    video_id: UUID
    skill_definition_id: UUID
    video_start_time: float
    video_end_time: float | None
    match_period: str | None
    match_time: float | None
    notes: str | None
    review_status: str
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    tags: list[TagSummary]
    participants: list[ParticipantRead]
    field_values: list[FieldValueRead]


class SkillFieldInput(StrictModel):
    key: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=100)]
    label: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    data_type: FieldType
    required: bool = False
    description: str | None = None
    options: list[Annotated[str, StringConstraints(min_length=1, max_length=100)]] | None = None
    display_order: Annotated[int, Field(ge=0)] = 0

    @model_validator(mode="after")
    def options_match_type(self):
        if self.data_type in (FieldType.SINGLE_SELECT, FieldType.MULTI_SELECT):
            if not self.options or len(self.options) != len(set(self.options)):
                raise ValueError("Select fields require nonempty, unique options")
        elif self.options is not None:
            raise ValueError("Only select fields accept options")
        return self


class SkillWrite(StrictModel):
    name: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    description: str | None = None
    category: Annotated[str, StringConstraints(min_length=1, max_length=100)] | None = None
    version: Annotated[int, Field(ge=1)] = 1
    created_by: UUID | None = None
    fields: list[SkillFieldInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_fields(self):
        keys = [field.key for field in self.fields]
        if len(keys) != len(set(keys)):
            raise ValueError("Skill field keys must be unique")
        return self


class SkillFieldRead(BaseModel):
    id: UUID
    key: str
    label: str
    data_type: FieldType
    required: bool
    description: str | None
    options: list[str] | None
    display_order: int


class SkillRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    category: str | None
    version: int
    is_active: bool
    fields: list[SkillFieldRead]


class MatchPlayerRead(BaseModel):
    participant_id: UUID
    player_id: UUID
    team_id: UUID
    first_name: str
    last_name: str
    jersey_number: int | None = None
    starter: bool
    position_played: str | None


class MatchTeamRead(BaseModel):
    id: UUID
    name: str


class MatchContextRead(BaseModel):
    match_id: UUID
    players: list[MatchPlayerRead]
    teams: list[MatchTeamRead]
