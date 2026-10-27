# PlayMAKER interchange contract

Version **0.1** freezes the JSON document currently exported by TagMAKER. It is
the input contract for VideoMAKER; VideoMAKER development can start against
[`tagmaker-project-0.1.schema.json`](tagmaker-project-0.1.schema.json) and the
synthetic [fixture](fixtures/tagmaker-project-0.1.json). This folder is the
contract source of truth. A consumer must reject unknown major or minor
versions until it explicitly supports them.

Install `requirements.txt` and run `python validate.py export.json` to check
the schema plus IDs, references, and sequential timeline arithmetic. The
fixture is a passing example. Consumers may implement the same checks in
their own language.

## Timeline and media

- `project.media` is an **ordered sequence of consecutive clips**, not camera
  angles synchronized to one timebase. `media_id` stays stable within a match.
- Media paths are relative to the JSON file when possible. The JSON never
  contains media bytes. Resolve a relative path from the export file's parent.
- All times are integer milliseconds. An event's `source_media_id` and
  `source_time_ms` identify its clip location. `global_video_time_ms` is the
  sum of the durations of preceding clips plus `source_time_ms`. Durations may
  be null before probing; consumers should then use the source location.
- `timestamp_quality: "player-reported-ms"` means a rounded player position,
  not a frame number. On variable frame rate media, VideoMAKER should seek to
  the timestamp and inspect the decoded frame; it must not multiply by FPS.
- `game_clock_ms` is independent of video time and can be null. `clock_direction`
  is `up`, `down`, or null. Period labels come from the embedded sport profile.

## Event and score rules

- `event_id`, `match_id`, team/player IDs, and media IDs are stable strings.
  VideoMAKER should keep `event_id` in generated clips or overlays so edits can
  be traced back to the source tag.
- `type` names are defined by `project.profile_data.events`. Consumers should
  preserve unknown event types and `attributes`; they need not render them.
- `related_event_ids` are other events in the same match. Their order does not
  imply playback order; sort by `global_video_time_ms` and then original array
  order when needed.
- `score_snapshot` and `score_correction` carry authoritative per-team totals in
  `attributes.scores`. They are not scoring plays. A partial tagging session
  cannot be treated as a complete final score merely by summing `points`.
- WebMAKER source identities on roster members use `webmaker_player_id` and
  `webmaker_team_id`; TagMAKER event `player_id` is its own stable ID.
- At most one team may set optional `is_our_team: true`. TagMAKER presents that
  team's called-up players individually and the other teams as team-level
  choices. This affects the tagging UI, not event attribution: an opponent
  event has its `team_id` and a null `player_id`.
- A basketball roster member may set `starter: true` for the starting five.
  A completed `substitution` event keeps the outgoing player in `player_id`
  and records both `attributes.player_out_id` and `attributes.player_in_id`.
  Those IDs must be different players on `team_id`. Older one-player
  substitution events remain readable but cannot establish who entered.

## Compatibility policy

TagMAKER exports `format: "tagmaker-project"` and `version: "0.1"`; the file's
`project` object is defined by the schema. The `team` and `rosterMember`
objects are extensible; consumers should ignore unknown metadata there. New
top-level project or event keys require a version change and fixture.
Renaming, removing, or changing meanings requires a new major version.
VideoMAKER should use the fixture for importer and round-trip
tests, including clip boundaries, missing game clock, and score corrections.
SQLite is TagMAKER's local autosave format, not the suite contract.

The WebMAKER Studio CSV is a separate, per-game reporting format. It cannot
represent the event timeline; see TagMAKER's WebMAKER export documentation.
