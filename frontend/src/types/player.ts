export type PlayerPosition = 'GK' | 'CB' | 'LB' | 'RB' | 'CDM' | 'CM' | 'CAM' | 'LW' | 'RW' | 'ST'
export type PlayerStatus = 'Available' | 'Injured' | 'Limited'
export type MatchResult = 'W' | 'D' | 'L'

export interface PlayerStats {
  minutesPlayed: number
  goals: number
  assists: number
  progressivePasses: number
  tackles: number
  interceptions: number
  turnovers: number
  averageRating: number
}

export interface RecentMatch {
  date: string
  opponent: string
  result: MatchResult
  minutes: number
  rating: number
  goals: number
  assists: number
}

export interface WinLossMetric {
  label: string
  wins: number
  losses: number
  suffix?: string
  inverse?: boolean
}

export interface VideoClip {
  title: string
  opponent: string
  date: string
  length: string
  tone: 'green' | 'blue' | 'amber'
}

export interface Player {
  id: number
  name: string
  number: number
  initials: string
  position: PlayerPosition
  positionName: string
  secondaryPosition: string
  age: number
  preferredFoot: 'Left' | 'Right'
  status: PlayerStatus
  recentForm: MatchResult[]
  matchesPlayed: number
  minutes: number
  goals: number
  assists: number
  rating: number
  team: string
  role: string
  roleDescription: string
  seasonStats: PlayerStats
  performanceRatings: number[]
  winLossMetrics: WinLossMetric[]
  recentMatches: RecentMatch[]
  videoClips: VideoClip[]
  strengths: string[]
  focusAreas: string[]
}
