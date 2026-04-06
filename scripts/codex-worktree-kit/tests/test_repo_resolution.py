import os
import tempfile
import textwrap
import unittest
from pathlib import Path

from codex_worktree.config import parse_config
from codex_worktree.errors import RepoResolutionError
from codex_worktree.repo_resolution import resolve_repo_path


class RepoResolutionTests(unittest.TestCase):
    def test_repo_env_takes_precedence_over_discover(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            consumer = base / "backend"
            consumer.mkdir()
            env_repo = base / "docs-env"
            discover_repo = consumer / "docs"
            self._init_repo(env_repo)
            self._init_repo(discover_repo)
            config = self._load_config(base)

            resolved = resolve_repo_path(
                root_dir=consumer,
                repo_key="docs",
                repo_config=config.repos["docs"],
                env={"CODEX_DOCS_REPO": str(env_repo)},
            )

            self.assertEqual(resolved, env_repo.resolve())

    def test_required_repo_missing_raises_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            consumer = base / "backend"
            consumer.mkdir()
            config = self._load_config(base)

            with self.assertRaises(RepoResolutionError):
                resolve_repo_path(
                    root_dir=consumer,
                    repo_key="docs",
                    repo_config=config.repos["docs"],
                    env={},
                )

    def test_sibling_repo_is_used_as_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            consumer = base / "backend"
            sibling = base / "docs"
            consumer.mkdir()
            self._init_repo(sibling)
            config = self._load_config(base)

            resolved = resolve_repo_path(
                root_dir=consumer,
                repo_key="docs",
                repo_config=config.repos["docs"],
                env={},
            )

            self.assertEqual(resolved, sibling.resolve())

    def test_main_worktree_sibling_repo_is_used_for_app_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = base / "smartra"
            main_root = project / "backend"
            docs_repo = project / "docs"
            app_worktree = base / ".codex" / "worktrees" / "0acf" / "backend"
            main_root.mkdir(parents=True)
            app_worktree.mkdir(parents=True)
            self._init_repo(docs_repo)
            config = self._load_config(base)

            resolved = resolve_repo_path(
                root_dir=app_worktree,
                repo_key="docs",
                repo_config=config.repos["docs"],
                env={},
                git_common_dir_resolver=lambda _: main_root / ".git",
            )

            self.assertEqual(resolved, docs_repo.resolve())

    def _load_config(self, base: Path):
        config_path = base / "worktree.toml"
        config_path.write_text(
            textwrap.dedent(
                """
                version = 1

                [repos.docs]
                repo_env = ["CODEX_DOCS_REPO"]
                discover = [".docs", "docs"]
                linked_worktree_path = "../docs"
                branch_strategy = "mirror-current-or-parent"
                required = true
                """
            ),
            encoding="utf-8",
        )
        return parse_config(config_path)

    def _init_repo(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        (path / ".git").mkdir()


if __name__ == "__main__":
    unittest.main()
