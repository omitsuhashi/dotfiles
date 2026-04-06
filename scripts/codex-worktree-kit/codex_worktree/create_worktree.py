from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .config import AppConfig, WorktreeConfig, resolve_worktree_root
from .errors import CodexWorktreeError
from .git_ops import GitRunner, SubprocessGitRunner


@dataclass(frozen=True)
class CreateWorktreeResult:
    path: Path
    plan: list[str]


def resolve_primary_worktree_root(
    *,
    root_dir: Path,
    repo_name: str,
    worktree_config: WorktreeConfig,
    cli_override: Path | None,
    env: Mapping[str, str] | None,
) -> Path:
    config = AppConfig(version=1, worktree=worktree_config)
    resolved = resolve_worktree_root(root_dir=root_dir, config=config, cli_override=cli_override, env=env)
    if worktree_config.default_root is None and not cli_override and not any((env or {}).get(name) for name in worktree_config.default_root_env):
        return (root_dir.parent / ".worktrees" / repo_name).resolve()
    return resolved


def create_primary_worktree(
    *,
    root_dir: Path,
    name: str,
    config: AppConfig,
    worktree_root: Path | None,
    env: Mapping[str, str] | None,
    git: GitRunner | None = None,
    dry_run: bool = False,
) -> CreateWorktreeResult:
    git = git or SubprocessGitRunner()
    if not config.worktree.configured:
        raise CodexWorktreeError(
            "create-worktree requires a [worktree] section in the config; "
            "without it, primary worktree management is treated as external"
        )
    base_root = resolve_primary_worktree_root(
        root_dir=root_dir,
        repo_name=root_dir.name,
        worktree_config=config.worktree,
        cli_override=worktree_root,
        env=env,
    )
    target_path = (base_root / name).resolve()
    if target_path.exists():
        raise CodexWorktreeError(f"worktree path already exists: {target_path}")

    result = git.add_worktree(
        root_dir,
        target_path,
        branch=name,
        create_branch=True,
        start_point="HEAD",
        dry_run=dry_run,
    )
    plan = [" ".join(result.args)]
    return CreateWorktreeResult(path=target_path, plan=plan)
