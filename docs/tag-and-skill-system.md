# Tag and skill system

Tags describe an event; skills define the structured data collected for it. Both are reusable stable-ID records and neither creates a new database column when a coach expands the library.

## Tags

The editor loads active global tags from `GET /tags?is_active=true`, supports name/description search and category filtering, and places recently used tags first. Multiple tags can be attached to an annotation. A tag may be created inline with name, description, category, and optional hex color; the draft's time, participants, fields, and notes stay intact, and the returned tag is selected immediately.

Recent tag IDs are a browser-local convenience rather than domain data. They update immediately after a successful annotation save and fall back to an empty list if local storage is missing or malformed.

Names are Unicode NFKC-normalized, case-folded, trimmed, and whitespace-collapsed into `normalized_name`. `(scope, normalized_name)` is unique, including archived rows. Thus `Progressive Pass`, ` progressive  pass `, and capitalization variants cannot become duplicates. Archiving preserves existing annotation links; archived tags cannot be newly attached.

## Skills and fields

`SkillDefinition` holds name, category, description, active state, and version. `SkillFieldDefinition` rows supply ordered field keys, labels, required flags, descriptions, types, and select options. The inline skill creator sends the definition and all fields to one transactional endpoint; the new skill is immediately selected. No schema migration is required.

Supported controls and persisted JSON values are:

| Type | UI / value |
|---|---|
| `boolean` | Checkbox / JSON boolean |
| `number` | Numeric input / finite number |
| `rating` | Numeric rating input (UI suggests 1–5) / finite number |
| `single_select` | Select / one configured option |
| `multi_select` | Multi-select / unique configured options |
| `text` | Text area / string |
| `player_reference` | Current-match player select / player UUID plus restrictive FK |
| `team_reference` | Home/away team select / team UUID plus restrictive FK |

Select definitions require nonempty unique options. Other types reject options. Annotation values must belong to the selected skill and required values must be present on aggregate saves. Reference types are further restricted to the annotation's match context.

Used skill structure is historically protected by the Milestone 1 rules. Create a new version rather than changing the key/type/options/required semantics of a used skill. Archiving prevents new use but retains old annotations.

## Example

A `Pass` skill can define required `Outcome` (`Completed`, `Incomplete`) plus optional `Recipient`, `Direction`, and `Distance`. `Scanning Before Receiving` can define required `Observed` (`Yes`, `No`, `Unclear`) and optional `Rating`. These definitions produce their controls through the same React dispatcher; neither skill name nor its fields are hardcoded into the annotation form.
