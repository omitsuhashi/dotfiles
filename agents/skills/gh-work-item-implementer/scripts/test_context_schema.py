import json
import unittest
from pathlib import Path


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "assets" / "context.schema.json"
)
WORK_STATE_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "assets" / "work_state.schema.json"
)
SKILL_PATH = Path(__file__).resolve().parents[1] / "SKILL.md"


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

    def test_work_state_schema_requires_resume_metadata(self):
        with open(WORK_STATE_SCHEMA_PATH, "r", encoding="utf-8") as fp:
            payload = json.load(fp)

        item_schema = payload["properties"]["items"]["items"]
        self.assertIn("objective", item_schema["required"])
        self.assertIn("constraints", item_schema["required"])
        self.assertIn("acceptance_criteria", item_schema["required"])
        self.assertIn("assumptions", item_schema["required"])
        self.assertIn("dependencies", item_schema["required"])
        self.assertIn("next_action", item_schema["required"])
        self.assertIn("verification_summary", item_schema["required"])
        self.assertIn("review_summary", item_schema["required"])
        self.assertIn("updated_at", item_schema["required"])

    def test_skill_mentions_handoff_artifacts_and_autonomy_contract(self):
        body = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("## Autonomy Contract", body)
        self.assertIn("<context_dir>/<owner>-<repo>#<num>/handoff.json", body)
        self.assertIn("<context_dir>/<owner>-<repo>#<num>/handoff.md", body)


if __name__ == "__main__":
    unittest.main()
