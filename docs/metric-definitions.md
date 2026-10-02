# Metric definitions — Milestone 5

The backend is the only source of metric meaning. Reporting responses pair values with a catalog entry containing a stable key, human label, display format, aggregation rule, traceability flag, and optional numerator/denominator keys. React uses the label and format; it does not reclassify annotations.

## Standard metrics

Standard event metrics reuse Milestone 4 classification and role-aware actor attribution: actions, pass attempts, completed passes, pass completion, progressive passes, shots, shots on target, goals, assists, tackles, interceptions, and turnovers. Appearances and minutes come from match participation rather than annotations.

Pass completion is a ratio:

```text
sum(completed passes) / sum(completed + incomplete passes) × 100
```

Season, team, and result-group percentages always use these summed components. Player percentages are never averaged and a missing denominator returns null, not zero.

## Dynamic coach metrics

Each active skill is exposed as `skill:<uuid>` and each active tag as `tag:<uuid>`, with its stored human-readable name as the label. A count includes active annotations matching that exact definition and attributes them through the same participant/actor rules. New skills and tags therefore appear in Select Metrics without a React release.

These dynamic definitions are event counts. Numeric/rating custom-field aggregation and per-90 definitions are not part of the Milestone 4 engine and are not claimed as supported in Milestone 5.

## Missing and incomplete data

A measured count is zero only when a participating player has no matching active annotation in the selected match set. Unknown minutes remain null. Match/session coverage is returned separately, so a zero from unfinished annotation work is visibly distinguishable from a reviewed zero.

Archived annotations never contribute. Restoring an annotation makes it contribute again on the next request.
