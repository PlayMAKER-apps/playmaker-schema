from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("playmaker_validator", ROOT / "validate.py")
validator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(validator)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads((ROOT / "fixtures" / "tagmaker-project-0.1.json").read_text(encoding="utf-8"))

    def test_fixture(self):
        validator.validate_document(self.document)

    def test_clip_offset(self):
        broken = copy.deepcopy(self.document)
        broken["project"]["events"][1]["global_video_time_ms"] = 100
        with self.assertRaisesRegex(ValueError, "global video time"):
            validator.validate_document(broken)

    def test_missing_event_relation(self):
        broken = copy.deepcopy(self.document)
        broken["project"]["events"][2]["related_event_ids"] = ["missing"]
        with self.assertRaisesRegex(ValueError, "invalid relations"):
            validator.validate_document(broken)

    def test_version(self):
        broken = copy.deepcopy(self.document)
        broken["version"] = "0.2"
        with self.assertRaises(Exception):
            validator.validate_document(broken)


if __name__ == "__main__":
    unittest.main()
