import { useEffect, useMemo, useRef, useState } from 'react'
import { annotationsApi, type SkillCreate } from '../../services/annotationsApi'
import type { AnnotationRecord, AnnotationWrite, MatchContext, SkillField, SkillRecord, TagRecord } from '../../types/annotation'

type Props = {
  sessionId: string; matchId: string; videoId: string; period: string | null
  videoOffset: number; matchOffset: number; currentTime: number; duration: number
  selected: AnnotationRecord | null; tags: TagRecord[]; skills: SkillRecord[]; context: MatchContext | null
  onSaved: (annotation: AnnotationRecord) => void; onArchived: (id: string) => void
  onTagCreated: (tag: TagRecord) => void; onSkillCreated: (skill: SkillRecord) => void
  onClearSelection: () => void; onDirtyChange: (dirty: boolean) => void
}
type ParticipantDraft = { player_id: string | null; role: string }
type SaveState = 'idle' | 'saving' | 'saved' | 'failed'

const formatTime = (value: number | null) => value === null ? '—' : `${Math.floor(value / 60).toString().padStart(2, '0')}:${(value % 60).toFixed(1).padStart(4, '0')}`
const fieldEmpty = (value: unknown) => value === undefined || value === null || (typeof value === 'string' && !value.trim()) || (Array.isArray(value) && value.length === 0)
const keyFromLabel = (value: string) => value.toLowerCase().trim().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').replace(/^[^a-z]+/, '') || 'field'
const loadRecentTags = () => {
  try {
    const stored: unknown = JSON.parse(localStorage.getItem('statcom-recent-tags') || '[]')
    return Array.isArray(stored) ? stored.filter((id): id is string => typeof id === 'string') : []
  } catch { return [] }
}

export default function AnnotationEditor({ sessionId, matchId, videoId, period, videoOffset, matchOffset, currentTime, duration,
  selected, tags, skills, context, onSaved, onArchived, onTagCreated, onSkillCreated, onClearSelection, onDirtyChange }: Props) {
  const [start, setStart] = useState<number | null>(currentTime)
  const [end, setEnd] = useState<number | null>(null)
  const [skillId, setSkillId] = useState('')
  const [tagIds, setTagIds] = useState<string[]>([])
  const [participants, setParticipants] = useState<ParticipantDraft[]>([])
  const [values, setValues] = useState<Record<string, unknown>>({})
  const [notes, setNotes] = useState('')
  const [reviewStatus, setReviewStatus] = useState<AnnotationRecord['review_status']>('DRAFT')
  const [dirty, setDirtyState] = useState(false)
  const [saveState, setSaveState] = useState<SaveState>('idle')
  const [error, setError] = useState('')
  const inFlight = useRef(false)
  const [tagSearch, setTagSearch] = useState('')
  const [tagCategory, setTagCategory] = useState('')
  const [recent, setRecent] = useState<string[]>(loadRecentTags)
  const [showTagForm, setShowTagForm] = useState(false)
  const [newTag, setNewTag] = useState({ name: '', description: '', category: '', color: '#20b876' })
  const [showSkillForm, setShowSkillForm] = useState(false)
  const [newSkill, setNewSkill] = useState<SkillCreate>({ name: '', description: null, category: null, fields: [] })
  const setDirty = (value = true) => { setDirtyState(value); onDirtyChange(value); if (value) setSaveState('idle') }
  const selectedSkill = skills.find(skill => skill.id === skillId)

  useEffect(() => {
    if (selected) {
      setStart(selected.video_start_time); setEnd(selected.video_end_time); setSkillId(selected.skill_definition_id)
      setTagIds(selected.tags.map(tag => tag.id))
      setParticipants(selected.participants.map(item => ({ player_id: item.player_id, role: item.role })))
      setValues(Object.fromEntries(selected.field_values.map(item => [item.field_definition_id, item.value])))
      setNotes(selected.notes || ''); setReviewStatus(selected.review_status)
    } else {
      setStart(currentTime); setEnd(null); setSkillId(''); setTagIds([]); setParticipants([]); setValues({}); setNotes(''); setReviewStatus('DRAFT')
    }
    setError(''); setSaveState(current => current === 'saved' ? 'saved' : 'idle'); setDirtyState(false); onDirtyChange(false)
    // Playback changes must not reset a draft.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected?.id])

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (dirty) event.preventDefault() }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])

  useEffect(() => {
    if (!selected && !dirty) setStart(currentTime)
  }, [currentTime, dirty, selected])

  const categories = [...new Set(tags.map(tag => tag.category).filter((value): value is string => Boolean(value)))].sort()
  const visibleTags = useMemo(() => tags.filter(tag => (!tagCategory || tag.category === tagCategory) &&
    (!tagSearch || `${tag.name} ${tag.description || ''}`.toLowerCase().includes(tagSearch.toLowerCase())))
    .sort((a, b) => {
      const ai = recent.indexOf(a.id), bi = recent.indexOf(b.id)
      return (ai < 0 ? 999 : ai) - (bi < 0 ? 999 : bi) || a.name.localeCompare(b.name)
    }), [tags, tagCategory, tagSearch, recent])

  const changeValue = (field: SkillField, value: unknown) => { setValues(current => ({ ...current, [field.id]: value })); setDirty() }
  const renderField = (field: SkillField) => {
    const value = values[field.id]
    if (field.data_type === 'boolean') return <input type="checkbox" checked={value === true} onChange={event => changeValue(field, event.target.checked)} />
    if (field.data_type === 'number' || field.data_type === 'rating') return <input type="number" step="any" min={field.data_type === 'rating' ? 1 : undefined} max={field.data_type === 'rating' ? 5 : undefined} value={typeof value === 'number' ? value : ''} onChange={event => changeValue(field, event.target.value === '' ? undefined : Number(event.target.value))} />
    if (field.data_type === 'single_select') return <select value={typeof value === 'string' ? value : ''} onChange={event => changeValue(field, event.target.value)}><option value="">Select…</option>{field.options?.map(option => <option key={option}>{option}</option>)}</select>
    if (field.data_type === 'multi_select') return <select multiple value={Array.isArray(value) ? value as string[] : []} onChange={event => changeValue(field, [...event.target.selectedOptions].map(option => option.value))}>{field.options?.map(option => <option key={option}>{option}</option>)}</select>
    if (field.data_type === 'player_reference') return <select value={typeof value === 'string' ? value : ''} onChange={event => changeValue(field, event.target.value)}><option value="">Select match player…</option>{context?.players.map(player => <option key={player.player_id} value={player.player_id}>{player.first_name} {player.last_name}</option>)}</select>
    if (field.data_type === 'team_reference') return <select value={typeof value === 'string' ? value : ''} onChange={event => changeValue(field, event.target.value)}><option value="">Select match team…</option>{context?.teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}</select>
    return <textarea rows={2} value={typeof value === 'string' ? value : ''} onChange={event => changeValue(field, event.target.value)} />
  }

  const buildPayload = (): AnnotationWrite => {
    if (start === null) throw new Error('Choose a point or set a start time.')
    if (start < 0 || start > duration || (end !== null && (end < start || end > duration))) throw new Error('The selected time must be within the video and the end cannot precede the start.')
    if (!skillId || !selectedSkill) throw new Error('Choose a skill.')
    const missing = selectedSkill.fields.filter(field => field.required && fieldEmpty(values[field.id])).map(field => field.label)
    if (missing.length) throw new Error(`Complete required fields: ${missing.join(', ')}.`)
    return { match_id: matchId, video_id: videoId, skill_definition_id: skillId, video_start_time: start,
      video_end_time: end, match_period: period, match_time: Math.max(0, start - videoOffset + matchOffset),
      notes: notes.trim() || null, review_status: reviewStatus, created_by: null, tag_ids: tagIds,
      participants, field_values: selectedSkill.fields.filter(field => !fieldEmpty(values[field.id])).map(field => ({ field_definition_id: field.id, value: values[field.id] })) }
  }
  const save = async () => {
    if (inFlight.current) return
    setError('')
    let payload: AnnotationWrite
    try { payload = buildPayload() } catch (e) { setError((e as Error).message); return }
    inFlight.current = true; setSaveState('saving')
    try {
      const saved = selected ? await annotationsApi.update(selected.id, payload) : await annotationsApi.create(sessionId, payload)
      const recentIds = [...tagIds, ...recent.filter(id => !tagIds.includes(id))].slice(0, 8)
      localStorage.setItem('statcom-recent-tags', JSON.stringify(recentIds))
      setRecent(recentIds)
      onSaved(saved); setDirty(false); setSaveState('saved')
    } catch (e) { setError((e as Error).message); setSaveState('failed') } finally { inFlight.current = false }
  }
  useEffect(() => {
    const shortcuts = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement
      const typing = target.matches('input, textarea, select, [contenteditable="true"]')
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') { event.preventDefault(); void save(); return }
      if (typing) return
      if (event.key.toLowerCase() === 's') { event.preventDefault(); setStart(currentTime); if (end !== null && end < currentTime) setEnd(null); setDirty() }
      if (event.key.toLowerCase() === 'e') { event.preventDefault(); if (start === null || currentTime < start) setError('Set a valid start time before the end.'); else { setEnd(currentTime); setDirty() } }
    }
    window.addEventListener('keydown', shortcuts)
    return () => window.removeEventListener('keydown', shortcuts)
  })
  const clear = () => {
    if (dirty && !window.confirm('Discard unsaved annotation changes?')) return
    onClearSelection(); setStart(currentTime); setEnd(null); setSkillId(''); setTagIds([]); setParticipants([]); setValues({}); setNotes(''); setReviewStatus('DRAFT'); setDirty(false); setSaveState('idle'); setError('')
  }
  const archive = async () => {
    if (!selected || !window.confirm('Archive this annotation? It will leave the active timeline and list.')) return
    try { await annotationsApi.archive(selected.id); onArchived(selected.id); onClearSelection() } catch (e) { setError((e as Error).message) }
  }
  const createTag = async () => {
    try {
      const tag = await annotationsApi.createTag({ name: newTag.name, description: newTag.description || null, category: newTag.category || null, color: newTag.color || null })
      onTagCreated(tag); setTagIds(current => [...current, tag.id]); setNewTag({ name: '', description: '', category: '', color: '#20b876' }); setShowTagForm(false); setDirty()
    } catch (e) { setError((e as Error).message) }
  }
  const createSkill = async () => {
    try {
      const skill = await annotationsApi.createSkill(newSkill)
      onSkillCreated(skill); setSkillId(skill.id); setValues({}); setNewSkill({ name: '', description: null, category: null, fields: [] }); setShowSkillForm(false); setDirty()
    } catch (e) { setError((e as Error).message) }
  }

  return <section className="card va-editor" aria-labelledby="editor-title">
    <div className="va-card-heading"><h2 id="editor-title">Annotation Editor</h2><span className="va-count">{selected ? 'EDITING' : 'NEW'}</span></div>
    <div className="va-editor__body">
      <div className="va-range-summary"><strong>{end === null ? 'Point' : 'Range'}</strong><span>{formatTime(start)}{end !== null ? ` → ${formatTime(end)}` : ''}</span></div>
      <div className="va-range-actions">
        <button type="button" className="va-row-action" onClick={() => { setStart(currentTime); if (end !== null && end < currentTime) setEnd(null); setDirty() }}>Set Start</button>
        <button type="button" className="va-row-action" onClick={() => { if (start === null) setError('Set a start time first.'); else if (currentTime < start) setError('End time cannot be before start time.'); else { setEnd(currentTime); setDirty() } }}>Set End</button>
        <button type="button" className="va-row-action" onClick={() => { setStart(currentTime); setEnd(null); setDirty() }}>Use Current Time</button>
        <button type="button" className="va-row-action" onClick={() => { setStart(null); setEnd(null); setDirty() }}>Clear Selection</button>
      </div>
      <p className="va-helper">Video: {formatTime(start)} · Match: {start === null ? '—' : formatTime(Math.max(0, start - videoOffset + matchOffset))}{period ? ` · ${period}` : ''}</p>

      <label className="va-field">Skill <select value={skillId} onChange={event => { setSkillId(event.target.value); setValues({}); setDirty() }}><option value="">Choose skill…</option>{skills.map(skill => <option key={skill.id} value={skill.id}>{skill.name}{skill.version > 1 ? ` v${skill.version}` : ''}</option>)}</select></label>
      <button type="button" className="va-row-action va-inline-action" onClick={() => setShowSkillForm(value => !value)}>Add New Skill</button>
      {showSkillForm && <div className="va-inline-form">
        <input aria-label="New skill name" placeholder="Skill name" value={newSkill.name} onChange={event => setNewSkill({ ...newSkill, name: event.target.value })} />
        <input aria-label="New skill description" placeholder="Description" value={newSkill.description || ''} onChange={event => setNewSkill({ ...newSkill, description: event.target.value || null })} />
        <input aria-label="New skill category" placeholder="Category" value={newSkill.category || ''} onChange={event => setNewSkill({ ...newSkill, category: event.target.value || null })} />
        {newSkill.fields.map((field, index) => <div className="va-skill-field-row" key={index}>
          <input aria-label={`Field ${index + 1} label`} placeholder="Field label" value={field.label} onChange={event => { const fields = [...newSkill.fields]; fields[index] = { ...field, label: event.target.value, key: keyFromLabel(event.target.value) }; setNewSkill({ ...newSkill, fields }) }} />
          <select aria-label={`Field ${index + 1} type`} value={field.data_type} onChange={event => { const fields = [...newSkill.fields]; const data_type = event.target.value; fields[index] = { ...field, data_type, options: data_type.includes('select') ? (field.options || []) : null }; setNewSkill({ ...newSkill, fields }) }}>{['boolean','number','rating','single_select','multi_select','text','player_reference','team_reference'].map(type => <option key={type}>{type}</option>)}</select>
          {field.data_type.includes('select') && <input aria-label={`Field ${index + 1} options`} placeholder="Options, comma separated" value={(field.options || []).join(', ')} onChange={event => { const fields = [...newSkill.fields]; fields[index] = { ...field, options: event.target.value.split(',').map(value => value.trim()).filter(Boolean) }; setNewSkill({ ...newSkill, fields }) }} />}
          <label><input type="checkbox" checked={field.required} onChange={event => { const fields = [...newSkill.fields]; fields[index] = { ...field, required: event.target.checked }; setNewSkill({ ...newSkill, fields }) }} /> Required</label>
          <button type="button" className="va-row-action" onClick={() => setNewSkill({ ...newSkill, fields: newSkill.fields.filter((_, item) => item !== index) })}>Remove</button>
        </div>)}
        <div className="va-range-actions"><button type="button" className="va-row-action" onClick={() => setNewSkill({ ...newSkill, fields: [...newSkill.fields, { key: `field_${newSkill.fields.length + 1}`, label: '', data_type: 'text', required: false, options: null, display_order: newSkill.fields.length }] })}>Add Field</button><button type="button" className="va-button va-button--primary" disabled={!newSkill.name} onClick={() => void createSkill()}>Save Skill</button></div>
      </div>}

      {selectedSkill?.fields.map(field => <label className="va-field" key={field.id}>{field.label}{field.required ? ' *' : ''}{renderField(field)}{field.description && <small>{field.description}</small>}</label>)}

      <div className="va-field"><span>Players</span>{participants.map((participant, index) => <div className="va-participant-row" key={index}>
        <select aria-label={`Participant ${index + 1}`} value={participant.player_id || '__unknown__'} onChange={event => { const next = [...participants]; next[index] = { ...participant, player_id: event.target.value === '__unknown__' ? null : event.target.value }; setParticipants(next); setDirty() }}><option value="__unknown__">Unknown player</option>{context?.players.map(player => <option key={player.player_id} value={player.player_id}>{player.jersey_number !== null ? `#${player.jersey_number} ` : ''}{player.first_name} {player.last_name}</option>)}</select>
        <input aria-label={`Participant ${index + 1} role`} list="participant-roles" value={participant.role} onChange={event => { const next = [...participants]; next[index] = { ...participant, role: event.target.value }; setParticipants(next); setDirty() }} />
        <button type="button" className="va-row-action" onClick={() => { setParticipants(participants.filter((_, item) => item !== index)); setDirty() }}>Remove</button>
      </div>)}<datalist id="participant-roles">{['Player','Passer','Receiver','Defender','Target'].map(role => <option key={role} value={role} />)}</datalist>
      <button type="button" className="va-row-action va-inline-action" onClick={() => { setParticipants([...participants, { player_id: context?.players[0]?.player_id || null, role: 'Player' }]); setDirty() }}>Add Player</button></div>

      <div className="va-tag-tools"><input aria-label="Search tags" placeholder="Search tags…" value={tagSearch} onChange={event => setTagSearch(event.target.value)} /><select aria-label="Filter tag category" value={tagCategory} onChange={event => setTagCategory(event.target.value)}><option value="">All categories</option>{categories.map(category => <option key={category}>{category}</option>)}</select></div>
      <div className="va-tags">{visibleTags.map(tag => <button type="button" className={tagIds.includes(tag.id) ? 'is-selected' : ''} style={{ borderColor: tag.color || undefined }} key={tag.id} onClick={() => { setTagIds(current => current.includes(tag.id) ? current.filter(id => id !== tag.id) : [...current, tag.id]); setDirty() }}>{tag.name}</button>)}</div>
      <button type="button" className="va-row-action va-inline-action" onClick={() => setShowTagForm(value => !value)}>Add New Tag</button>
      {showTagForm && <div className="va-inline-form"><input aria-label="New tag name" placeholder="Tag name" value={newTag.name} onChange={event => setNewTag({ ...newTag, name: event.target.value })} /><input aria-label="New tag description" placeholder="Description" value={newTag.description} onChange={event => setNewTag({ ...newTag, description: event.target.value })} /><input aria-label="New tag category" placeholder="Category" value={newTag.category} onChange={event => setNewTag({ ...newTag, category: event.target.value })} /><input aria-label="New tag color" type="color" value={newTag.color} onChange={event => setNewTag({ ...newTag, color: event.target.value })} /><button type="button" className="va-button va-button--primary" disabled={!newTag.name.trim()} onClick={() => void createTag()}>Save Tag</button></div>}

      <label className="va-field">Status<select value={reviewStatus} onChange={event => { setReviewStatus(event.target.value as AnnotationRecord['review_status']); setDirty() }}><option value="DRAFT">Draft</option><option value="READY_FOR_REVIEW">Ready for Review</option><option value="REVIEWED">Reviewed</option></select></label>
      <label className="va-field">Notes<textarea rows={2} value={notes} placeholder="Add a note about this moment…" onChange={event => { setNotes(event.target.value); setDirty() }} /></label>
      <div className="va-editor__actions">{selected && <button type="button" className="va-button va-button--danger" onClick={() => void archive()}>Delete</button>}<button type="button" className="va-button" onClick={clear}>Clear</button><button type="button" className="va-button va-button--primary" disabled={saveState === 'saving'} onClick={() => void save()}>{saveState === 'saving' ? 'Saving…' : selected ? 'Save Changes' : 'Save Annotation'}</button></div>
      {saveState === 'saved' && <p className="va-success" role="status">Saved</p>}
      {error && <p className="va-error" role="alert">{saveState === 'failed' ? 'Save failed: ' : ''}{error} {saveState === 'failed' && <button type="button" className="va-row-action" onClick={() => void save()}>Retry</button>}</p>}
      <p className="va-helper">Shortcuts: Space play/pause · S start · E end · Ctrl/Cmd+S save · ←/→ seek 2 seconds</p>
    </div>
  </section>
}
