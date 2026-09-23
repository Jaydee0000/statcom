import type { MatchResult, Player, PlayerPosition, PlayerStatus } from '../types/player'

const defaultRatings = [6.9, 7.2, 7.6, 7.4, 8.0, 7.7, 8.2, 7.5, 7.9, 8.4]

const sharedProfile = {
  team: 'Riverside FC',
  preferredFoot: 'Right' as const,
  secondaryPosition: 'Attacking Midfielder',
  role: 'Box-to-Box Midfielder',
  roleDescription: 'Connects defensive and attacking phases, contributes in buildup, ball progression, and defensive recovery.',
  performanceRatings: defaultRatings,
  winLossMetrics: [
    { label: 'Pass Accuracy', wins: 87, losses: 74, suffix: '%' },
    { label: 'Progressive Passes', wins: 12.1, losses: 6.3 },
    { label: 'Recoveries', wins: 8.4, losses: 5.1 },
    { label: 'Turnovers', wins: 5.8, losses: 9.4, inverse: true },
    { label: 'Tackles', wins: 4.7, losses: 3.1 },
    { label: 'Interceptions', wins: 3.6, losses: 2.2 },
  ],
  recentMatches: [
    { date: 'Apr 5', opponent: 'Northview', result: 'W' as const, minutes: 90, rating: 8.4, goals: 1, assists: 1 },
    { date: 'Mar 29', opponent: 'Summit FC', result: 'W' as const, minutes: 90, rating: 7.8, goals: 0, assists: 1 },
    { date: 'Mar 22', opponent: 'Westlake', result: 'L' as const, minutes: 90, rating: 6.8, goals: 0, assists: 0 },
    { date: 'Mar 15', opponent: 'Central HS', result: 'D' as const, minutes: 90, rating: 7.6, goals: 0, assists: 1 },
    { date: 'Mar 8', opponent: 'Oakridge', result: 'W' as const, minutes: 90, rating: 8.1, goals: 1, assists: 0 },
  ],
  videoClips: [
    { title: 'Progressive Passing', opponent: 'Northview', date: 'Apr 5', length: '01:24', tone: 'green' as const },
    { title: 'Defensive Recovery', opponent: 'Summit FC', date: 'Mar 29', length: '00:48', tone: 'blue' as const },
    { title: 'Goal Contribution', opponent: 'Oakridge', date: 'Mar 8', length: '01:06', tone: 'amber' as const },
  ],
  strengths: ['Passing range', 'Ball retention', 'Defensive work rate'],
  focusAreas: ['Reduce turnovers in final third', 'Improve shooting accuracy', 'Increase attacking-box involvement'],
}

type RosterPlayer = {
  name: string
  number: number
  position: PlayerPosition
  positionName: string
  age: number
  status: PlayerStatus
  recentForm: MatchResult[]
  matchesPlayed: number
  minutes: number
  goals: number
  assists: number
  rating: number
}

const roster: RosterPlayer[] = [
  { name: 'Ethan Carter', number: 10, position: 'CM', positionName: 'Central Midfielder', age: 22, status: 'Available', recentForm: ['W','W','L','D','W'], matchesPlayed: 30, minutes: 2520, goals: 8, assists: 5, rating: 8.1 },
  { name: 'Lucas Mendes', number: 1, position: 'GK', positionName: 'Goalkeeper', age: 27, status: 'Available', recentForm: ['W','W','L','D','W'], matchesPlayed: 29, minutes: 2610, goals: 0, assists: 0, rating: 7.5 },
  { name: 'Mateo Ruiz', number: 4, position: 'CB', positionName: 'Centre Back', age: 25, status: 'Available', recentForm: ['W','D','L','W','W'], matchesPlayed: 28, minutes: 2387, goals: 2, assists: 1, rating: 7.7 },
  { name: 'Noah Kim', number: 3, position: 'LB', positionName: 'Left Back', age: 21, status: 'Limited', recentForm: ['D','W','W','L','D'], matchesPlayed: 24, minutes: 1864, goals: 1, assists: 6, rating: 7.3 },
  { name: 'Liam Parker', number: 2, position: 'RB', positionName: 'Right Back', age: 23, status: 'Available', recentForm: ['W','W','D','W','L'], matchesPlayed: 27, minutes: 2241, goals: 2, assists: 4, rating: 7.4 },
  { name: 'Daniel Okafor', number: 6, position: 'CDM', positionName: 'Defensive Midfielder', age: 26, status: 'Available', recentForm: ['W','D','W','W','W'], matchesPlayed: 30, minutes: 2479, goals: 3, assists: 3, rating: 7.8 },
  { name: 'Samuel Diaz', number: 8, position: 'CM', positionName: 'Central Midfielder', age: 24, status: 'Injured', recentForm: ['W','L','D','W','L'], matchesPlayed: 20, minutes: 1538, goals: 4, assists: 5, rating: 7.2 },
  { name: 'Ryan Patel', number: 11, position: 'LW', positionName: 'Left Winger', age: 20, status: 'Available', recentForm: ['W','W','W','D','W'], matchesPlayed: 26, minutes: 1920, goals: 10, assists: 7, rating: 8.0 },
  { name: 'Owen Clarke', number: 7, position: 'RW', positionName: 'Right Winger', age: 23, status: 'Available', recentForm: ['L','W','D','W','W'], matchesPlayed: 28, minutes: 2133, goals: 9, assists: 8, rating: 7.9 },
  { name: 'Marcus Bell', number: 9, position: 'ST', positionName: 'Striker', age: 28, status: 'Available', recentForm: ['W','W','L','W','W'], matchesPlayed: 29, minutes: 2304, goals: 17, assists: 3, rating: 8.2 },
  { name: 'Leo Fernandes', number: 14, position: 'CAM', positionName: 'Attacking Midfielder', age: 22, status: 'Limited', recentForm: ['D','W','W','D','L'], matchesPlayed: 22, minutes: 1498, goals: 6, assists: 9, rating: 7.6 },
  { name: 'Jack Morrison', number: 5, position: 'CB', positionName: 'Centre Back', age: 29, status: 'Available', recentForm: ['W','W','D','L','W'], matchesPlayed: 25, minutes: 2187, goals: 3, assists: 0, rating: 7.4 },
  { name: 'Andre Silva', number: 15, position: 'CB', positionName: 'Centre Back', age: 24, status: 'Available', recentForm: ['W','L','W','D','W'], matchesPlayed: 19, minutes: 1342, goals: 1, assists: 1, rating: 7.1 },
  { name: 'Tyler Brooks', number: 18, position: 'ST', positionName: 'Striker', age: 19, status: 'Injured', recentForm: ['D','L','W','L','D'], matchesPlayed: 16, minutes: 884, goals: 5, assists: 2, rating: 6.9 },
  { name: 'Julian Costa', number: 21, position: 'CAM', positionName: 'Attacking Midfielder', age: 21, status: 'Available', recentForm: ['W','D','W','W','D'], matchesPlayed: 23, minutes: 1617, goals: 7, assists: 6, rating: 7.7 },
]

const initials = (name: string) => name.split(' ').map((part) => part[0]).join('')

export const mockPlayers: Player[] = roster.map((player, index) => ({
  ...player,
  id: index + 1,
  initials: initials(player.name),
  ...sharedProfile,
  seasonStats: {
    minutesPlayed: player.minutes,
    goals: player.goals,
    assists: player.assists,
    progressivePasses: index === 0 ? 86 : 58 + index * 2,
    tackles: index === 0 ? 64 : 38 + index,
    interceptions: index === 0 ? 41 : 24 + index,
    turnovers: index === 0 ? 38 : 28 + index,
    averageRating: player.rating,
  },
}))

export const getPlayerById = (id: string | undefined) => mockPlayers.find((player) => player.id === Number(id))
