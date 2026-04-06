from __future__ import annotations


class CodexWorktreeError(Exception):
    """Base error for codex worktree kit."""


class ConfigError(CodexWorktreeError):
    """Raised when the config file is invalid."""


class RepoResolutionError(CodexWorktreeError):
    """Raised when a configured repository cannot be resolved."""


class SymlinkConflictError(CodexWorktreeError):
    """Raised when a symlink target collides with a non-symlink path."""


class GitCommandError(CodexWorktreeError):
    """Raised when a git command fails."""

    def __init__(self, *, args: list[str], returncode: int, stderr: str) -> None:
        self.args = args
        self.returncode = returncode
        self.stderr = stderr
        message = stderr.strip() or f"git command failed with exit code {returncode}"
        super().__init__(message)


class StepExecutionError(CodexWorktreeError):
    """Raised when a post-setup step fails."""

    def __init__(self, *, step_name: str, returncode: int) -> None:
        self.step_name = step_name
        self.returncode = returncode
        super().__init__(f"step '{step_name}' failed with exit code {returncode}")
