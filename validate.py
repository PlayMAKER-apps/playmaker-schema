"""Validate PlayMAKER TagMAKER JSON 0.1, including cross-reference invariants."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_PATH = Path(__file__).with_name("tagmaker-project-0.1.schema.json")


def validate_document(document: dict) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(document)
    project = document["project"]
    media = project["media"]
    events = project["events"]
    media_ids = [item["media_id"] for item in media]
    team_ids = [item["id"] for item in project["teams"]]
    player_ids = [item["id"] for item in project["roster"]]
    event_ids = [item["event_id"] for item in events]
    for name, ids in (("media", media_ids), ("team", team_ids),
                      ("player", player_ids), ("event", event_ids)):
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate {name} ID")
    if sum(team.get("is_our_team", False) for team in project["teams"]) > 1:
        raise ValueError("More than one team is marked as our squad")
    for member in project["roster"]:
        if member["team_id"] is not None and member["team_id"] not in team_ids:
            raise ValueError(f"Roster player {member['id']} refers to a missing team")
    media_index = {item["media_id"]: index for index, item in enumerate(media)}
    for event in events:
        identity = event["event_id"]
        if event["match_id"] != project["match_id"] or event["sport"] != project["sport"]:
            raise ValueError(f"Event {identity} has mismatched match or sport")
        if event["source_media_id"] not in media_index:
            raise ValueError(f"Event {identity} refers to missing media")
        if event.get("team_id") is not None and event["team_id"] not in team_ids:
            raise ValueError(f"Event {identity} refers to missing team")
        if event.get("player_id") is not None and event["player_id"] not in player_ids:
            raise ValueError(f"Event {identity} refers to missing player")
        if event["type"] == "substitution" and ("player_out_id" in event.get("attributes", {})
                                                 or "player_in_id" in event.get("attributes", {})):
            outgoing = event["attributes"].get("player_out_id")
            incoming = event["attributes"].get("player_in_id")
            roster = {member["id"]: member for member in project["roster"]}
            if (not isinstance(outgoing, str) or not isinstance(incoming, str)
                    or outgoing == incoming or event.get("player_id") != outgoing
                    or outgoing not in roster or incoming not in roster
                    or roster[outgoing]["team_id"] != event.get("team_id")
                    or roster[incoming]["team_id"] != event.get("team_id")):
                raise ValueError(f"Event {identity} has invalid substitution players")
        if any(other == identity or other not in event_ids for other in event.get("related_event_ids", [])):
            raise ValueError(f"Event {identity} has invalid relations")
        if event["type"] in {"score_snapshot", "score_correction"}:
            if set(event["attributes"]["scores"]) - set(team_ids):
                raise ValueError(f"Event {identity} refers to missing score team")
        previous = media[:media_index[event["source_media_id"]]]
        if all(clip["duration_ms"] is not None for clip in previous):
            expected = sum(clip["duration_ms"] for clip in previous) + event["source_time_ms"]
            if event["global_video_time_ms"] != expected:
                raise ValueError(f"Event {identity} has inconsistent global video time")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python validate.py <tagmaker-export.json>", file=sys.stderr)
        return 2
    try:
        document = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        validate_document(document)
    except Exception as exc:
        print(f"Invalid: {exc}", file=sys.stderr)
        return 1
    print("Valid PlayMAKER TagMAKER JSON 0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
