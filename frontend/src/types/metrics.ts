export type MetricValues = {
  total_actions: number; passes: number; completed_passes: number; incomplete_passes: number
  pass_completion_pct: number | null; progressive_passes: number; shots: number
  shots_on_target: number; goals: number; assists: number; tackles: number
  interceptions: number; turnovers: number
}
export type AppliedFilters = {
  player_id: string | null; skill_id: string | null; tag_id: string | null; outcome: string | null
  start_time: number | null; end_time: number | null; session_id: string | null; period: string | null
  bucket_seconds: number
}
export type BreakdownItem = { id: string | null; label: string; count: number }
export type TimelineBucket = { start_time: number; end_time: number; count: number }
export type MetricEvent = {
  annotation_id: string; annotation_session_id: string; video_id: string; skill_id: string | null
  skill: string; video_start_time: number; video_end_time: number | null; match_time: number
  period: string | null; player_ids: string[]; tag_ids: string[]; outcomes: string[]
}
export type Breakdowns = {
  actions_by_skill: BreakdownItem[]; actions_by_outcome: BreakdownItem[]
  actions_by_player: BreakdownItem[]; actions_by_tag: BreakdownItem[]
  timeline_buckets: TimelineBucket[]; events: MetricEvent[]
}
export type TeamMetrics = { team_id: string; team_name: string; side: string; metrics: MetricValues }
export type PlayerSummary = {
  player_id: string; team_id: string; first_name: string; last_name: string
  jersey_number: number | null; metrics: MetricValues
}
export type MatchMetrics = {
  match_id: string; home_team_id: string; away_team_id: string; filters: AppliedFilters
  metrics: MetricValues; teams: TeamMetrics[]; players: PlayerSummary[]; breakdowns: Breakdowns
  unattributed: { unknown_participant_actions: number; no_player_actions: number; ambiguous_team_actions: number }
}
export type MetricsFilters = {
  player_id?: string; skill_id?: string; tag_id?: string; outcome?: string
  start_time?: number; end_time?: number; session_id?: string; period?: string; bucket_seconds?: number
}
