import Icon from '../ui/Icon'

type Props = { onNew: () => void; onSelect: () => void }
export default function VideoAnalysisEmptyState({ onNew, onSelect }: Props) {
  return <section className="card va-empty" aria-labelledby="empty-title">
    <div className="va-empty__icon"><Icon name="video" /></div>
    <span className="va-eyebrow">YOUR ANALYSIS STARTS HERE</span>
    <h2 id="empty-title">No Annotation Session Selected</h2>
    <p>Choose a pending video, resume an in-progress video, or start a new annotation session to open the workspace and editor.</p>
    <div className="va-actions">
      <button type="button" className="va-button va-button--primary" onClick={onNew}>New Annotation Session</button>
      <button type="button" className="va-button" onClick={onSelect}>Select Pending Video</button>
    </div>
  </section>
}
