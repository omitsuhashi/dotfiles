import json
import unittest
from pathlib import Path


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "assets" / "context.schema.json"
)
WORK_STATE_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "assets" / "work_state.schema.json"
)


class ContextSchemaTests(unittest.TestCase):
    def test_mode_enum_includes_all_runtime_modes(self):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as fp:
            payload = json.load(fp)

        self.assertEqual(
            payload["properties"]["mode"]["enum"],
            ["epic", "issue", "sub_issue", "standalone_issue"],
        )

    def test_work_state_schema_defines_lifecycle_statuses(self):
        with open(WORK_STATE_SCHEMA_PATH, "r", encoding="utf-8") as fp:
            payload = json.load(fp)

        item_schema = payload["properties"]["items"]["items"]["properties"]
        self.assertEqual(
            item_schema["status"]["enum"],
            [
                "planned",
                "implemented",
                "verified",
                "checkpoint_committed",
                "review_clean",
                "closed",
            ],
        )


if __name__ == "__main__":
    unittest.main()
