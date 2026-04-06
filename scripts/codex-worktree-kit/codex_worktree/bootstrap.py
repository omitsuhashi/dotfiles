from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

from .branching import plan_linked_worktree_branch
from .config import AppConfig
from .errors import StepExecutionError
from .git_ops import GitRunner, SubprocessGitRunner
from .repo_resolution import resolve_repo_path
from .symlink_ops import ensure_symlink


CommandRunner = Callable[[list[str], Path], int]


@dataclass(frozen=True)
class BootstrapResult:
    plan: list[str] = field(default_factory=list)
    resolved_repos: dict[str, Path] = field(default_factory=dict)
    link_targets: dict[str, Path] = field(default_factory=dict)


def bootstrap_repository(
    *,
    root_dir: Path,
    config: AppConfig,
    env: Mapping[str, str] | None,
    git: GitRunner | None = None,
    dry_run: bool = False,
    command_runner: CommandRunner | None = None,
) -> BootstrapResult:
    git = git or SubprocessGitRunner()
    command_runner = command_runner or run_step_command
    env = env or {}
    plan: list[str] = []
    resolved_repos: dict[str, Path] = {}
    link_targets: dict[str, Path] = {}

    if config.git.hooks_path:
        result = git.set_hooks_path(root_dir, config.git.hooks_path, dry_run=dry_run)
        plan.append(" ".join(result.args))

    for repo_key, repo_config in config.repos.items():
        repo_path = resolve_repo_path(root_dir=root_dir, repo_key=repo_key, repo_config=repo_config, env=env)
        if repo_path is None:
            continue
        resolved_repos[repo_key] = repo_path
        target_path = repo_path

        if repo_config.linked_worktree_path:
            linked_path = (root_dir / repo_config.linked_worktree_path).resolve()
            target_path = linked_path
            if not linked_path.exists():
                branch_plan = plan_linked_worktree_branch(
                    consumer_root=root_dir,
                    linked_repo=repo_path,
                    strategy=repo_config.branch_strategy,
                    git=git,
                )
                result = git.add_worktree(
                    repo_path,
                    linked_path,
                    branch=branch_plan.branch,
                    create_branch=branch_plan.create_branch,
                    detach=branch_plan.detach,
                    start_point=branch_plan.start_point,
                    dry_run=dry_run,
                )
                plan.append(" ".join(result.args))
            else:
                plan.append(f"reuse existing path {linked_path}")

        link_targets[repo_key] = target_path

    for link in config.links:
        rendered = ensure_symlink(
            link_path=(root_dir / link.path).resolve(),
            target_path=link_targets[link.repo],
            dry_run=dry_run,
        )
        plan.append(rendered)

    for step in config.steps:
        cwd = (root_dir / step.cwd).resolve()
        rendered = f"(cd {cwd} && {' '.join(step.run)})"
        plan.append(rendered)
        if not dry_run:
            returncode = command_runner(step.run, cwd)
            if returncode != 0:
                print(
                    f"step '{step.name}' failed in {cwd} with exit code {returncode}",
                    file=sys.stderr,
                )
                raise StepExecutionError(step_name=step.name, returncode=returncode)

    if dry_run:
        for line in plan:
            print(line)

    return BootstrapResult(plan=plan, resolved_repos=resolved_repos, link_targets=link_targets)


def run_step_command(argv: list[str], cwd: Path) -> int:
    completed = subprocess.run(argv, cwd=cwd, check=False)
    return completed.returncode
