from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .errors import ConfigError


SUPPORTED_BRANCH_STRATEGIES = {"mirror-current-or-parent", "detach"}


@dataclass(frozen=True)
class GitConfig:
    hooks_path: str | None = None


@dataclass(frozen=True)
class WorktreeConfig:
    configured: bool = False
    default_root: str | None = None
    default_root_env: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RepoConfig:
    repo_env: list[str] = field(default_factory=list)
    discover: list[str] = field(default_factory=list)
    linked_worktree_path: str | None = None
    branch_strategy: str = "detach"
    required: bool = False


@dataclass(frozen=True)
class LinkConfig:
    path: str
    repo: str


@dataclass(frozen=True)
class StepConfig:
    name: str
    cwd: str
    run: list[str]


@dataclass(frozen=True)
class AppConfig:
    version: int
    git: GitConfig = field(default_factory=GitConfig)
    worktree: WorktreeConfig = field(default_factory=WorktreeConfig)
    repos: dict[str, RepoConfig] = field(default_factory=dict)
    links: list[LinkConfig] = field(default_factory=list)
    steps: list[StepConfig] = field(default_factory=list)


def parse_config(path: Path) -> AppConfig:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    worktree_data = data.get("worktree", {})
    config = AppConfig(
        version=_require_int(data, "version"),
        git=_parse_git_config(data.get("git", {})),
        worktree=_parse_worktree_config(worktree_data, configured="worktree" in data),
        repos=_parse_repos(data.get("repos", {})),
        links=_parse_links(data.get("links", [])),
        steps=_parse_steps(data.get("steps", [])),
    )
    validate_config(config)
    return config


def validate_config(config: AppConfig) -> None:
    if config.version != 1:
        raise ConfigError(f"unsupported config version: {config.version}")

    for repo_key, repo_config in config.repos.items():
        if repo_config.branch_strategy not in SUPPORTED_BRANCH_STRATEGIES:
            raise ConfigError(
                f"repos.{repo_key}.branch_strategy must be one of "
                f"{sorted(SUPPORTED_BRANCH_STRATEGIES)}"
            )

    for link in config.links:
        if link.repo not in config.repos:
            raise ConfigError(f"links.path '{link.path}' references unknown repo '{link.repo}'")

    for step in config.steps:
        if not step.run:
            raise ConfigError(f"step '{step.name}' must define a non-empty run array")


def resolve_worktree_root(
    *,
    root_dir: Path,
    config: AppConfig,
    cli_override: Path | None,
    env: Mapping[str, str] | None,
) -> Path:
    if cli_override is not None:
        return cli_override.expanduser().resolve()

    env = env or {}
    for env_name in config.worktree.default_root_env:
        value = env.get(env_name)
        if value:
            return Path(value).expanduser().resolve()

    if config.worktree.default_root:
        default_root = Path(config.worktree.default_root).expanduser()
        if default_root.is_absolute():
            return default_root.resolve()
        return (root_dir / default_root).resolve()

    repo_name = root_dir.name
    return (root_dir.parent / ".worktrees" / repo_name).resolve()


def _parse_git_config(data: Any) -> GitConfig:
    _require_table(data, "git")
    hooks_path = data.get("hooks_path")
    if hooks_path is not None and not isinstance(hooks_path, str):
        raise ConfigError("git.hooks_path must be a string")
    return GitConfig(hooks_path=hooks_path)


def _parse_worktree_config(data: Any, *, configured: bool) -> WorktreeConfig:
    _require_table(data, "worktree")
    default_root = data.get("default_root")
    default_root_env = _require_str_list(data.get("default_root_env", []), "worktree.default_root_env")
    if default_root is not None and not isinstance(default_root, str):
        raise ConfigError("worktree.default_root must be a string")
    return WorktreeConfig(
        configured=configured,
        default_root=default_root,
        default_root_env=default_root_env,
    )


def _parse_repos(data: Any) -> dict[str, RepoConfig]:
    _require_table(data, "repos")
    repos: dict[str, RepoConfig] = {}
    for repo_key, repo_data in data.items():
        _require_table(repo_data, f"repos.{repo_key}")
        branch_strategy = repo_data.get("branch_strategy", "detach")
        if not isinstance(branch_strategy, str):
            raise ConfigError(f"repos.{repo_key}.branch_strategy must be a string")
        repos[repo_key] = RepoConfig(
            repo_env=_require_str_list(repo_data.get("repo_env", []), f"repos.{repo_key}.repo_env"),
            discover=_require_str_list(repo_data.get("discover", []), f"repos.{repo_key}.discover"),
            linked_worktree_path=_optional_str(
                repo_data.get("linked_worktree_path"),
                f"repos.{repo_key}.linked_worktree_path",
            ),
            branch_strategy=branch_strategy,
            required=_optional_bool(repo_data.get("required", False), f"repos.{repo_key}.required"),
        )
    return repos


def _parse_links(data: Any) -> list[LinkConfig]:
    if not isinstance(data, list):
        raise ConfigError("links must be an array of tables")
    links: list[LinkConfig] = []
    for index, item in enumerate(data):
        _require_table(item, f"links[{index}]")
        links.append(
            LinkConfig(
                path=_require_str(item, "path", f"links[{index}].path"),
                repo=_require_str(item, "repo", f"links[{index}].repo"),
            )
        )
    return links


def _parse_steps(data: Any) -> list[StepConfig]:
    if not isinstance(data, list):
        raise ConfigError("steps must be an array of tables")
    steps: list[StepConfig] = []
    for index, item in enumerate(data):
        _require_table(item, f"steps[{index}]")
        steps.append(
            StepConfig(
                name=_require_str(item, "name", f"steps[{index}].name"),
                cwd=_require_str(item, "cwd", f"steps[{index}].cwd"),
                run=_require_str_list(item.get("run", []), f"steps[{index}].run"),
            )
        )
    return steps


def _require_int(data: Mapping[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise ConfigError(f"{key} must be an integer")
    return value


def _require_table(value: Any, key: str) -> None:
    if not isinstance(value, dict):
        raise ConfigError(f"{key} must be a table")


def _require_str(data: Mapping[str, Any], key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{label} must be a non-empty string")
    return value


def _require_str_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ConfigError(f"{label} must be an array of non-empty strings")
    return list(value)


def _optional_str(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{label} must be a non-empty string")
    return value


def _optional_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{label} must be a boolean")
    return value
