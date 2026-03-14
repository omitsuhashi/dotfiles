import contextlib
import io
import unittest
from unittest import mock

import close_work_item


class CloseWorkItemTests(unittest.TestCase):
    def test_rejects_epic_kind(self):
        stderr = io.StringIO()
        with (
            self.assertRaises(SystemExit) as exc,
            contextlib.redirect_stderr(stderr),
        ):
            close_work_item.main(
                [
                    "--kind",
                    "epic",
                    "--repo",
                    "acme/project",
                    "--number",
                    "10",
                ]
            )

        self.assertEqual(exc.exception.code, 2)
        self.assertIn("invalid choice", stderr.getvalue())

    def test_closes_issue(self):
        with (
            mock.patch.object(close_work_item, "run", return_value="") as run_mock,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            close_work_item.main(
                [
                    "--kind",
                    "issue",
                    "--repo",
                    "acme/project",
                    "--number",
                    "11",
                ]
            )

        run_mock.assert_called_once_with(
            [
                "gh",
                "issue",
                "close",
                "11",
                "--repo",
                "acme/project",
                "--comment",
                "Implemented and verified in this task.",
            ]
        )

    def test_closes_sub_issue(self):
        with (
            mock.patch.object(close_work_item, "run", return_value="") as run_mock,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            close_work_item.main(
                [
                    "--kind",
                    "sub-issue",
                    "--repo",
                    "acme/project",
                    "--number",
                    "12",
                ]
            )

        run_mock.assert_called_once_with(
            [
                "gh",
                "issue",
                "close",
                "12",
                "--repo",
                "acme/project",
                "--comment",
                "Implemented and verified in this task.",
            ]
        )


if __name__ == "__main__":
    unittest.main()
