export type FieldType = 'boolean' | 'number' | 'rating' | 'single_select' | 'multi_select' | 'text' | 'player_reference' | 'team_reference'

export type TagRecord = {
  id: string; name: string; normalized_name: string; description: string | null
  category: string | null; color: string | null; scope: string; is_active: boolean
}
export type SkillField = {
  id: string; key: string; label: string; data_type: FieldType; required: boolean
  description: string | null; options: string[] | null; display_order: number
}
export type SkillRecord = {
  id: string; name: string; description: string | null; category: string | null
  version: number; is_active: boolean; fields: SkillField[]
}
export type MatchPlayer = {
  participant_id: string; player_id: string; team_id: string; first_name: string; last_name: string
  jersey_number: number | null; starter: boolean; position_played: string | null
}
export type MatchTeam = { id: string; name: string }
export type MatchContext = { match_id: string; players: MatchPlayer[]; teams: MatchTeam[] }
export type AnnotationParticipant = {
  id: string; player_id: string | null; first_name: string | null; last_name: string | null; role: string
}
export type AnnotationRecord = {
  id: string; annotation_session_id: string; match_id: string; video_id: string; skill_definition_id: string
  video_start_time: number; video_end_time: number | null; match_period: string | null; match_time: number | null
  notes: string | null; review_status: 'DRAFT' | 'READY_FOR_REVIEW' | 'REVIEWED'; created_by: string | null
  created_at: string; updated_at: string
  tags: Pick<TagRecord, 'id' | 'name' | 'category' | 'color'>[]
  participants: AnnotationParticipant[]
  field_values: { id: string; field_definition_id: string; value: unknown }[]
}
export type AnnotationWrite = {
  match_id: string; video_id: string; skill_definition_id: string
  video_start_time: number; video_end_time: number | null; match_period: string | null; match_time: number
  notes: string | null; review_status: AnnotationRecord['review_status']; created_by: string | null
  tag_ids: string[]; participants: { player_id: string | null; role: string }[]
  field_values: { field_definition_id: string; value: unknown }[]
}
