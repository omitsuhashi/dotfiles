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


if __name__ == "__main__":
    unittest.main()
