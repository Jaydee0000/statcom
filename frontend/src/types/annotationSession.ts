export type AnnotationSession = {
  id: string
  videoId: string
  matchName: string
  date: string
  annotator: string
  progress: number
  status: 'In Progress' | 'Completed'
}
