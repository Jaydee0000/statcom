# Match analytics — Milestone 4

Match analytics is a read-only projection of persisted annotations. No totals are manually entered or stored, and no cross-match historical model is built.

## Endpoints

| Method and path | Purpose |
|---|---|
| `GET /matches/{match_id}/metrics` | Overall match metrics, home/away attribution, player table, breakdowns, timeline, and events |
| `GET /matches/{match_id}/players/{player_id}/metrics` | Role-aware metrics and breakdowns for one participating player |

Both accept `skill_id`, `tag_id`, exact structured `outcome`, `start_time`, `end_time`, `session_id`, `period`, and `bucket_seconds`. The match endpoint also accepts `player_id`. Bucket values are 60, 300, 600, or 900 seconds. Referenced players, skills, tags, and sessions are validated; a player endpoint rejects a real player who did not participate in the match.

Time filters use match seconds, not raw video seconds. Persisted `match_time` is preferred; legacy null values fall back to:

```text
video_start_time - video_time_offset + match_time_offset
```

`start_time` is inclusive and `end_time` is exclusive. Point and range annotations are filtered/bucketed by the annotation start instant, not by range overlap. `period` compares the existing annotation period case-insensitively; no period table was introduced.

## Deterministic classification

Classification normalizes Unicode, capitalization, underscores, and repeated whitespace, then compares exact canonical tokens. Notes and arbitrary text are never examined. This avoids manufacturing statistics through fuzzy matching.

| Metric | Evidence |
|---|---|
| Pass | Exact Pass/Passes/Passing/Progressive Pass skill or tag |
| Completed pass | Pass plus exact structured Outcome/Result value Complete, Completed, Success, or Successful; explicit Completed/Successful Pass tag also works |
| Incomplete pass | Pass plus exact structured Incomplete, Failed, Failure, or Unsuccessful value; explicit pass tag also works |
| Pass completion | `completed / (completed + incomplete) × 100`, rounded to two decimals; `null` when no pass outcomes are decided |
| Progressive pass | Classified pass plus exact Progressive Pass skill/tag |
| Shot | Exact Shot/Shooting/Shot on Target/Goal skill or tag |
| Shot on target | Shot plus exact On Target/Shot on Target/Goal/Scored structured outcome, or explicit Shot on Target/Goal skill/tag |
| Goal | Exact Goal skill/tag, or a shot with exact Goal/Scored structured outcome |
| Assist | Exact Assist skill/tag |
| Tackle | Exact Tackle skill/tag |
| Interception | Exact Interception skill/tag |
| Turnover | Exact Turnover skill/tag |

Unknown or unsupported evidence yields zero. A pass whose outcome is missing still counts as a pass but is excluded from the completion denominator rather than guessed incomplete.

## Attribution and data quality

Player `total_actions` counts each filtered annotation in which the player appears once. Action-specific metrics use roles: Passer, Shooter/Scorer, Assister/Provider, Tackler/Defender, Interceptor/Defender, and Turnover/Loser/Player, with generic Actor/Player/Primary roles accepted. When exactly one identified player exists, that player is the fallback actor. A Receiver or Target in a multi-player event does not receive the actor's pass/shot.

Team attribution first uses an explicit team-reference field named Team, Acting Team, or Possessing Team. Otherwise it resolves the identified actor through `match_participants`. Exactly one resolved team is required. Cross-team ambiguity remains in overall match metrics and increments `ambiguous_team_actions`, but is not assigned to either team.

An explicit null-player participant increments `unknown_participant_actions`; an empty participant list increments `no_player_actions`. Both may contribute to overall match action metrics. Neither contributes to a player's metrics. They contribute to a team only when an explicit supported team reference is present.

Archived annotations are excluded by `deleted_at IS NULL` in the initial query, before filters/classification. Archived tags attached to an active historical annotation still provide classification evidence because the annotation relationship remains valid.

## Response and frontend

The match response contains stable metric keys, applied filters, home/away team blocks, every match participant with player metrics, actions by skill/outcome/player/tag, nonempty timeline buckets, event/video offsets, and unattributed counts. Empty matches return the same shape with zero counts, `null` pass percentage, and empty breakdowns.

The Analytics page consumes this response directly; it does not recalculate match metrics. Clicking a timeline bucket applies its match-time interval as a filter. Event records expose video/session offsets for future deep linking, but Milestone 4 does not change the Milestone 3 session-opening workflow merely to add navigation.

## Limitations

- Classification conventions depend on coaches using the documented exact skills, tags, fields, outcomes, and participant roles.
- Multiple conflicting explicit team references or unresolved multi-team actors remain team-unassigned.
- Metrics are computed on request with no cache; this is appropriate for current match-sized datasets.
- Analytics is per match only. No seasons, historical trends, win/loss modeling, ratings, recommendations, reports, ML, or chatbot features are included.
