import { useEffect, useRef, useState } from 'react'
import Icon from '../ui/Icon'
import { matchesApi, type MatchRecord, type TeamRecord } from '../../services/matchesApi'
import { videosApi } from '../../services/videosApi'

type Props = { onUploaded: () => Promise<void> }
export default function VideoIntake({ onUploaded }: Props) {
  const [matches, setMatches] = useState<MatchRecord[]>([])
  const [teams, setTeams] = useState<TeamRecord[]>([])
  const [matchId, setMatchId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [creating, setCreating] = useState(false)
  const [home, setHome] = useState('')
  const [away, setAway] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const input = useRef<HTMLInputElement>(null)
  const load = async () => {
    setLoading(true); setError('')
    try { const [m, t] = await Promise.all([matchesApi.list(), matchesApi.teams()]); setMatches(m); setTeams(t) }
    catch (e) { setError((e as Error).message) } finally { setLoading(false) }
  }
  useEffect(() => { void load() }, [])
  const choose = (selected?: File) => {
    setSuccess(''); setError('')
    if (!selected) return
    if (!/\.(mp4|mov|webm)$/i.test(selected.name)) { setFile(null); setError('Unsupported video format. Use MP4, MOV, or WebM.'); return }
    setFile(selected)
  }
  const upload = async () => {
    if (!matchId || !file) { setError('Choose a match and a video file first.'); return }
    setBusy(true); setProgress(0); setError(''); setSuccess('')
    try {
      await videosApi.upload(file, matchId, setProgress)
      setSuccess('Video uploaded successfully.'); setFile(null)
      if (input.current) input.current.value = ''
      await onUploaded()
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  const createMatch = async () => {
    if (!home.trim() || !away.trim() || !date || home.trim().toLowerCase() === away.trim().toLowerCase()) {
      setError('Enter two different teams and a match date.'); return
    }
    setBusy(true); setError('')
    try {
      const resolveTeam = async (name: string) => {
        const existing = teams.find(t => t.name.toLowerCase() === name.trim().toLowerCase())
        if (existing) return existing
        const team = await matchesApi.createTeam(name.trim())
        setTeams(current => [...current, team]); return team
      }
      const h = await resolveTeam(home), a = await resolveTeam(away)
      const match = await matchesApi.create({ home_team_id: h.id, away_team_id: a.id, match_date: date })
      setMatches(current => [...current, match]); setMatchId(match.id); setCreating(false); setSuccess('Match created.')
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  const teamName = (id: string) => teams.find(t => t.id === id)?.name || 'Team'
  return <section className="card va-dashboard-card va-intake" aria-labelledby="intake-title">
    <div className="va-card-heading"><h2 id="intake-title">Video Intake</h2><span className="va-count">UPLOAD</span></div>
    <div className="va-intake-fields">
      <label className="va-field">Match<select id="video-match" value={matchId} disabled={loading || busy} onChange={e => setMatchId(e.target.value)}>
        <option value="">{loading ? 'Loading matches…' : matches.length ? 'Choose a match' : 'Create your first match'}</option>
        {matches.map(m => <option value={m.id} key={m.id}>{teamName(m.home_team_id)} vs {teamName(m.away_team_id)} · {m.match_date}</option>)}
      </select></label>
      <button type="button" className="va-row-action" disabled={busy} onClick={() => setCreating(!creating)}>{creating ? 'Cancel' : 'Create match'}</button>
      {creating && <div className="va-fields"><label>Home team<input aria-label="Home team" list="intake-teams" value={home} onChange={e => setHome(e.target.value)} /></label>
        <label>Away team<input aria-label="Away team" list="intake-teams" value={away} onChange={e => setAway(e.target.value)} /></label>
        <datalist id="intake-teams">{teams.map(t => <option key={t.id} value={t.name} />)}</datalist>
        <label>Match date<input aria-label="Match date" type="date" value={date} onChange={e => setDate(e.target.value)} /></label>
        <button type="button" className="va-row-action" disabled={busy} onClick={() => void createMatch()}>{busy ? 'Saving…' : 'Save match'}</button></div>}
    </div>
    <input ref={input} id="video-file" type="file" accept=".mp4,.mov,.webm" hidden disabled={busy} onChange={e => choose(e.target.files?.[0])} />
    <button type="button" className="va-dropzone" disabled={busy} onClick={() => input.current?.click()}
      onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (!busy) choose(e.dataTransfer.files[0]) }}>
      <Icon name="video" /><strong>{file?.name || 'Drag and drop match footage'}</strong><span>or <b>click to browse</b></span><small>MP4, MOV, WebM</small>
    </button>
    <div className="va-intake-fields"><button className="va-button va-button--primary" disabled={busy || loading} onClick={() => void upload()}>{busy ? `Uploading / processing… ${progress}%` : 'Upload selected video'}</button>
      {busy && <progress max="100" value={progress} aria-label="Upload progress" />}
      {error && <p role="alert" className="va-error">{error} <button className="va-row-action" onClick={() => void load()}>Reload matches</button></p>}
      {success && <p role="status" className="va-helper">{success}</p>}
    </div>
  </section>
}
