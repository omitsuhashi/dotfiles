import contextlib
import io
import json
import tempfile
import unittest
from unittest import mock

import fetch_context


class GhApiJsonErrorHandlingTests(unittest.TestCase):
    def test_allow_missing_does_not_swallow_403_permission_error(self):
        with mock.patch.object(
            fetch_context,
            "try_run",
            return_value=(1, "", "gh: HTTP 403: Resource not accessible by integration"),
        ):
            with self.assertRaises(RuntimeError):
                fetch_context.gh_api_json(
                    "/repos/acme/project/issues/1/sub_issues",
                    allow_missing=True,
                )


class FetchSubIssuesRepoResolutionTests(unittest.TestCase):
    def test_uses_sub_issue_repository_when_fetching_issue_details(self):
        calls = []

        def fake_gh_api_json(path, **kwargs):
            self.assertEqual(path, "/repos/acme/main/issues/10/sub_issues")
            return [
                {
                    "number": 11,
                    "repository_url": "https://api.github.com/repos/acme/main",
                    "html_url": "https://github.com/acme/main/issues/11",
                },
                {
                    "number": 21,
                    "repository_url": "https://api.github.com/repos/acme/other",
                    "html_url": "https://github.com/acme/other/issues/21",
                },
            ]

        def fake_fetch_issue(owner, repo, number):
            calls.append((owner, repo, number))
            return {"owner": owner, "repo": repo, "issue_number": number}

        with (
            mock.patch.object(fetch_context, "gh_api_json", side_effect=fake_gh_api_json),
            mock.patch.object(fetch_context, "fetch_issue", side_effect=fake_fetch_issue),
        ):
            result = fetch_context.fetch_sub_issues("acme", "main", 10)

        self.assertEqual(
            calls,
            [
                ("acme", "main", 11),
                ("acme", "other", 21),
            ],
        )
        self.assertEqual(len(result), 2)


class MainModeScopeFilteringTests(unittest.TestCase):
    def test_open_scope_preserves_epic_mode_when_all_sub_issues_are_closed(self):
        issue = {
            "owner": "acme",
            "repo": "main",
            "issue_number": 10,
            "url": "https://github.com/acme/main/issues/10",
            "title": "Target",
            "state": "open",
            "labels": [],
            "milestone": None,
            "assignees": [],
            "body": "",
        }
        closed_sub_issue = {
            "owner": "acme",
            "repo": "main",
            "issue_number": 11,
            "url": "https://github.com/acme/main/issues/11",
            "title": "Closed child",
            "state": "closed",
            "labels": [],
            "milestone": None,
            "assignees": [],
            "body": "",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            argv = ["fetch_context.py", "acme/main#10", "--context-dir", tmpdir]
            with (
                mock.patch("sys.argv", argv),
                mock.patch.object(fetch_context, "fetch_issue", return_value=issue),
                mock.patch.object(fetch_context, "fetch_parent", return_value=None),
                mock.patch.object(fetch_context, "fetch_sub_issues", return_value=[closed_sub_issue]),
                mock.patch.object(
                    fetch_context,
                    "fetch_dependencies",
                    return_value={"blocked_by": [], "blocking": []},
                ),
                mock.patch.object(fetch_context, "heuristic_neighbors", return_value=[]),
                contextlib.redirect_stdout(io.StringIO()) as stdout,
            ):
                fetch_context.main()

            output_path = stdout.getvalue().strip()
            with open(output_path, "r", encoding="utf-8") as fp:
                payload = json.load(fp)

        self.assertEqual(payload["sub_issues"], [])
        self.assertEqual(payload["mode"], "epic")
        self.assertEqual(payload["hierarchy"]["level"], "epic")
        self.assertEqual(payload["hierarchy"]["epic"]["issue_number"], 10)
        self.assertEqual(payload["hierarchy"]["issues"], [])

    def test_epic_hierarchy_contains_issue_units_and_sub_issues(self):
        epic_issue = {
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
        }
        issue_under_epic = {
            "owner": "acme",
            "repo": "main",
            "issue_number": 11,
            "url": "https://github.com/acme/main/issues/11",
            "title": "Issue A",
            "state": "open",
            "labels": [],
            "milestone": None,
            "assignees": [],
            "body": "",
        }
        sub_issue_under_issue = {
            "owner": "acme",
            "repo": "main",
            "issue_number": 12,
            "url": "https://github.com/acme/main/issues/12",
            "title": "Sub-issue A-1",
            "state": "open",
            "labels": [],
            "milestone": None,
            "assignees": [],
            "body": "",
        }

        def fake_fetch_sub_issues(owner, repo, number):
            self.assertEqual((owner, repo), ("acme", "main"))
            if number == 10:
                return [issue_under_epic]
            if number == 11:
                return [sub_issue_under_issue]
            return []

        with tempfile.TemporaryDirectory() as tmpdir:
            argv = ["fetch_context.py", "acme/main#10", "--context-dir", tmpdir]
            with (
                mock.patch("sys.argv", argv),
                mock.patch.object(fetch_context, "fetch_issue", return_value=epic_issue),
                mock.patch.object(fetch_context, "fetch_parent", return_value=None),
                mock.patch.object(fetch_context, "fetch_sub_issues", side_effect=fake_fetch_sub_issues),
                mock.patch.object(
                    fetch_context,
                    "fetch_dependencies",
                    return_value={"blocked_by": [], "blocking": []},
                ),
                mock.patch.object(fetch_context, "heuristic_neighbors", return_value=[]),
                contextlib.redirect_stdout(io.StringIO()) as stdout,
            ):
                fetch_context.main()

            output_path = stdout.getvalue().strip()
            with open(output_path, "r", encoding="utf-8") as fp:
                payload = json.load(fp)

        self.assertEqual(payload["hierarchy"]["level"], "epic")
        self.assertEqual(payload["hierarchy"]["epic"]["issue_number"], 10)
        self.assertEqual(len(payload["hierarchy"]["issues"]), 1)
        first_unit = payload["hierarchy"]["issues"][0]
        self.assertEqual(first_unit["issue"]["issue_number"], 11)
        self.assertEqual([entry["issue_number"] for entry in first_unit["sub_issues"]], [12])

    def test_sub_issue_hierarchy_includes_parent_issue_and_epic(self):
        sub_issue = {
            "owner": "acme",
            "repo": "main",
            "issue_number": 30,
            "url": "https://github.com/acme/main/issues/30",
            "title": "Sub-issue",
            "state": "open",
            "labels": [],
            "milestone": None,
            "assignees": [],
            "body": "",
        }
        parent_issue = {
            "owner": "acme",
            "repo": "main",
            "issue_number": 20,
            "url": "https://github.com/acme/main/issues/20",
            "title": "Issue",
            "state": "open",
            "labels": [],
            "milestone": None,
            "assignees": [],
            "body": "",
        }
        sibling_sub_issue = {
            "owner": "acme",
            "repo": "main",
            "issue_number": 31,
            "url": "https://github.com/acme/main/issues/31",
            "title": "Sibling",
            "state": "open",
            "labels": [],
            "milestone": None,
            "assignees": [],
            "body": "",
        }
        epic_issue = {
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
        }

        def fake_fetch_parent(owner, repo, number):
            self.assertEqual((owner, repo), ("acme", "main"))
            if number == 30:
                return parent_issue
            if number == 20:
                return epic_issue
            return None

        def fake_fetch_sub_issues(owner, repo, number):
            self.assertEqual((owner, repo), ("acme", "main"))
            if number == 30:
                return []
            if number == 20:
                return [sub_issue, sibling_sub_issue]
            return []

        with tempfile.TemporaryDirectory() as tmpdir:
            argv = ["fetch_context.py", "acme/main#30", "--context-dir", tmpdir]
            with (
                mock.patch("sys.argv", argv),
                mock.patch.object(fetch_context, "fetch_issue", return_value=sub_issue),
                mock.patch.object(fetch_context, "fetch_parent", side_effect=fake_fetch_parent),
                mock.patch.object(fetch_context, "fetch_sub_issues", side_effect=fake_fetch_sub_issues),
                mock.patch.object(
                    fetch_context,
                    "fetch_dependencies",
                    return_value={"blocked_by": [], "blocking": []},
                ),
                mock.patch.object(fetch_context, "heuristic_neighbors", return_value=[]),
                contextlib.redirect_stdout(io.StringIO()) as stdout,
            ):
                fetch_context.main()

            output_path = stdout.getvalue().strip()
            with open(output_path, "r", encoding="utf-8") as fp:
                payload = json.load(fp)

        self.assertEqual(payload["mode"], "sub_issue")
        self.assertEqual(payload["hierarchy"]["level"], "sub_issue")
        self.assertEqual(payload["hierarchy"]["epic"]["issue_number"], 10)
        self.assertEqual(payload["hierarchy"]["issues"][0]["issue"]["issue_number"], 20)
        sub_issue_numbers = [
            entry["issue_number"] for entry in payload["hierarchy"]["issues"][0]["sub_issues"]
        ]
        self.assertEqual(sub_issue_numbers, [30, 31])
        self.assertEqual([entry["issue_number"] for entry in payload["siblings"]], [31])


if __name__ == "__main__":
    unittest.main()
