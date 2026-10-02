export type CoverageStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'READY_FOR_REVIEW' | 'REVIEWED'
export type Result = 'W' | 'D' | 'L'

export type MetricDefinition = {
  key: string; label: string; format: 'count' | 'percent' | 'minutes' | 'rate'
  aggregation: 'sum' | 'ratio'; numerator_key: string | null; denominator_key: string | null
  traceable: boolean; supports_per_90: boolean; custom: boolean
}
export type MetricValue = { key: string; value: number | null; numerator: number | null; denominator: number | null; annotation_count: number }
export type Coverage = { status: CoverageStatus; complete: boolean; session_count: number; reviewed_sessions: number }
export type PlayerIdentity = {
  id: string; first_name: string; last_name: string; date_of_birth: string | null
  primary_position: string | null; secondary_position: string | null; preferred_foot: string | null
  photo_url: string | null; team_id: string | null; team_name: string | null
  jersey_number: number | null; availability: string | null
}
export type RosterPlayer = PlayerIdentity & {
  appearances: number; minutes: number | null; recent_form: Result[]; metrics: MetricValue[]; incomplete_matches: number
}
export type RosterResponse = { metric_definitions: MetricDefinition[]; players: RosterPlayer[] }
export type MatchReference = {
  id: string; match_date: string; home_team_id: string; home_team: string; away_team_id: string; away_team: string
  home_score: number | null; away_score: number | null; result: Result | null; opponent: string | null
  season_id: string | null; season: string | null; competition_id: string | null; competition: string | null
  location: string | null; status: string; coverage: Coverage
}
export type HistoryRow = {
  match: MatchReference; team_id: string; starter: boolean; position: string | null; minutes: number | null; metrics: MetricValue[]
}
export type PlayerHistory = { player: PlayerIdentity; metric_definitions: MetricDefinition[]; matches: HistoryRow[] }
export type PlayerSummary = {
  player: PlayerIdentity; appearances: number; minutes: number | null; metrics: MetricValue[]; coverage: Coverage
}
export type ResultGroup = { result: Result; match_count: number; complete_match_count: number; metrics: MetricValue[] }
export type ResultComparison = { player_id: string; metric_definitions: MetricDefinition[]; groups: ResultGroup[] }
export type SourceAnnotation = {
  annotation_id: string; annotation_session_id: string; video_id: string; match_id: string; match_date: string
  opponent: string | null; player_id: string | null; player_name: string | null; skill: string; tags: string[]
  outcomes: string[]; match_time: number; video_start_time: number; video_end_time: number | null; period: string | null
}
export type MetricSources = { metric: MetricDefinition; value: MetricValue; sources: SourceAnnotation[] }
export type VideoSummary = {
  id: string; original_filename: string; period: string | null; duration_seconds: number | null
  session_id: string | null; annotation_status: CoverageStatus
}
export type MatchPlayerStats = {
  player: PlayerIdentity; team_id: string; starter: boolean; position: string | null; minutes: number | null; metrics: MetricValue[]
}
export type MatchStats = {
  match: MatchReference; videos: VideoSummary[]; metric_definitions: MetricDefinition[]; participants: MatchPlayerStats[]
}
export type TeamStatSheet = {
  metric_definitions: MetricDefinition[]; players: RosterPlayer[]
  totals: { team_id: string; metrics: MetricValue[] }; match_count: number; incomplete_matches: number
}

export const metricValue = (values: MetricValue[], key: string) => values.find(item => item.key === key)?.value ?? null
export const formatMetric = (definition: MetricDefinition, value: number | null) => {
  if (value === null) return '—'
  if (definition.format === 'percent') return `${value.toFixed(1)}%`
  if (definition.format === 'minutes') return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(1)
  return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2)
}
export const coverageLabel = (status: CoverageStatus) => ({
  NOT_STARTED: 'Not Started', IN_PROGRESS: 'In Progress', READY_FOR_REVIEW: 'Ready for Review', REVIEWED: 'Reviewed',
}[status])
