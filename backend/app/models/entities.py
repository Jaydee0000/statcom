"""Milestone 1 persistence model. Foreign-key deletes are deliberately restrictive."""
from datetime import date, datetime, time
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (BigInteger, Boolean, CheckConstraint, DateTime, Enum, ForeignKey,
                        ForeignKeyConstraint, Index, String, Text, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdentityMixin, TimestampMixin


class UserRole(StrEnum):
    ADMIN = "admin"
    COACH = "coach"
    ANNOTATOR = "annotator"
    VIEWER = "viewer"


class SessionStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    REVIEWED = "REVIEWED"


class FieldType(StrEnum):
    BOOLEAN = "boolean"
    NUMBER = "number"
    RATING = "rating"
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    TEXT = "text"
    PLAYER_REFERENCE = "player_reference"
    TEAM_REFERENCE = "team_reference"


def enum_type(kind):
    return Enum(kind, native_enum=False, create_constraint=True,
                values_callable=lambda values: [v.value for v in values])


def ref(table, **kwargs):
    return mapped_column(ForeignKey(f"{table}.id", ondelete="RESTRICT"), index=True, **kwargs)


class User(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "users"
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(320))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(enum_type(UserRole), default=UserRole.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("uq_users_email_casefold", func.lower(email), unique=True),)


class Team(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "teams"
    name: Mapped[str] = mapped_column(String(200))
    short_name: Mapped[str | None] = mapped_column(String(50))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    age_group: Mapped[str | None] = mapped_column(String(50))
    memberships: Mapped[list["PlayerTeamMembership"]] = relationship(viewonly=True)


class Player(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "players"
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[date | None]
    primary_position: Mapped[str | None] = mapped_column(String(50))
    secondary_position: Mapped[str | None] = mapped_column(String(50))
    preferred_foot: Mapped[str | None] = mapped_column(String(20))
    photo_url: Mapped[str | None] = mapped_column(Text)
    memberships: Mapped[list["PlayerTeamMembership"]] = relationship(viewonly=True)


class PlayerTeamMembership(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "player_team_memberships"
    player_id: Mapped[UUID] = ref("players")
    team_id: Mapped[UUID] = ref("teams")
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    jersey_number: Mapped[int | None]
    status: Mapped[str] = mapped_column(String(30), default="active")
    player: Mapped[Player] = relationship(viewonly=True)
    team: Mapped[Team] = relationship(viewonly=True)
    __table_args__ = (
        UniqueConstraint("player_id", "team_id", "start_date"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="date_order"),
        CheckConstraint("jersey_number IS NULL OR jersey_number >= 0", name="jersey_nonnegative"),
    )


class Season(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "seasons"
    name: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date]
    end_date: Mapped[date]
    __table_args__ = (CheckConstraint("end_date >= start_date", name="date_order"),)


class Competition(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "competitions"
    name: Mapped[str] = mapped_column(String(200))


class Match(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "matches"
    season_id: Mapped[UUID | None] = ref("seasons")
    competition_id: Mapped[UUID | None] = ref("competitions")
    home_team_id: Mapped[UUID] = ref("teams")
    away_team_id: Mapped[UUID] = ref("teams")
    match_date: Mapped[date] = mapped_column(index=True)
    start_time: Mapped[time | None]
    location: Mapped[str | None] = mapped_column(String(200))
    weather: Mapped[str | None] = mapped_column(String(200))
    home_score: Mapped[int | None]
    away_score: Mapped[int | None]
    status: Mapped[str] = mapped_column(String(30), default="scheduled")
    home_team: Mapped[Team] = relationship(foreign_keys=[home_team_id], viewonly=True)
    away_team: Mapped[Team] = relationship(foreign_keys=[away_team_id], viewonly=True)
    participants: Mapped[list["MatchParticipant"]] = relationship(viewonly=True)
    videos: Mapped[list["Video"]] = relationship(viewonly=True)
    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="different_teams"),
        CheckConstraint("home_score IS NULL OR home_score >= 0", name="home_score_nonnegative"),
        CheckConstraint("away_score IS NULL OR away_score >= 0", name="away_score_nonnegative"),
    )


class MatchParticipant(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "match_participants"
    match_id: Mapped[UUID] = ref("matches")
    player_id: Mapped[UUID] = ref("players")
    team_id: Mapped[UUID] = ref("teams")
    starter: Mapped[bool] = mapped_column(default=False)
    position_played: Mapped[str | None] = mapped_column(String(50))
    start_minute: Mapped[float | None]
    end_minute: Mapped[float | None]
    __table_args__ = (
        UniqueConstraint("match_id", "player_id"),
        CheckConstraint("start_minute IS NULL OR start_minute >= 0", name="start_nonnegative"),
        CheckConstraint("end_minute IS NULL OR (start_minute IS NOT NULL AND end_minute >= start_minute)", name="minute_order"),
    )


class Video(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "videos"
    match_id: Mapped[UUID] = ref("matches")
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str | None] = mapped_column(String(500), unique=True)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    duration_seconds: Mapped[float | None]
    upload_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    processing_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    period: Mapped[str | None] = mapped_column(String(50))
    video_time_offset: Mapped[float] = mapped_column(default=0)
    match_time_offset: Mapped[float] = mapped_column(default=0)
    uploaded_by: Mapped[UUID | None] = ref("users")
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    match: Mapped[Match] = relationship(viewonly=True)
    sessions: Mapped[list["AnnotationSession"]] = relationship(viewonly=True)
    __table_args__ = (
        UniqueConstraint("id", "match_id"),
        CheckConstraint("file_size IS NULL OR file_size >= 0", name="size_nonnegative"),
        CheckConstraint("duration_seconds IS NULL OR duration_seconds >= 0", name="duration_nonnegative"),
        CheckConstraint("video_time_offset >= 0 AND match_time_offset >= 0", name="offsets_nonnegative"),
    )


class AnnotationSession(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "annotation_sessions"
    match_id: Mapped[UUID] = ref("matches")
    video_id: Mapped[UUID] = mapped_column(index=True)
    annotator_id: Mapped[UUID | None] = ref("users")
    status: Mapped[SessionStatus] = mapped_column(enum_type(SessionStatus), default=SessionStatus.NOT_STARTED, index=True)
    progress: Mapped[float] = mapped_column(default=0)
    last_playback_position: Mapped[float] = mapped_column(default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    video: Mapped[Video] = relationship(viewonly=True)
    annotations: Mapped[list["Annotation"]] = relationship(viewonly=True)
    __table_args__ = (
        ForeignKeyConstraint(["video_id", "match_id"], ["videos.id", "videos.match_id"], ondelete="RESTRICT"),
        UniqueConstraint("id", "video_id", "match_id"),
        UniqueConstraint("video_id", "annotator_id", postgresql_nulls_not_distinct=True),
        CheckConstraint("progress >= 0 AND progress <= 100", name="progress_range"),
        CheckConstraint("last_playback_position >= 0", name="position_nonnegative"),
    )


class Tag(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "tags"
    name: Mapped[str] = mapped_column(String(200))
    normalized_name: Mapped[str] = mapped_column(String(600))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    color: Mapped[str | None] = mapped_column(String(7))
    scope: Mapped[str] = mapped_column(String(100), default="global")
    is_active: Mapped[bool] = mapped_column(default=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID | None] = ref("users")
    __table_args__ = (UniqueConstraint("scope", "normalized_name"),)


class SkillDefinition(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "skill_definitions"
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[UUID | None] = ref("users")
    fields: Mapped[list["SkillFieldDefinition"]] = relationship(viewonly=True)
    __table_args__ = (UniqueConstraint("name", "version"), CheckConstraint("version >= 1", name="version_positive"))


class SkillFieldDefinition(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "skill_field_definitions"
    skill_definition_id: Mapped[UUID] = ref("skill_definitions")
    key: Mapped[str] = mapped_column(String(100))
    label: Mapped[str] = mapped_column(String(200))
    data_type: Mapped[FieldType] = mapped_column(enum_type(FieldType))
    required: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str | None] = mapped_column(Text)
    options: Mapped[list[str] | None] = mapped_column(JSONB)
    display_order: Mapped[int] = mapped_column(default=0)
    __table_args__ = (UniqueConstraint("skill_definition_id", "key"),)


class Annotation(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "annotations"
    annotation_session_id: Mapped[UUID] = mapped_column(index=True)
    match_id: Mapped[UUID] = ref("matches")
    video_id: Mapped[UUID] = mapped_column(index=True)
    skill_definition_id: Mapped[UUID | None] = ref("skill_definitions")
    video_start_time: Mapped[float]
    video_end_time: Mapped[float | None]
    match_period: Mapped[str | None] = mapped_column(String(50))
    match_time: Mapped[float | None]
    notes: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(30), default="DRAFT")
    created_by: Mapped[UUID | None] = ref("users")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    session: Mapped[AnnotationSession] = relationship(viewonly=True)
    participants: Mapped[list["AnnotationParticipant"]] = relationship(viewonly=True)
    tags: Mapped[list[Tag]] = relationship(secondary="annotation_tags", viewonly=True)
    field_values: Mapped[list["AnnotationFieldValue"]] = relationship(viewonly=True)
    __table_args__ = (
        ForeignKeyConstraint(["annotation_session_id", "video_id", "match_id"],
                             ["annotation_sessions.id", "annotation_sessions.video_id", "annotation_sessions.match_id"], ondelete="RESTRICT"),
        CheckConstraint("video_start_time >= 0", name="start_nonnegative"),
        CheckConstraint("video_end_time IS NULL OR video_end_time >= video_start_time", name="time_order"),
        CheckConstraint("match_time IS NULL OR match_time >= 0", name="match_time_nonnegative"),
    )


class AnnotationParticipant(IdentityMixin, Base):
    __tablename__ = "annotation_participants"
    annotation_id: Mapped[UUID] = ref("annotations")
    player_id: Mapped[UUID | None] = ref("players")
    role: Mapped[str] = mapped_column(String(50), default="player")
    __table_args__ = (UniqueConstraint("annotation_id", "player_id", "role"),)


class AnnotationTag(IdentityMixin, Base):
    __tablename__ = "annotation_tags"
    annotation_id: Mapped[UUID] = ref("annotations")
    tag_id: Mapped[UUID] = ref("tags")
    __table_args__ = (UniqueConstraint("annotation_id", "tag_id"),)


class AnnotationFieldValue(IdentityMixin, TimestampMixin, Base):
    __tablename__ = "annotation_field_values"
    annotation_id: Mapped[UUID] = ref("annotations")
    field_definition_id: Mapped[UUID] = ref("skill_field_definitions")
    value: Mapped[Any] = mapped_column(JSONB(none_as_null=True), nullable=False)
    # Reference-valued fields also carry real FKs so deletes cannot orphan them.
    player_value_id: Mapped[UUID | None] = ref("players")
    team_value_id: Mapped[UUID | None] = ref("teams")
    __table_args__ = (
        UniqueConstraint("annotation_id", "field_definition_id"),
        CheckConstraint("player_value_id IS NULL OR team_value_id IS NULL", name="one_reference_kind"),
        CheckConstraint("player_value_id IS NULL OR value = to_jsonb(player_value_id::text)", name="player_value_matches"),
        CheckConstraint("team_value_id IS NULL OR value = to_jsonb(team_value_id::text)", name="team_value_matches"),
    )
