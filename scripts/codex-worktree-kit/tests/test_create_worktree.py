import tempfile
import unittest
from pathlib import Path

from codex_worktree.branching import select_branch_name
from codex_worktree.config import AppConfig, WorktreeConfig
from codex_worktree.create_worktree import create_primary_worktree
from codex_worktree.create_worktree import resolve_primary_worktree_root
from codex_worktree.errors import CodexWorktreeError, GitCommandError
from codex_worktree.git_ops import GitRunner, GitResult


class FakeGitRunner(GitRunner):
    def __init__(self, *, current_branch=None, valid_branch_names=None, existing_branches=None, worktree_error=None):
        self._current_branch = current_branch
        self._valid_branch_names = valid_branch_names or set()
        self._existing_branches = existing_branches or set()
        self._worktree_error = worktree_error

    def current_branch(self, repo: Path) -> str | None:
        return self._current_branch

    def is_valid_branch_name(self, name: str) -> bool:
        return name in self._valid_branch_names

    def branch_exists(self, repo: Path, branch: str) -> bool:
        return branch in self._existing_branches

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
        if self._worktree_error is not None:
            raise self._worktree_error
        return GitResult(args=["git"], returncode=0, stdout=str(path), stderr="")

    def set_hooks_path(self, repo: Path, hooks_path: str, *, dry_run: bool = False) -> GitResult:
        return GitResult(args=["git"], returncode=0, stdout="", stderr="")


class CreateWorktreeTests(unittest.TestCase):
    def test_branch_strategy_prefers_current_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            consumer = Path(tmp) / "backend"
            consumer.mkdir()
            git = FakeGitRunner(current_branch="feature/docs-sync")

            branch = select_branch_name(
                consumer_root=consumer,
                strategy="mirror-current-or-parent",
                git=git,
            )

            self.assertEqual(branch, "feature/docs-sync")

    def test_branch_strategy_uses_parent_name_when_branch_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            consumer = Path(tmp) / "feature-docs-sync" / "backend"
            consumer.mkdir(parents=True)
            git = FakeGitRunner(valid_branch_names={"feature-docs-sync"})

            branch = select_branch_name(
                consumer_root=consumer,
                strategy="mirror-current-or-parent",
                git=git,
            )

            self.assertEqual(branch, "feature-docs-sync")

    def test_resolve_primary_worktree_root_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root_dir = Path(tmp) / "backend"
            root_dir.mkdir()

            resolved = resolve_primary_worktree_root(
                root_dir=root_dir,
                repo_name="backend",
                worktree_config=WorktreeConfig(default_root=None, default_root_env=[]),
                cli_override=None,
                env={},
            )

            self.assertEqual(resolved, (root_dir.parent / ".worktrees" / "backend").resolve())

    def test_create_worktree_requires_worktree_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root_dir = Path(tmp) / "backend"
            root_dir.mkdir()

            with self.assertRaises(CodexWorktreeError) as ctx:
                create_primary_worktree(
                    root_dir=root_dir,
                    name="feature-x",
                    config=AppConfig(version=1),
                    worktree_root=None,
                    env={},
                    git=FakeGitRunner(),
                    dry_run=True,
                )

            self.assertIn("[worktree]", str(ctx.exception))

    def test_git_failure_is_propagated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            consumer = Path(tmp) / "backend"
            consumer.mkdir()
            git = FakeGitRunner(
                worktree_error=GitCommandError(
                    args=["git", "worktree", "add"],
                    returncode=17,
                    stderr="boom",
                )
            )

            with self.assertRaises(GitCommandError) as ctx:
                git.add_worktree(consumer, consumer / "feature-x", branch="feature-x", create_branch=True)

            self.assertEqual(ctx.exception.returncode, 17)


if __name__ == "__main__":
    unittest.main()
