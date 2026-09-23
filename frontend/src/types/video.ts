export type Video = {
  id: string
  fileName: string
  matchName: string
  dateAdded: string
  duration: string
  progress?: number
  status: 'Not Started' | 'In Progress' | 'Annotated' | 'Reviewed'
}
