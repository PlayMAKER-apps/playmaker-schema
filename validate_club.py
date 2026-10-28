"""Validate the distinct public-club contract without changing TagMAKER 0.1."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA = json.loads(Path(__file__).with_name("club-public-0.1.schema.json").read_text(encoding="utf-8"))


def validate_club(document: dict) -> None:
    Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(document)
    ZoneInfo(document["club"]["timezone"])
    collections = {name: document.get(name, []) for name in ("teams", "squads", "competitions", "fixtures", "players", "rosters", "sponsors")}
    ids = {}
    for name, items in collections.items():
        values = [item["id"] for item in items]
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate {name} ID")
        ids[name] = set(values)
    if any(squad["team_id"] not in ids["teams"] for squad in collections["squads"]):
        raise ValueError("Squad refers to missing team")
    for competition in collections["competitions"]:
        if set(competition["squad_ids"]) - ids["squads"]:
            raise ValueError("Competition refers to missing squad")
    for fixture in collections["fixtures"]:
        if fixture["competition_id"] not in ids["competitions"] or fixture["home_team_id"] not in ids["teams"] or fixture["away_team_id"] not in ids["teams"]:
            raise ValueError("Fixture refers to missing competition or team")
        if fixture["home_team_id"] == fixture["away_team_id"]:
            raise ValueError("Fixture home and away teams must differ")
    fixture_by_id = {item["id"]: item for item in collections["fixtures"]}
    result_ids = [item["fixture_id"] for item in document["results"]]
    if len(result_ids) != len(set(result_ids)):
        raise ValueError("Duplicate result fixture ID")
    for result in document["results"]:
        if result["fixture_id"] not in fixture_by_id or fixture_by_id[result["fixture_id"]]["status"] != "final":
            raise ValueError("Result needs a final fixture")
    for roster in collections["rosters"]:
        if roster["squad_id"] not in ids["squads"] or roster["competition_id"] not in ids["competitions"] or set(roster["player_ids"]) - ids["players"]:
            raise ValueError("Roster has a missing reference")
    for stat in document.get("player_stats", []):
        if stat["fixture_id"] not in fixture_by_id or stat["player_id"] not in ids["players"]:
            raise ValueError("Player stat has a missing reference")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python validate_club.py <public-club.json>", file=sys.stderr)
        return 2
    try:
        validate_club(json.loads(Path(argv[1]).read_text(encoding="utf-8")))
    except Exception as exc:
        print(f"Invalid public club data: {exc}", file=sys.stderr)
        return 1
    print("Valid PlayMAKER public club data 0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
