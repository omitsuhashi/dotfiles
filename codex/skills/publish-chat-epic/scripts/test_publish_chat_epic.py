import importlib.util
import os
import sys
import unittest


MODULE_PATH = os.path.join(os.path.dirname(__file__), "publish_chat_epic.py")
SPEC = importlib.util.spec_from_file_location("publish_chat_epic", MODULE_PATH)
publish_chat_epic = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["publish_chat_epic"] = publish_chat_epic
SPEC.loader.exec_module(publish_chat_epic)


class TestEpicLabels(unittest.TestCase):
    def test_default_epic_added(self) -> None:
        labels = publish_chat_epic.build_epic_labels(
            labels=["bug"], epic_labels=["priority"]
        )
        self.assertEqual(labels, ["bug", "priority", "epic"])

    def test_epic_not_duplicated(self) -> None:
        labels = publish_chat_epic.build_epic_labels(
            labels=["epic", "bug"], epic_labels=["epic"]
        )
        self.assertEqual(labels.count("epic"), 1)


class TestEpicGrouping(unittest.TestCase):
    def test_grouping_multiple_epics(self) -> None:
        text = "\n".join(
            [
                "~~~markdown",
                "# Epic: Alpha",
                "A",
                "~~~",
                "",
                "~~~markdown",
                "# ISSUE-1",
                "B",
                "~~~",
                "",
                "~~~markdown",
                "# Epic: Beta",
                "C",
                "~~~",
                "",
                "~~~markdown",
                "# ISSUE-2",
                "D",
                "~~~",
            ]
        )
        blocks = publish_chat_epic.parse_blocks(text)
        groups = publish_chat_epic.group_epic_blocks(blocks)
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0].epic.title, "Epic: Alpha")
        self.assertEqual([b.title for b in groups[0].subs], ["ISSUE-1"])
        self.assertEqual(groups[1].epic.title, "Epic: Beta")
        self.assertEqual([b.title for b in groups[1].subs], ["ISSUE-2"])

    def test_grouping_fallback_when_no_epic(self) -> None:
        text = "\n".join(
            [
                "~~~markdown",
                "# ISSUE-1",
                "A",
                "~~~",
                "",
                "~~~markdown",
                "# ISSUE-2",
                "B",
                "~~~",
            ]
        )
        blocks = publish_chat_epic.parse_blocks(text)
        groups = publish_chat_epic.group_epic_blocks(blocks)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].epic.title, "ISSUE-1")
        self.assertEqual([b.title for b in groups[0].subs], ["ISSUE-2"])

    def test_grouping_epic_detection_is_case_insensitive(self) -> None:
        text = "\n".join(
            [
                "~~~markdown",
                "# ISSUE-0",
                "A",
                "~~~",
                "",
                "~~~markdown",
                "# ePiC: Gamma",
                "B",
                "~~~",
                "",
                "~~~markdown",
                "# ISSUE-1",
                "C",
                "~~~",
            ]
        )
        blocks = publish_chat_epic.parse_blocks(text)
        groups = publish_chat_epic.group_epic_blocks(blocks)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].epic.title, "ePiC: Gamma")
        self.assertEqual([b.title for b in groups[0].subs], ["ISSUE-1"])


class TestPlanLines(unittest.TestCase):
    def test_build_plan_lines_multiple_epics(self) -> None:
        blocks = [
            publish_chat_epic.Block(internal_index=0, title="Epic: A", body="A\n"),
            publish_chat_epic.Block(internal_index=1, title="ISSUE-1", body="B\n"),
            publish_chat_epic.Block(internal_index=2, title="Epic: B", body="C\n"),
        ]
        groups = publish_chat_epic.group_epic_blocks(blocks)
        lines = publish_chat_epic.build_plan_lines("org/repo", groups)
        self.assertEqual(
            lines,
            [
                "[PLAN] repo=org/repo",
                "[PLAN] epic: Epic: A",
                "[PLAN] sub[1]: ISSUE-1",
                "[PLAN] epic: Epic: B",
            ],
        )


class TestMappingPayload(unittest.TestCase):
    def test_build_mapping_payload_uses_epics_key(self) -> None:
        payload = publish_chat_epic.build_mapping_payload(
            repo="org/repo",
            epics=[
                {
                    "epic": {"title": "Epic: A", "number": 1, "url": "u"},
                    "sub_issues": [],
                }
            ],
        )
        self.assertEqual(payload["repo"], "org/repo")
        self.assertIn("epics", payload)
        self.assertNotIn("epic", payload)


class TestSubissueApiArgs(unittest.TestCase):
    def test_subissue_api_uses_raw_field(self) -> None:
        args = publish_chat_epic.build_subissue_api_args(
            repo="org/repo", parent_number=10, sub_issue_id=123
        )
        self.assertIn("-F", args)
        self.assertNotIn("-f", args)
        self.assertIn("sub_issue_id=123", args)


class TestRunWithRetries(unittest.TestCase):
    def test_run_with_retries_retries_then_succeeds(self) -> None:
        calls = []

        def runner(cmd, check=True):  # type: ignore[no-untyped-def]
            calls.append(cmd)
            if len(calls) < 3:
                raise RuntimeError("fail")
            return "ok"

        publish_chat_epic.run_with_retries(
            ["echo", "ok"],
            attempts=3,
            wait_seconds=0,
            run_fn=runner,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
