import type { Video } from '../types/video'

export const mockVideos: Video[] = [
  { id: 'v1', fileName: 'riverside-eastwood.mp4', matchName: 'Riverside vs Eastwood', dateAdded: '23 Sep 2026', duration: '94:12', status: 'In Progress', progress: 60 },
  { id: 'v2', fileName: 'riverside-northside.mp4', matchName: 'Riverside vs Northside', dateAdded: '22 Sep 2026', duration: '92:30', status: 'In Progress', progress: 25 },
  { id: 'v3', fileName: 'westfield-metro-city.mov', matchName: 'Westfield vs Metro City', dateAdded: '21 Sep 2026', duration: '96:08', status: 'In Progress', progress: 90 },
  { id: 'v4', fileName: 'riverside-kingston.mp4', matchName: 'Riverside vs Kingston', dateAdded: '20 Sep 2026', duration: '93:45', status: 'Not Started' },
  { id: 'v5', fileName: 'riverside-oakland.mp4', matchName: 'Riverside vs Oakland', dateAdded: '18 Sep 2026', duration: '91:20', status: 'Reviewed' },
  { id: 'v6', fileName: 'riverside-united.mp4', matchName: 'Riverside vs United', dateAdded: '15 Sep 2026', duration: '95:00', status: 'Annotated' },
  { id: 'v7', fileName: 'metro-city-westfield.mp4', matchName: 'Metro City vs Westfield', dateAdded: '12 Sep 2026', duration: '92:15', status: 'Reviewed' },
  { id: 'v8', fileName: 'kingston-riverside.mov', matchName: 'Kingston vs Riverside', dateAdded: '08 Sep 2026', duration: '94:40', status: 'Annotated' },
]
export const pendingVideos = mockVideos.filter(video => video.status === 'Not Started' || video.status === 'In Progress')
export const completedVideos = mockVideos.filter(video => video.status === 'Annotated' || video.status === 'Reviewed')
