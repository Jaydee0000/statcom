# Player analytics — Milestone 5

## Endpoints

- `GET /players/summary`: batched roster identity, membership display data, appearances, minutes, recent results, selected metrics, and incomplete-match counts.
- `GET /players/{id}/summary`: profile identity and selected aggregate values.
- `GET /players/{id}/metrics/history`: chronological appearances with opponent, result, participation, coverage, and per-match values.
- `GET /players/{id}/metrics/by-result`: wins, draws, and losses with sample/reviewed counts and observed per-match values.
- `GET /players/{id}/metrics/sources?metric=...`: annotations contributing to one traceable metric.

Filters support season and competition where applicable. Multiple `metrics` query parameters select definitions.

## Aggregation rules

An appearance is a persisted MatchParticipant. Minutes equal `end_minute - start_minute`; if either boundary is missing, that match's minutes are unknown and the combined value remains null. Result is relative to the player's recorded team. Matches without a final score have no result category and are not forced into win/draw/loss.

Result comparison keeps draws. Count metrics are reported as observed per-match values within each group. Ratio metrics retain summed numerators and denominators and are recalculated. The UI explicitly describes comparison, not causation.

## Coverage and traceability

Coverage combines all annotation sessions for a match. All sessions must be reviewed for complete data. No sessions is Not Started; mixed work is In Progress; ready/reviewed work is Ready for Review; all reviewed is Reviewed.

A source item includes the original annotation, session, video, timestamp, skill, tags, outcome, match, opponent, and player. The player profile opens that existing video/session at the annotation timestamp. Source lists do not render or store new clips.
