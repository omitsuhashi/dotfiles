import contextlib
import io
import json
import tempfile
import unittest

import work_item_state


def sample_context() -> dict:
    return {
        "target": {
            "raw": "acme/main#10",
            "owner": "acme",
            "repo": "main",
            "issue_number": 10,
            "url": "https://github.com/acme/main/issues/10",
        },
        "mode": "epic",
        "issue": {
            "owner": "acme",
            "repo": "main",
            "issue_number": 10,
            "url": "https://github.com/acme/main/issues/10",
            "title": "Epic",
            "state": "open",
            "labels": [],
            "milestone": None,
            "assignees": [],
            "body": "",
        },
        "parent": None,
        "sub_issues": [
            {
                "owner": "acme",
                "repo": "main",
                "issue_number": 11,
                "url": "https://github.com/acme/main/issues/11",
                "title": "Issue 11",
                "state": "open",
                "labels": [],
                "milestone": None,
                "assignees": [],
                "body": "",
            }
        ],
        "hierarchy": {
            "level": "epic",
            "epic": {
                "owner": "acme",
                "repo": "main",
                "issue_number": 10,
                "url": "https://github.com/acme/main/issues/10",
                "title": "Epic",
                "state": "open",
                "labels": [],
                "milestone": None,
                "assignees": [],
                "body": "",
            },
            "issues": [
                {
                    "issue": {
                        "owner": "acme",
                        "repo": "main",
                        "issue_number": 11,
                        "url": "https://github.com/acme/main/issues/11",
                        "title": "Issue 11",
                        "state": "open",
                        "labels": [],
                        "milestone": None,
                        "assignees": [],
                        "body": "",
                    },
                    "sub_issues": [
                        {
                            "owner": "acme",
                            "repo": "main",
                            "issue_number": 12,
                            "url": "https://github.com/acme/main/issues/12",
                            "title": "Sub 12",
                            "state": "open",
                            "labels": [],
                            "milestone": None,
                            "assignees": [],
                            "body": "",
                        },
                        {
                            "owner": "acme",
                            "repo": "main",
                            "issue_number": 13,
                            "url": "https://github.com/acme/main/issues/13",
                            "title": "Sub 13",
                            "state": "open",
                            "labels": [],
                            "milestone": None,
                            "assignees": [],
                            "body": "",
                        },
                    ],
                }
            ],
        },
        "siblings": [],
        "dependencies": {"blocked_by": [], "blocking": []},
        "related": {"heuristic_neighbors": []},
    }


class WorkItemStateTests(unittest.TestCase):
    def run_main(self, argv: list[str]) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            work_item_state.main(argv)
        return stdout.getvalue().strip()

    def write_context(self, tmpdir: str) -> str:
        path = f"{tmpdir}/context.json"
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(sample_context(), fp)
        return path

    def read_json(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)

    def init_state(self, tmpdir: str) -> str:
        context_path = self.write_context(tmpdir)
        return self.run_main(
            [
                "init",
                "--context",
                context_path,
            ]
        )

    def test_init_creates_ordered_sub_issue_then_issue_work_items(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = self.init_state(tmpdir)
            payload = self.read_json(state_path)

        self.assertEqual(payload["target"]["issue_number"], 10)
        self.assertEqual(
            [(entry["kind"], entry["number"]) for entry in payload["items"]],
            [("sub-issue", 12), ("sub-issue", 13), ("issue", 11)],
        )
        self.assertEqual(payload["items"][0]["status"], "planned")

    def test_show_active_returns_first_non_closed_item(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = self.init_state(tmpdir)
            self.run_main(
                [
                    "advance",
                    "--state",
                    state_path,
                    "--kind",
                    "sub-issue",
                    "--number",
                    "12",
                    "--status",
                    "implemented",
                    "--base-sha",
                    "aaa111",
                ]
            )
            self.run_main(
                [
                    "advance",
                    "--state",
                    state_path,
                    "--kind",
                    "sub-issue",
                    "--number",
                    "12",
                    "--status",
                    "verified",
                ]
            )
            self.run_main(
                [
                    "advance",
                    "--state",
                    state_path,
                    "--kind",
                    "sub-issue",
                    "--number",
                    "12",
                    "--status",
                    "checkpoint_committed",
                    "--head-sha",
                    "bbb222",
                    "--commit-sha",
                    "bbb222",
                ]
            )
            self.run_main(
                [
                    "advance",
                    "--state",
                    state_path,
                    "--kind",
                    "sub-issue",
                    "--number",
                    "12",
                    "--status",
                    "review_clean",
                    "--head-sha",
                    "ccc333",
                ]
            )
            self.run_main(
                [
                    "advance",
                    "--state",
                    state_path,
                    "--kind",
                    "sub-issue",
                    "--number",
                    "12",
                    "--status",
                    "closed",
                    "--closed-at",
                    "2026-03-14T10:00:00Z",
                ]
            )
            stdout = self.run_main(["show-active", "--state", state_path])

        payload = json.loads(stdout)
        self.assertEqual(payload["kind"], "sub-issue")
        self.assertEqual(payload["number"], 13)

    def test_advance_rejects_skipping_required_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = self.init_state(tmpdir)

            with self.assertRaisesRegex(RuntimeError, "Invalid status transition"):
                work_item_state.main(
                    [
                        "advance",
                        "--state",
                        state_path,
                        "--kind",
                        "sub-issue",
                        "--number",
                        "12",
                        "--status",
                        "verified",
                    ]
                )

    def test_assert_closable_rejects_sub_issue_without_review_clean_and_head_sha(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = self.init_state(tmpdir)
            self.run_main(
                [
                    "advance",
                    "--state",
                    state_path,
                    "--kind",
                    "sub-issue",
                    "--number",
                    "12",
                    "--status",
                    "implemented",
                    "--base-sha",
                    "aaa111",
                ]
            )
            self.run_main(
                [
                    "advance",
                    "--state",
                    state_path,
                    "--kind",
                    "sub-issue",
                    "--number",
                    "12",
                    "--status",
                    "verified",
                ]
            )

            with self.assertRaisesRegex(RuntimeError, "review_clean"):
                work_item_state.main(
                    [
                        "assert-closable",
                        "--state",
                        state_path,
                        "--kind",
                        "sub-issue",
                        "--number",
                        "12",
                    ]
                )

    def test_assert_closable_rejects_issue_when_child_sub_issue_not_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = self.init_state(tmpdir)
            self.run_main(
                [
                    "advance",
                    "--state",
                    state_path,
                    "--kind",
                    "issue",
                    "--number",
                    "11",
                    "--status",
                    "implemented",
                    "--base-sha",
                    "aaa111",
                ]
            )
            self.run_main(
                [
                    "advance",
                    "--state",
                    state_path,
                    "--kind",
                    "issue",
                    "--number",
                    "11",
                    "--status",
                    "verified",
                ]
            )
            self.run_main(
                [
                    "advance",
                    "--state",
                    state_path,
                    "--kind",
                    "issue",
                    "--number",
                    "11",
                    "--status",
                    "checkpoint_committed",
                    "--head-sha",
                    "bbb222",
                    "--commit-sha",
                    "bbb222",
                ]
            )
            self.run_main(
                [
                    "advance",
                    "--state",
                    state_path,
                    "--kind",
                    "issue",
                    "--number",
                    "11",
                    "--status",
                    "review_clean",
                    "--head-sha",
                    "ccc333",
                ]
            )

            with self.assertRaisesRegex(RuntimeError, "Child sub-issues are not closed"):
                work_item_state.main(
                    [
                        "assert-closable",
                        "--state",
                        state_path,
                        "--kind",
                        "issue",
                        "--number",
                        "11",
                    ]
                )

    def test_assert_closable_rejects_epic_kind(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = self.init_state(tmpdir)

            with self.assertRaisesRegex(RuntimeError, "Epic closure is not supported"):
                work_item_state.main(
                    [
                        "assert-closable",
                        "--state",
                        state_path,
                        "--kind",
                        "epic",
                        "--number",
                        "10",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
