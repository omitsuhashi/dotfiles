import io
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from codex_worktree.bootstrap import bootstrap_repository
from codex_worktree.config import parse_config
from codex_worktree.errors import StepExecutionError, SymlinkConflictError
from codex_worktree.git_ops import GitRunner, GitResult
from codex_worktree.symlink_ops import ensure_symlink


class BootstrapPlanTests(unittest.TestCase):
    def test_symlink_collision_raises_for_real_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root_dir = Path(tmp) / "backend"
            root_dir.mkdir()
            (root_dir / ".docs").mkdir()
            target = root_dir / "../docs"

            with self.assertRaises(SymlinkConflictError):
                ensure_symlink(link_path=root_dir / ".docs", target_path=target, dry_run=False)

    def test_bootstrap_dry_run_prints_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root_dir = base / "backend"
            root_dir.mkdir()
            docs_repo = base / "docs-source"
            docs_repo.mkdir()
            (docs_repo / ".git").mkdir()
            config = self._load_config(base)
            git = RecordingGitRunner()

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = bootstrap_repository(
                    root_dir=root_dir,
                    config=config,
                    env={"CODEX_DOCS_REPO": str(docs_repo)},
                    git=git,
                    dry_run=True,
                )

            rendered = stdout.getvalue()
            self.assertIn("git config core.hooksPath .githooks", rendered)
            self.assertIn("git worktree add", rendered)
            self.assertIn("ln -s", rendered)
            self.assertIn("make docs-catalog", rendered)
            self.assertTrue(result.plan)

    def test_step_failure_propagates_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root_dir = base / "backend"
            root_dir.mkdir()
            docs_repo = base / "docs-source"
            docs_repo.mkdir()
            (docs_repo / ".git").mkdir()
            linked_docs = base / "docs"
            linked_docs.mkdir()
            config = self._load_config(base)
            git = RecordingGitRunner(skip_existing_worktree=True)

            with self.assertRaises(StepExecutionError) as ctx:
                bootstrap_repository(
                    root_dir=root_dir,
                    config=config,
                    env={"CODEX_DOCS_REPO": str(docs_repo)},
                    git=git,
                    dry_run=False,
                    command_runner=lambda argv, cwd: 23,
                )

            self.assertEqual(ctx.exception.returncode, 23)
            self.assertEqual(ctx.exception.step_name, "sync-openapi")

    def _load_config(self, base: Path):
        config_path = base / "worktree.toml"
        config_path.write_text(
            textwrap.dedent(
                """
                version = 1

                [git]
                hooks_path = ".githooks"

                [repos.docs]
                repo_env = ["CODEX_DOCS_REPO"]
                discover = [".docs", "../docs", "docs"]
                linked_worktree_path = "../docs"
                branch_strategy = "mirror-current-or-parent"
                required = true

                [[links]]
                path = ".docs"
                repo = "docs"

                [[steps]]
                name = "sync-openapi"
                cwd = "."
                run = ["make", "sync-openapi"]

                [[steps]]
                name = "docs-catalog"
                cwd = ".docs"
                run = ["make", "docs-catalog"]
                """
            ),
            encoding="utf-8",
        )
        return parse_config(config_path)


class RecordingGitRunner(GitRunner):
    def __init__(self, *, skip_existing_worktree: bool = False):
        self.skip_existing_worktree = skip_existing_worktree
        self.commands = []

    def current_branch(self, repo: Path) -> str | None:
        return "feature/docs-sync"

    def is_valid_branch_name(self, name: str) -> bool:
        return True

    def branch_exists(self, repo: Path, branch: str) -> bool:
        return False

    def add_worktree(
        self,
        repo: Path,
        path: Path,
        *,
        branch: str | None = None,
        create_branch: bool = False,
        detach: bool = False,
        start_point: str | None = None,
        dry_run: bool = False,
    ) -> GitResult:
        self.commands.append(
            ("add_worktree", repo, path, branch, create_branch, detach, start_point, dry_run)
        )
        if not dry_run and not self.skip_existing_worktree:
            path.mkdir(parents=True, exist_ok=True)
            (path / ".git").mkdir(exist_ok=True)
        return GitResult(args=["git", "worktree", "add"], returncode=0, stdout=str(path), stderr="")

    def set_hooks_path(self, repo: Path, hooks_path: str, *, dry_run: bool = False) -> GitResult:
        self.commands.append(("set_hooks_path", repo, hooks_path, dry_run))
        return GitResult(args=["git", "config", "core.hooksPath", hooks_path], returncode=0, stdout="", stderr="")


if __name__ == "__main__":
    unittest.main()
