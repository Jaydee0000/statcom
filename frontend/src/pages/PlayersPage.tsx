import { useState } from 'react'
import PageHeader from '../components/layout/PageHeader'
import PlayerRosterTable from '../components/players/PlayerRosterTable'
import { mockPlayers } from '../data/mockPlayers'

const positionGroups = ['All', 'Goalkeepers', 'Defenders', 'Midfielders', 'Forwards'] as const
const availability = ['All', 'Available', 'Unavailable'] as const

export default function PlayersPage() {
  const [positionFilter, setPositionFilter] = useState<(typeof positionGroups)[number]>('All')
  const [availabilityFilter, setAvailabilityFilter] = useState<(typeof availability)[number]>('All')

  const positionMap = {
    Goalkeepers: ['GK'], Defenders: ['CB', 'LB', 'RB'], Midfielders: ['CDM', 'CM', 'CAM'], Forwards: ['LW', 'RW', 'ST'],
  }
  const visiblePlayers = mockPlayers.filter((player) => {
    const matchesPosition = positionFilter === 'All' || positionMap[positionFilter].includes(player.position)
    const matchesAvailability = availabilityFilter === 'All' || (availabilityFilter === 'Available' ? player.status === 'Available' : player.status !== 'Available')
    return matchesPosition && matchesAvailability
  })

  return (
    <div className="players-page">
      <PageHeader title="Players" subtitle="Squad roster" />
      <section className="card roster-card">
        <div className="roster-card__header"><div><span>2026/27 Squad</span><h2>Squad Roster</h2><p>{visiblePlayers.length} players shown</p></div></div>
        <div className="roster-toolbar">
          <div className="filter-group" aria-label="Filter by position">{positionGroups.map((filter) => <button key={filter} type="button" className={positionFilter === filter ? 'filter-button filter-button--active' : 'filter-button'} onClick={() => setPositionFilter(filter)}>{filter}</button>)}</div>
          <div className="availability-filter"><span>Availability</span><select value={availabilityFilter} onChange={(event) => setAvailabilityFilter(event.target.value as (typeof availability)[number])}>{availability.map((filter) => <option key={filter}>{filter}</option>)}</select></div>
        </div>
        <PlayerRosterTable players={visiblePlayers} />
      </section>
    </div>
  )
}
