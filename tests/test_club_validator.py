from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("club_validator", ROOT / "validate_club.py")
validator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(validator)


class PublicClubTests(unittest.TestCase):
    def load(self, sport: str):
        return json.loads((ROOT / "fixtures" / f"club-public-{sport}-0.1.json").read_text(encoding="utf-8"))

    def test_basketball_and_multi_roster(self):
        document = self.load("basketball")
        validator.validate_club(document)
        self.assertEqual(len(document["rosters"]), 2)
        self.assertEqual({item["squad_id"] for item in document["rosters"]}, {"harbor-senior"})

    def test_football_without_optional_fields(self):
        validator.validate_club(self.load("football"))

    def test_missing_field_and_version(self):
        document = self.load("football")
        del document["club"]["timezone"]
        with self.assertRaises(Exception):
            validator.validate_club(document)
        document = self.load("football")
        document["schema_version"] = "0.2"
        with self.assertRaises(Exception):
            validator.validate_club(document)

    def test_broken_references_and_fake_result(self):
        document = self.load("basketball")
        broken = copy.deepcopy(document)
        broken["results"][0]["fixture_id"] = "game-002"
        with self.assertRaisesRegex(ValueError, "final fixture"):
            validator.validate_club(broken)
        broken = copy.deepcopy(document)
        broken["rosters"][0]["player_ids"].append("missing")
        with self.assertRaisesRegex(ValueError, "missing reference"):
            validator.validate_club(broken)


if __name__ == "__main__":
    unittest.main()
