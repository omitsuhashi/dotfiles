from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, Mapping

from .config import RepoConfig
from .errors import RepoResolutionError

GitCommonDirResolver = Callable[[Path], Path | None]


def resolve_repo_path(
    *,
    root_dir: Path,
    repo_key: str,
    repo_config: RepoConfig,
    env: Mapping[str, str] | None,
    git_common_dir_resolver: GitCommonDirResolver | None = None,
) -> Path | None:
    env = env or {}

    for env_name in repo_config.repo_env:
        raw = env.get(env_name)
        if raw:
            candidate = Path(raw).expanduser().resolve()
            if _is_git_repo(candidate):
                return candidate

    for discover_path in repo_config.discover:
        candidate = (root_dir / discover_path).resolve()
        if _is_git_repo(candidate):
            return candidate

    sibling = (root_dir.parent / repo_key).resolve()
    if _is_git_repo(sibling):
        return sibling

    worktree_candidates = _worktree_candidate_paths(
        root_dir=root_dir,
        repo_key=repo_key,
        git_common_dir_resolver=git_common_dir_resolver,
    )
    for candidate in worktree_candidates:
        if _is_git_repo(candidate):
            return candidate

    if repo_config.required:
        raise RepoResolutionError(
            f"failed to resolve repo '{repo_key}'. "
            f"Checked env {repo_config.repo_env}, discover paths {repo_config.discover}, "
            f"sibling path '{sibling}', and worktree-derived paths "
            f"{[str(path) for path in worktree_candidates]}."
        )
    return None


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def _worktree_candidate_paths(
    *,
    root_dir: Path,
    repo_key: str,
    git_common_dir_resolver: GitCommonDirResolver | None,
) -> list[Path]:
    resolver = git_common_dir_resolver or _resolve_git_common_dir
    common_dir = resolver(root_dir)
    if common_dir is None:
        return []

    main_root = common_dir.parent
    return [
        (main_root / f".{repo_key}").resolve(),
        (main_root.parent / repo_key).resolve(),
    ]


def _resolve_git_common_dir(root_dir: Path) -> Path | None:
    completed = subprocess.run(
        ["git", "-C", str(root_dir), "rev-parse", "--git-common-dir"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None

    raw = completed.stdout.strip()
    if not raw:
        return None

    common_dir = Path(raw).expanduser()
    if common_dir.is_absolute():
        return common_dir.resolve()
    return (root_dir / common_dir).resolve()
