# Annotation system — Milestones 3–5

Milestone 3 turns the existing Video Analysis workspace into a persistent annotation editor. Milestone 4 reads those records into match analytics without changing the editor or storing duplicate totals.

## Editor workflow

Open or resume a video session, seek with the player, and choose either a point (`Use Current Time`) or range (`Set Start`, seek, `Set End`). The editor displays the selection at tenth-second precision and validates it against the known video duration. Video and match timestamps are separate:

Until the user changes the draft, its default point follows the current playhead. Once a point/range or another editor value is changed, dirty-state tracking fixes that draft in place so later playback does not silently rewrite it.

```text
match_time = video_start_time - video_time_offset + match_time_offset
```

Choose an active skill and the editor renders its ordered backend field definitions. Choose any number of active tags and match participants, assign participant roles, add notes/status, and save. A single aggregate request creates the annotation, tag links, participant links, and custom values in one transaction. Editing replaces that aggregate in one transaction while retaining the annotation ID. Failed saves keep the draft in the editor and expose Retry; repeated clicks are ignored while the request is in flight.

The player timeline maps start to `video_start_time / duration`. Point annotations are narrow markers; ranges use `(video_end_time - video_start_time) / duration` as their visible width. A tag color is preferred, falling back to the StatCom green. Clicking a marker or list row seeks to its start and loads its aggregate into the editor. The compact list includes time, skill/player, tags, status, and “Duplicate here.” Duplication copies classification data but uses the current playhead as a new point timestamp.

Archive is confirmed and sets `deleted_at`; active session lists/timelines exclude archived rows while their child data remains for auditability. `POST /annotations/{id}/restore` is available for administrative recovery. The active session ID is remembered in browser local storage, so a refresh reopens the session and rebuilds annotations from PostgreSQL; explicitly closing the session clears that browser hint without deleting the session.

Analytics uses the same active-row rule: `deleted_at IS NULL` is applied before classification, so archived annotations stop contributing immediately and restored annotations contribute again. Analytics uses the annotation start instant and persisted `match_time` (or the video-offset formula as a fallback). See [match analytics](match-analytics.md) for definitions and attribution rules.

Milestone 5 source responses retain `annotation_id`, `annotation_session_id`, `video_id`, video/match timestamps, skill, tags, outcomes, player, match, and opponent. The frontend links these to `/video-analysis?video={video_id}&annotation={annotation_id}`. Video Analysis opens or resumes the existing session, selects the active annotation, and seeks the original media to `video_start_time`; no duplicate clip is created.

## Participants

`GET /matches/{id}/annotation-context` returns only `match_participants`, joined to player display data, plus the match's home/away teams. An annotation supports no participants, multiple players, the same player in distinct roles, and an explicit unknown participant. Revision `0002` makes the participant player reference nullable so “unknown” remains distinct from an empty participant list. Common UI roles are Player, Passer, Receiver, Defender, and Target; the role text remains extensible.

Player-reference custom fields must reference a match participant. Team-reference fields must reference the current match's home or away team. The server applies these rules even if a client bypasses the React form.

## Validation and atomicity

Aggregate writes lock and validate the session, enforce its match/video pair, validate start/end against video duration, require an active skill, validate all required fields and data types/options, validate active tags, and restrict identified participants to the match context. Only after validation does the service flush the annotation and its children; one commit completes the entire aggregate. Integrity failures roll back everything.

Required text fields treat empty and whitespace-only values as missing in both the editor and API.

Low-level Milestone 1 CRUD endpoints remain for administration and compatibility, but the workspace uses the aggregate endpoints documented below. Consumers creating editor annotations should do the same.

| Method and path | Purpose |
|---|---|
| `GET /annotation-sessions/{id}/annotations` | Active session annotations with tags, participants, and values |
| `POST /annotation-sessions/{id}/annotations` | Atomic annotation create |
| `GET /annotations/{id}/aggregate` | One active annotation aggregate |
| `PATCH /annotations/{id}/aggregate` | Atomic edit without creating another annotation |
| `POST /annotations/{id}/duplicate` | Copy content at explicitly supplied new time |
| `DELETE /annotations/{id}/archive` | Soft-delete from active UI |
| `POST /annotations/{id}/restore` | Restore a soft-deleted annotation |
| `GET /matches/{id}/annotation-context` | Match teams and eligible players |
| `GET/POST /annotation-library/skills` | Read/create skills with fields |
| Existing `GET/POST /tags` | Read/create normalized reusable tags |

## Unsaved changes and shortcuts

Dirty editor state warns before opening another annotation, switching/closing sessions, following an in-app navigation link, or unloading the page. Inline tag/skill panels do not reset the draft. Controls ignore letter/playback shortcuts while typing in a form field.

| Shortcut | Action |
|---|---|
| Space | Play/pause |
| S | Set start to current video time |
| E | Set end to current video time |
| Ctrl/Cmd + S | Save annotation |
| Left/Right arrow | Seek backward/forward two seconds |

## Current boundaries

Authentication/authorization is still not implemented, so the coach/admin distinction cannot yet be enforced server-side and `created_by` is optional. Favorite tags are not stored; recent tag ordering is kept in browser local storage. The offset formula supports continuous footage but not discontinuous time segments. There is no collaborative conflict/version protocol. Generated ratings, advanced reports, recommendations, predictive ML, chatbot, and computer vision are deliberately excluded.
