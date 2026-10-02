"""Milestone 1 core foundation

Revision ID: 0001
Revises:
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('competitions',
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_competitions'))
    )
    op.create_table('players',
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('date_of_birth', sa.Date(), nullable=True),
    sa.Column('primary_position', sa.String(length=50), nullable=True),
    sa.Column('secondary_position', sa.String(length=50), nullable=True),
    sa.Column('preferred_foot', sa.String(length=20), nullable=True),
    sa.Column('photo_url', sa.Text(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_players'))
    )
    op.create_table('seasons',
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('end_date >= start_date', name=op.f('ck_seasons_date_order')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_seasons'))
    )
    op.create_table('teams',
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('short_name', sa.String(length=50), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('state', sa.String(length=100), nullable=True),
    sa.Column('age_group', sa.String(length=50), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_teams'))
    )
    op.create_table('users',
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('password_hash', sa.Text(), nullable=False),
    sa.Column('role', sa.Enum('admin', 'coach', 'annotator', 'viewer', name='userrole', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index('uq_users_email_casefold', 'users', [sa.literal_column('lower(email)')], unique=True)
    op.create_table('matches',
    sa.Column('season_id', sa.Uuid(), nullable=True),
    sa.Column('competition_id', sa.Uuid(), nullable=True),
    sa.Column('home_team_id', sa.Uuid(), nullable=False),
    sa.Column('away_team_id', sa.Uuid(), nullable=False),
    sa.Column('match_date', sa.Date(), nullable=False),
    sa.Column('start_time', sa.Time(), nullable=True),
    sa.Column('location', sa.String(length=200), nullable=True),
    sa.Column('weather', sa.String(length=200), nullable=True),
    sa.Column('home_score', sa.Integer(), nullable=True),
    sa.Column('away_score', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('away_score IS NULL OR away_score >= 0', name=op.f('ck_matches_away_score_nonnegative')),
    sa.CheckConstraint('home_score IS NULL OR home_score >= 0', name=op.f('ck_matches_home_score_nonnegative')),
    sa.CheckConstraint('home_team_id <> away_team_id', name=op.f('ck_matches_different_teams')),
    sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], name=op.f('fk_matches_away_team_id_teams'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['competition_id'], ['competitions.id'], name=op.f('fk_matches_competition_id_competitions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], name=op.f('fk_matches_home_team_id_teams'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], name=op.f('fk_matches_season_id_seasons'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_matches'))
    )
    op.create_index(op.f('ix_matches_away_team_id'), 'matches', ['away_team_id'], unique=False)
    op.create_index(op.f('ix_matches_competition_id'), 'matches', ['competition_id'], unique=False)
    op.create_index(op.f('ix_matches_home_team_id'), 'matches', ['home_team_id'], unique=False)
    op.create_index(op.f('ix_matches_match_date'), 'matches', ['match_date'], unique=False)
    op.create_index(op.f('ix_matches_season_id'), 'matches', ['season_id'], unique=False)
    op.create_table('player_team_memberships',
    sa.Column('player_id', sa.Uuid(), nullable=False),
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('jersey_number', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('end_date IS NULL OR end_date >= start_date', name=op.f('ck_player_team_memberships_date_order')),
    sa.CheckConstraint('jersey_number IS NULL OR jersey_number >= 0', name=op.f('ck_player_team_memberships_jersey_nonnegative')),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], name=op.f('fk_player_team_memberships_player_id_players'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_player_team_memberships_team_id_teams'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_player_team_memberships')),
    sa.UniqueConstraint('player_id', 'team_id', 'start_date', name=op.f('uq_player_team_memberships_player_id'))
    )
    op.create_index(op.f('ix_player_team_memberships_player_id'), 'player_team_memberships', ['player_id'], unique=False)
    op.create_index(op.f('ix_player_team_memberships_team_id'), 'player_team_memberships', ['team_id'], unique=False)
    op.create_table('skill_definitions',
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('version >= 1', name=op.f('ck_skill_definitions_version_positive')),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_skill_definitions_created_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skill_definitions')),
    sa.UniqueConstraint('name', 'version', name=op.f('uq_skill_definitions_name'))
    )
    op.create_index(op.f('ix_skill_definitions_created_by'), 'skill_definitions', ['created_by'], unique=False)
    op.create_table('tags',
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('normalized_name', sa.String(length=600), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('color', sa.String(length=7), nullable=True),
    sa.Column('scope', sa.String(length=100), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_tags_created_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tags')),
    sa.UniqueConstraint('scope', 'normalized_name', name=op.f('uq_tags_scope'))
    )
    op.create_index(op.f('ix_tags_created_by'), 'tags', ['created_by'], unique=False)
    op.create_table('match_participants',
    sa.Column('match_id', sa.Uuid(), nullable=False),
    sa.Column('player_id', sa.Uuid(), nullable=False),
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.Column('starter', sa.Boolean(), nullable=False),
    sa.Column('position_played', sa.String(length=50), nullable=True),
    sa.Column('start_minute', sa.Float(), nullable=True),
    sa.Column('end_minute', sa.Float(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('end_minute IS NULL OR (start_minute IS NOT NULL AND end_minute >= start_minute)', name=op.f('ck_match_participants_minute_order')),
    sa.CheckConstraint('start_minute IS NULL OR start_minute >= 0', name=op.f('ck_match_participants_start_nonnegative')),
    sa.ForeignKeyConstraint(['match_id'], ['matches.id'], name=op.f('fk_match_participants_match_id_matches'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], name=op.f('fk_match_participants_player_id_players'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_match_participants_team_id_teams'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_match_participants')),
    sa.UniqueConstraint('match_id', 'player_id', name=op.f('uq_match_participants_match_id'))
    )
    op.create_index(op.f('ix_match_participants_match_id'), 'match_participants', ['match_id'], unique=False)
    op.create_index(op.f('ix_match_participants_player_id'), 'match_participants', ['player_id'], unique=False)
    op.create_index(op.f('ix_match_participants_team_id'), 'match_participants', ['team_id'], unique=False)
    op.create_table('skill_field_definitions',
    sa.Column('skill_definition_id', sa.Uuid(), nullable=False),
    sa.Column('key', sa.String(length=100), nullable=False),
    sa.Column('label', sa.String(length=200), nullable=False),
    sa.Column('data_type', sa.Enum('boolean', 'number', 'rating', 'single_select', 'multi_select', 'text', 'player_reference', 'team_reference', name='fieldtype', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('required', sa.Boolean(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['skill_definition_id'], ['skill_definitions.id'], name=op.f('fk_skill_field_definitions_skill_definition_id_skill_definitions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skill_field_definitions')),
    sa.UniqueConstraint('skill_definition_id', 'key', name=op.f('uq_skill_field_definitions_skill_definition_id'))
    )
    op.create_index(op.f('ix_skill_field_definitions_skill_definition_id'), 'skill_field_definitions', ['skill_definition_id'], unique=False)
    op.create_table('videos',
    sa.Column('match_id', sa.Uuid(), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('storage_key', sa.String(length=500), nullable=True),
    sa.Column('mime_type', sa.String(length=100), nullable=True),
    sa.Column('file_size', sa.BigInteger(), nullable=True),
    sa.Column('duration_seconds', sa.Float(), nullable=True),
    sa.Column('upload_status', sa.String(length=30), nullable=False),
    sa.Column('processing_status', sa.String(length=30), nullable=False),
    sa.Column('period', sa.String(length=50), nullable=True),
    sa.Column('video_time_offset', sa.Float(), nullable=False),
    sa.Column('match_time_offset', sa.Float(), nullable=False),
    sa.Column('uploaded_by', sa.Uuid(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('duration_seconds IS NULL OR duration_seconds >= 0', name=op.f('ck_videos_duration_nonnegative')),
    sa.CheckConstraint('file_size IS NULL OR file_size >= 0', name=op.f('ck_videos_size_nonnegative')),
    sa.CheckConstraint('video_time_offset >= 0 AND match_time_offset >= 0', name=op.f('ck_videos_offsets_nonnegative')),
    sa.ForeignKeyConstraint(['match_id'], ['matches.id'], name=op.f('fk_videos_match_id_matches'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], name=op.f('fk_videos_uploaded_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_videos')),
    sa.UniqueConstraint('id', 'match_id', name=op.f('uq_videos_id')),
    sa.UniqueConstraint('storage_key', name=op.f('uq_videos_storage_key'))
    )
    op.create_index(op.f('ix_videos_match_id'), 'videos', ['match_id'], unique=False)
    op.create_index(op.f('ix_videos_uploaded_by'), 'videos', ['uploaded_by'], unique=False)
    op.create_table('annotation_sessions',
    sa.Column('match_id', sa.Uuid(), nullable=False),
    sa.Column('video_id', sa.Uuid(), nullable=False),
    sa.Column('annotator_id', sa.Uuid(), nullable=True),
    sa.Column('status', sa.Enum('NOT_STARTED', 'IN_PROGRESS', 'READY_FOR_REVIEW', 'REVIEWED', name='sessionstatus', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('progress', sa.Float(), nullable=False),
    sa.Column('last_playback_position', sa.Float(), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('last_playback_position >= 0', name=op.f('ck_annotation_sessions_position_nonnegative')),
    sa.CheckConstraint('progress >= 0 AND progress <= 100', name=op.f('ck_annotation_sessions_progress_range')),
    sa.ForeignKeyConstraint(['annotator_id'], ['users.id'], name=op.f('fk_annotation_sessions_annotator_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['match_id'], ['matches.id'], name=op.f('fk_annotation_sessions_match_id_matches'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['video_id', 'match_id'], ['videos.id', 'videos.match_id'], name=op.f('fk_annotation_sessions_video_id_videos'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_annotation_sessions')),
    sa.UniqueConstraint('id', 'video_id', 'match_id', name=op.f('uq_annotation_sessions_id')),
    sa.UniqueConstraint('video_id', 'annotator_id', name=op.f('uq_annotation_sessions_video_id'), postgresql_nulls_not_distinct=True)
    )
    op.create_index(op.f('ix_annotation_sessions_annotator_id'), 'annotation_sessions', ['annotator_id'], unique=False)
    op.create_index(op.f('ix_annotation_sessions_match_id'), 'annotation_sessions', ['match_id'], unique=False)
    op.create_index(op.f('ix_annotation_sessions_status'), 'annotation_sessions', ['status'], unique=False)
    op.create_index(op.f('ix_annotation_sessions_video_id'), 'annotation_sessions', ['video_id'], unique=False)
    op.create_table('annotations',
    sa.Column('annotation_session_id', sa.Uuid(), nullable=False),
    sa.Column('match_id', sa.Uuid(), nullable=False),
    sa.Column('video_id', sa.Uuid(), nullable=False),
    sa.Column('skill_definition_id', sa.Uuid(), nullable=True),
    sa.Column('video_start_time', sa.Float(), nullable=False),
    sa.Column('video_end_time', sa.Float(), nullable=True),
    sa.Column('match_period', sa.String(length=50), nullable=True),
    sa.Column('match_time', sa.Float(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('review_status', sa.String(length=30), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('match_time IS NULL OR match_time >= 0', name=op.f('ck_annotations_match_time_nonnegative')),
    sa.CheckConstraint('video_end_time IS NULL OR video_end_time >= video_start_time', name=op.f('ck_annotations_time_order')),
    sa.CheckConstraint('video_start_time >= 0', name=op.f('ck_annotations_start_nonnegative')),
    sa.ForeignKeyConstraint(['annotation_session_id', 'video_id', 'match_id'], ['annotation_sessions.id', 'annotation_sessions.video_id', 'annotation_sessions.match_id'], name=op.f('fk_annotations_annotation_session_id_annotation_sessions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_annotations_created_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['match_id'], ['matches.id'], name=op.f('fk_annotations_match_id_matches'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['skill_definition_id'], ['skill_definitions.id'], name=op.f('fk_annotations_skill_definition_id_skill_definitions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_annotations'))
    )
    op.create_index(op.f('ix_annotations_annotation_session_id'), 'annotations', ['annotation_session_id'], unique=False)
    op.create_index(op.f('ix_annotations_created_by'), 'annotations', ['created_by'], unique=False)
    op.create_index(op.f('ix_annotations_deleted_at'), 'annotations', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_annotations_match_id'), 'annotations', ['match_id'], unique=False)
    op.create_index(op.f('ix_annotations_skill_definition_id'), 'annotations', ['skill_definition_id'], unique=False)
    op.create_index(op.f('ix_annotations_video_id'), 'annotations', ['video_id'], unique=False)
    op.create_table('annotation_field_values',
    sa.Column('annotation_id', sa.Uuid(), nullable=False),
    sa.Column('field_definition_id', sa.Uuid(), nullable=False),
    sa.Column('value', postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=False),
    sa.Column('player_value_id', sa.Uuid(), nullable=True),
    sa.Column('team_value_id', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['annotation_id'], ['annotations.id'], name=op.f('fk_annotation_field_values_annotation_id_annotations'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['field_definition_id'], ['skill_field_definitions.id'], name=op.f('fk_annotation_field_values_field_definition_id_skill_field_definitions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['player_value_id'], ['players.id'], name=op.f('fk_annotation_field_values_player_value_id_players'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['team_value_id'], ['teams.id'], name=op.f('fk_annotation_field_values_team_value_id_teams'), ondelete='RESTRICT'),
    sa.CheckConstraint('player_value_id IS NULL OR team_value_id IS NULL', name=op.f('ck_annotation_field_values_one_reference_kind')),
    sa.CheckConstraint('player_value_id IS NULL OR value = to_jsonb(player_value_id::text)', name=op.f('ck_annotation_field_values_player_value_matches')),
    sa.CheckConstraint('team_value_id IS NULL OR value = to_jsonb(team_value_id::text)', name=op.f('ck_annotation_field_values_team_value_matches')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_annotation_field_values')),
    sa.UniqueConstraint('annotation_id', 'field_definition_id', name=op.f('uq_annotation_field_values_annotation_id'))
    )
    op.create_index(op.f('ix_annotation_field_values_annotation_id'), 'annotation_field_values', ['annotation_id'], unique=False)
    op.create_index(op.f('ix_annotation_field_values_field_definition_id'), 'annotation_field_values', ['field_definition_id'], unique=False)
    op.create_index(op.f('ix_annotation_field_values_player_value_id'), 'annotation_field_values', ['player_value_id'], unique=False)
    op.create_index(op.f('ix_annotation_field_values_team_value_id'), 'annotation_field_values', ['team_value_id'], unique=False)
    op.create_table('annotation_participants',
    sa.Column('annotation_id', sa.Uuid(), nullable=False),
    sa.Column('player_id', sa.Uuid(), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['annotation_id'], ['annotations.id'], name=op.f('fk_annotation_participants_annotation_id_annotations'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], name=op.f('fk_annotation_participants_player_id_players'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_annotation_participants')),
    sa.UniqueConstraint('annotation_id', 'player_id', 'role', name=op.f('uq_annotation_participants_annotation_id'))
    )
    op.create_index(op.f('ix_annotation_participants_annotation_id'), 'annotation_participants', ['annotation_id'], unique=False)
    op.create_index(op.f('ix_annotation_participants_player_id'), 'annotation_participants', ['player_id'], unique=False)
    op.create_table('annotation_tags',
    sa.Column('annotation_id', sa.Uuid(), nullable=False),
    sa.Column('tag_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['annotation_id'], ['annotations.id'], name=op.f('fk_annotation_tags_annotation_id_annotations'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name=op.f('fk_annotation_tags_tag_id_tags'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_annotation_tags')),
    sa.UniqueConstraint('annotation_id', 'tag_id', name=op.f('uq_annotation_tags_annotation_id'))
    )
    op.create_index(op.f('ix_annotation_tags_annotation_id'), 'annotation_tags', ['annotation_id'], unique=False)
    op.create_index(op.f('ix_annotation_tags_tag_id'), 'annotation_tags', ['tag_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_annotation_tags_tag_id'), table_name='annotation_tags')
    op.drop_index(op.f('ix_annotation_tags_annotation_id'), table_name='annotation_tags')
    op.drop_table('annotation_tags')
    op.drop_index(op.f('ix_annotation_participants_player_id'), table_name='annotation_participants')
    op.drop_index(op.f('ix_annotation_participants_annotation_id'), table_name='annotation_participants')
    op.drop_table('annotation_participants')
    op.drop_index(op.f('ix_annotation_field_values_field_definition_id'), table_name='annotation_field_values')
    op.drop_index(op.f('ix_annotation_field_values_player_value_id'), table_name='annotation_field_values', if_exists=True)
    op.drop_index(op.f('ix_annotation_field_values_team_value_id'), table_name='annotation_field_values', if_exists=True)
    op.drop_index(op.f('ix_annotation_field_values_annotation_id'), table_name='annotation_field_values')
    op.drop_table('annotation_field_values')
    op.drop_index(op.f('ix_annotations_video_id'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_skill_definition_id'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_match_id'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_deleted_at'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_created_by'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_annotation_session_id'), table_name='annotations')
    op.drop_table('annotations')
    op.drop_index(op.f('ix_annotation_sessions_video_id'), table_name='annotation_sessions')
    op.drop_index(op.f('ix_annotation_sessions_status'), table_name='annotation_sessions')
    op.drop_index(op.f('ix_annotation_sessions_match_id'), table_name='annotation_sessions')
    op.drop_index(op.f('ix_annotation_sessions_annotator_id'), table_name='annotation_sessions')
    op.drop_table('annotation_sessions')
    op.drop_index(op.f('ix_videos_uploaded_by'), table_name='videos')
    op.drop_index(op.f('ix_videos_match_id'), table_name='videos')
    op.drop_table('videos')
    op.drop_index(op.f('ix_skill_field_definitions_skill_definition_id'), table_name='skill_field_definitions')
    op.drop_table('skill_field_definitions')
    op.drop_index(op.f('ix_match_participants_team_id'), table_name='match_participants')
    op.drop_index(op.f('ix_match_participants_player_id'), table_name='match_participants')
    op.drop_index(op.f('ix_match_participants_match_id'), table_name='match_participants')
    op.drop_table('match_participants')
    op.drop_index(op.f('ix_tags_created_by'), table_name='tags')
    op.drop_table('tags')
    op.drop_index(op.f('ix_skill_definitions_created_by'), table_name='skill_definitions')
    op.drop_table('skill_definitions')
    op.drop_index(op.f('ix_player_team_memberships_team_id'), table_name='player_team_memberships')
    op.drop_index(op.f('ix_player_team_memberships_player_id'), table_name='player_team_memberships')
    op.drop_table('player_team_memberships')
    op.drop_index(op.f('ix_matches_season_id'), table_name='matches')
    op.drop_index(op.f('ix_matches_match_date'), table_name='matches')
    op.drop_index(op.f('ix_matches_home_team_id'), table_name='matches')
    op.drop_index(op.f('ix_matches_competition_id'), table_name='matches')
    op.drop_index(op.f('ix_matches_away_team_id'), table_name='matches')
    op.drop_table('matches')
    op.drop_index('uq_users_email_casefold', table_name='users')
    op.drop_table('users')
    op.drop_table('teams')
    op.drop_table('seasons')
    op.drop_table('players')
    op.drop_table('competitions')
