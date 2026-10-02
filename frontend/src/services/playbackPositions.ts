import { annotationSessionsApi } from './annotationSessionsApi'
// Queue per session survives route unmounts; a late older save cannot overwrite a newer one.
const queues = new Map<string, Promise<void>>()
const pending = new Map<string, number>()
const lastSaved = new Map<string, number>()
export const playbackPositions = {
  save(id: string, position: number) {
    pending.set(id, position)
    const task = (queues.get(id) || Promise.resolve()).catch(() => {}).then(async () => {
      if (lastSaved.get(id) === position) return
      await annotationSessionsApi.update(id, { last_playback_position: position }, true)
      lastSaved.set(id, position)
      sessionStorage.removeItem(`statcom-save-error-${id}`)
    })
    queues.set(id, task)
    void task.catch(() => sessionStorage.setItem(`statcom-save-error-${id}`, 'Your last playback position could not be saved.'))
    return task
  },
  async flush(id: string) {
    try { await queues.get(id) } catch {
      const position = pending.get(id)
      if (position !== undefined) await this.save(id, position)
    }
  },
}
