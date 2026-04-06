from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .bootstrap import bootstrap_repository
from .config import AppConfig, parse_config
from .create_worktree import create_primary_worktree
from .errors import CodexWorktreeError, GitCommandError, StepExecutionError
from .repo_resolution import resolve_repo_path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except StepExecutionError as error:
        return error.returncode
    except GitCommandError as error:
        print(error.stderr.strip() or str(error), file=sys.stderr)
        return error.returncode
    except CodexWorktreeError as error:
        print(str(error), file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-worktree")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap")
    bootstrap.add_argument("--root-dir", required=True)
    bootstrap.add_argument("--config", required=True)
    bootstrap.add_argument("--dry-run", action="store_true")
    bootstrap.set_defaults(func=_cmd_bootstrap)

    create = subparsers.add_parser("create-worktree")
    create.add_argument("name")
    create.add_argument("--root-dir")
    create.add_argument("--worktree-root")
    create.add_argument("--config")
    create.add_argument("--dry-run", action="store_true")
    create.set_defaults(func=_cmd_create_worktree)

    resolve = subparsers.add_parser("resolve-repo")
    resolve.add_argument("--root-dir", required=True)
    resolve.add_argument("--config", required=True)
    resolve.add_argument("--repo-key", required=True)
    resolve.set_defaults(func=_cmd_resolve_repo)

    validate = subparsers.add_parser("validate-config")
    validate.add_argument("--config", required=True)
    validate.set_defaults(func=_cmd_validate_config)
    return parser


def bootstrap_entrypoint() -> int:
    return main(["bootstrap", *sys.argv[1:]])


def create_worktree_entrypoint() -> int:
    return main(["create-worktree", *sys.argv[1:]])


def resolve_repo_entrypoint() -> int:
    return main(["resolve-repo", *sys.argv[1:]])


def validate_config_entrypoint() -> int:
    return main(["validate-config", *sys.argv[1:]])


def _cmd_bootstrap(args: argparse.Namespace) -> int:
    config = parse_config(Path(args.config))
    bootstrap_repository(
        root_dir=Path(args.root_dir).resolve(),
        config=config,
        env=os.environ,
        dry_run=args.dry_run,
    )
    return 0


def _cmd_create_worktree(args: argparse.Namespace) -> int:
    root_dir = Path(args.root_dir).resolve() if args.root_dir else Path.cwd().resolve()
    config = parse_config(_resolve_config_path(root_dir, args.config))
    result = create_primary_worktree(
        root_dir=root_dir,
        name=args.name,
        config=config,
        worktree_root=Path(args.worktree_root).resolve() if args.worktree_root else None,
        env=os.environ,
        dry_run=args.dry_run,
    )
    if args.dry_run:
        for line in result.plan:
            print(line)
    else:
        print(result.path)
    return 0


def _cmd_resolve_repo(args: argparse.Namespace) -> int:
    root_dir = Path(args.root_dir).resolve()
    config = parse_config(Path(args.config))
    repo_config = config.repos.get(args.repo_key)
    if repo_config is None:
        raise CodexWorktreeError(f"unknown repo key: {args.repo_key}")
    resolved = resolve_repo_path(
        root_dir=root_dir,
        repo_key=args.repo_key,
        repo_config=repo_config,
        env=os.environ,
    )
    if resolved is None:
        raise CodexWorktreeError(f"repo '{args.repo_key}' is not configured as required and was not found")
    print(resolved)
    return 0


def _cmd_validate_config(args: argparse.Namespace) -> int:
    config = parse_config(Path(args.config))
    _ = config
    print(f"valid: {args.config}")
    return 0


def _resolve_config_path(root_dir: Path, cli_value: str | None) -> Path:
    if cli_value:
        return Path(cli_value).resolve()
    return (root_dir / ".codex" / "worktree.toml").resolve()
