const fields = ['Event Type', 'Player', 'Phase of Play', 'Outcome', 'Start Time', 'End Time', 'Team', 'Context']
const tags = ['Press', 'Recovery', 'Progressive Pass', 'Turnover', 'Goal Chance', 'Build Up']

export default function AnnotationEditor() {
  return <section className="card va-editor" aria-labelledby="editor-title">
    <div className="va-card-heading"><h2 id="editor-title">Annotation Editor</h2><span className="va-count">PREVIEW</span></div>
    <div className="va-editor__body"><p className="va-helper">Temporary layout fields. Changes are not saved.</p>
      <div className="va-fields">{fields.map(field => <label key={field}>{field}<input type="text" placeholder={field.includes('Time') ? '00:00' : `Enter ${field.toLowerCase()}`} /></label>)}</div>
      <label className="va-field">Tags<input type="text" placeholder="Add a tag…" /></label>
      <div className="va-tags">{tags.map(tag => <button type="button" key={tag}>{tag}</button>)}</div>
      <label className="va-field">Notes<textarea rows={2} placeholder="Add a note about this moment…" /></label>
      <div className="va-editor__actions"><button type="button" className="va-button va-button--danger">Delete</button><button type="button" className="va-button">Clear</button><button type="button" className="va-button va-button--primary">Save Annotation</button></div>
      <p className="va-helper">Editor actions are visual only.</p>
    </div>
  </section>
}
