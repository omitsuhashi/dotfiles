from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .git_ops import GitRunner


@dataclass(frozen=True)
class BranchPlan:
    branch: str | None
    create_branch: bool
    detach: bool
    start_point: str | None


def select_branch_name(*, consumer_root: Path, strategy: str, git: GitRunner) -> str | None:
    if strategy == "detach":
        return None
    if strategy != "mirror-current-or-parent":
        raise ValueError(f"unsupported branch strategy: {strategy}")

    current = git.current_branch(consumer_root)
    if current:
        return current

    candidate = consumer_root.parent.name
    if candidate and git.is_valid_branch_name(candidate):
        return candidate
    return None


def plan_linked_worktree_branch(
    *,
    consumer_root: Path,
    linked_repo: Path,
    strategy: str,
    git: GitRunner,
) -> BranchPlan:
    desired_branch = select_branch_name(consumer_root=consumer_root, strategy=strategy, git=git)
    if desired_branch is None:
        return BranchPlan(branch=None, create_branch=False, detach=True, start_point="HEAD")

    if git.branch_exists(linked_repo, desired_branch):
        return BranchPlan(
            branch=desired_branch,
            create_branch=False,
            detach=False,
            start_point=desired_branch,
        )

    if git.remote_branch_exists(linked_repo, desired_branch):
        return BranchPlan(
            branch=desired_branch,
            create_branch=True,
            detach=False,
            start_point=f"origin/{desired_branch}",
        )

    return BranchPlan(
        branch=desired_branch,
        create_branch=True,
        detach=False,
        start_point="HEAD",
    )
