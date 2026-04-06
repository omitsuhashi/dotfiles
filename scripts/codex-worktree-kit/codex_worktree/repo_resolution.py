from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .config import RepoConfig
from .errors import RepoResolutionError


def resolve_repo_path(
    *,
    root_dir: Path,
    repo_key: str,
    repo_config: RepoConfig,
    env: Mapping[str, str] | None,
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

    if repo_config.required:
        raise RepoResolutionError(
            f"failed to resolve repo '{repo_key}'. "
            f"Checked env {repo_config.repo_env}, discover paths {repo_config.discover}, "
            f"and sibling path '{sibling}'."
        )
    return None


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()
