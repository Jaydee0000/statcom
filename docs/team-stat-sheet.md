# Team Stat Sheet — Milestone 5

The Team Stat Sheet is available at `/team-stats`. Rows are players with recorded participation; columns are selected backend metric definitions. Filters include team, season, competition, match, and date range.

`GET /team-stats` returns the complete matrix in one response:

- selected definitions and human-readable labels;
- player identity, position, appearances, minutes, values, and incomplete-match count;
- mathematically valid team totals;
- selected match count and incomplete-match count.

The frontend never requests one metric or player at a time. The service selects the match set, bulk-loads match participants and canonical Milestone 4 events, and aggregates in memory using a bounded query pattern.

## Dynamic columns

Select Metrics is populated by `GET /metric-definitions`. Standard definitions and active coach-created skill/tag definitions share the same response shape. Selecting a custom definition sends its stable key to the backend and adds the returned column; no React code change is needed.

Team percentage totals use summed numerators and denominators. They are never an average of player percentages. Unknown minutes remain blank. Values from partly annotated matches are shown with an explicit incomplete warning rather than silently presented as final.

No stat columns or rollups are persisted, and source annotations remain the authoritative records.
