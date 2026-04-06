import tempfile
import textwrap
import unittest
from pathlib import Path

from codex_worktree.config import parse_config, resolve_worktree_root
from codex_worktree.errors import ConfigError


class ValidateConfigTests(unittest.TestCase):
    def test_parse_and_validate_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "worktree.toml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    version = 1

                    [git]
                    hooks_path = ".githooks"

                    [worktree]
                    default_root = "../.worktrees/backend"
                    default_root_env = ["CODEX_WORKTREE_ROOT"]

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
                    """
                ),
                encoding="utf-8",
            )

            config = parse_config(config_path)

            self.assertEqual(config.version, 1)
            self.assertEqual(config.git.hooks_path, ".githooks")
            self.assertEqual(config.worktree.default_root, "../.worktrees/backend")
            self.assertEqual(config.repos["docs"].linked_worktree_path, "../docs")
            self.assertEqual(config.links[0].repo, "docs")
            self.assertEqual(config.steps[0].run, ["make", "sync-openapi"])

    def test_invalid_version_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "worktree.toml"
            config_path.write_text("version = 2\n", encoding="utf-8")

            with self.assertRaises(ConfigError):
                parse_config(config_path)

    def test_worktree_root_resolution_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root_dir = Path(tmp) / "backend"
            root_dir.mkdir()
            config_path = Path(tmp) / "worktree.toml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    version = 1

                    [worktree]
                    default_root = "../.worktrees/backend"
                    default_root_env = ["CODEX_WORKTREE_ROOT", "ALT_ROOT"]
                    """
                ),
                encoding="utf-8",
            )
            config = parse_config(config_path)

            explicit = resolve_worktree_root(
                root_dir=root_dir,
                config=config,
                cli_override=Path("/tmp/explicit"),
                env={"CODEX_WORKTREE_ROOT": "/tmp/env"},
            )
            from_env = resolve_worktree_root(
                root_dir=root_dir,
                config=config,
                cli_override=None,
                env={"CODEX_WORKTREE_ROOT": "/tmp/env"},
            )
            from_default = resolve_worktree_root(
                root_dir=root_dir,
                config=config,
                cli_override=None,
                env={},
            )

            self.assertEqual(explicit, Path("/tmp/explicit").resolve())
            self.assertEqual(from_env, Path("/tmp/env").resolve())
            self.assertEqual(from_default, (root_dir / "../.worktrees/backend").resolve())


if __name__ == "__main__":
    unittest.main()
