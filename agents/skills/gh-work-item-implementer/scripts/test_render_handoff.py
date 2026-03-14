import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import render_handoff
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
        "sub_issues": [],
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
                        }
                    ],
                }
            ],
        },
        "siblings": [],
        "dependencies": {"blocked_by": [], "blocking": []},
        "related": {"heuristic_neighbors": []},
    }


class RenderHandoffTests(unittest.TestCase):
    def write_context(self, tmpdir: str) -> str:
        path = Path(tmpdir) / "context.json"
        path.write_text(json.dumps(sample_context()), encoding="utf-8")
        return str(path)

    def init_state(self, context_path: str) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            work_item_state.main(["init", "--context", context_path])
        return stdout.getvalue().strip()

    def read_json(self, path: str) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def test_render_handoff_uses_active_item_resume_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            context_path = self.write_context(tmpdir)
            state_path = self.init_state(context_path)
            work_item_state.main(
                [
                    "annotate",
                    "--state",
                    state_path,
                    "--kind",
                    "sub-issue",
                    "--number",
                    "12",
                    "--objective",
                    "Keep work resumable without chat history",
                    "--constraint",
                    "Use only handoff.md for restart",
                    "--acceptance-criterion",
                    "Next subagent can continue from artifact only",
                    "--assumption",
                    "Issue 11 remains open during sub-issue work",
                    "--dependency",
                    "issue #11 integration follows",
                    "--next-action",
                    "Run verification then checkpoint commit",
                ]
            )
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
                    "implemented",
                    "--base-sha",
                    "aaa111",
                ]
            )

            markdown_out = Path(tmpdir) / "handoff.md"
            json_out = Path(tmpdir) / "handoff.json"
            render_handoff.main(
                [
                    "--context",
                    context_path,
                    "--state",
                    state_path,
                    "--markdown-out",
                    str(markdown_out),
                    "--json-out",
                    str(json_out),
                ]
            )

            payload = self.read_json(str(json_out))
            markdown = markdown_out.read_text(encoding="utf-8")

        self.assertEqual(payload["active_item"]["kind"], "sub-issue")
        self.assertEqual(payload["active_item"]["number"], 12)
        self.assertEqual(
            payload["active_item"]["objective"],
            "Keep work resumable without chat history",
        )
        self.assertEqual(payload["active_item"]["next_action"], "Run verification then checkpoint commit")
        self.assertIn("Active unit: Issue #11 / Sub-issue #12", markdown)
        self.assertIn("Closable kind: sub-issue", markdown)
        self.assertIn("Objective: Keep work resumable without chat history", markdown)
        self.assertIn("Next: Run verification then checkpoint commit", markdown)

    def test_render_handoff_skips_closed_item_and_uses_next_active_item(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            context_path = self.write_context(tmpdir)
            state_path = self.init_state(context_path)
            for status, extra in [
                ("implemented", ["--base-sha", "aaa111"]),
                ("verified", []),
                ("checkpoint_committed", ["--head-sha", "bbb222", "--commit-sha", "bbb222"]),
                ("review_clean", ["--head-sha", "ccc333"]),
                ("closed", []),
            ]:
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
                        status,
                        *extra,
                    ]
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                render_handoff.main(["--context", context_path, "--state", state_path])

        markdown = stdout.getvalue()
        self.assertIn("Active unit: Issue #11", markdown)
        self.assertIn("Closable kind: issue", markdown)
        self.assertNotIn("Sub-issue #12", markdown)
