from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import GitCommandError


@dataclass(frozen=True)
class GitResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str


class GitRunner:
    def current_branch(self, repo: Path) -> str | None:
        raise NotImplementedError

    def is_valid_branch_name(self, name: str) -> bool:
        raise NotImplementedError

    def branch_exists(self, repo: Path, branch: str) -> bool:
        raise NotImplementedError

    def remote_branch_exists(self, repo: Path, branch: str) -> bool:
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
        raise NotImplementedError

    def set_hooks_path(self, repo: Path, hooks_path: str, *, dry_run: bool = False) -> GitResult:
        raise NotImplementedError


class SubprocessGitRunner(GitRunner):
    def current_branch(self, repo: Path) -> str | None:
        result = self._run(["git", "-C", str(repo), "branch", "--show-current"])
        branch = result.stdout.strip()
        return branch or None

    def is_valid_branch_name(self, name: str) -> bool:
        completed = subprocess.run(
            ["git", "check-ref-format", "--branch", name],
            check=False,
            capture_output=True,
            text=True,
        )
        return completed.returncode == 0

    def branch_exists(self, repo: Path, branch: str) -> bool:
        completed = subprocess.run(
            ["git", "-C", str(repo), "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
            check=False,
            capture_output=True,
            text=True,
        )
        return completed.returncode == 0

    def remote_branch_exists(self, repo: Path, branch: str) -> bool:
        completed = subprocess.run(
            ["git", "-C", str(repo), "ls-remote", "--exit-code", "--heads", "origin", branch],
            check=False,
            capture_output=True,
            text=True,
        )
        return completed.returncode == 0

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
        args = ["git", "-C", str(repo), "worktree", "add"]
        if detach:
            args.append("--detach")
        if create_branch and branch:
            args.extend(["-b", branch])
        args.append(str(path))
        if not detach:
            args.append(start_point or branch or "HEAD")
        if dry_run:
            return GitResult(args=args, returncode=0, stdout="", stderr="")
        return self._run(args)

    def set_hooks_path(self, repo: Path, hooks_path: str, *, dry_run: bool = False) -> GitResult:
        args = ["git", "-C", str(repo), "config", "core.hooksPath", hooks_path]
        if dry_run:
            return GitResult(args=args, returncode=0, stdout="", stderr="")
        return self._run(args)

    def _run(self, args: list[str]) -> GitResult:
        completed = subprocess.run(args, check=False, capture_output=True, text=True)
        result = GitResult(
            args=args,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        if completed.returncode != 0:
            raise GitCommandError(args=args, returncode=completed.returncode, stderr=completed.stderr)
        return result
