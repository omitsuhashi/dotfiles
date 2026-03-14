#!/usr/bin/env python3
"""Close a GitHub issue-like work item while forbidding Epic closure."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Sequence

import work_item_state

DEFAULT_COMMENT = "Implemented and verified in this task."


def run(cmd: Sequence[str]) -> str:
    proc = subprocess.run(
        list(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}"
            + (f"\n{stderr}" if stderr else "")
        )
    return proc.stdout


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Close an issue or sub-issue while forbidding Epic closure."
    )
    parser.add_argument("--kind", choices=["issue", "sub-issue"], required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--number", required=True, type=int)
    parser.add_argument("--comment", default=DEFAULT_COMMENT)
    return parser.parse_args(argv)


def assert_closable(state_path: str, kind: str, number: int) -> None:
    payload = work_item_state.load_state(Path(state_path))
    work_item_state.assert_closable(payload, kind, number)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    assert_closable(args.state, args.kind, args.number)
    output = run(
        [
            "gh",
            "issue",
            "close",
            str(args.number),
            "--repo",
            args.repo,
            "--comment",
            args.comment,
        ]
    )
    if output:
        print(output, end="")


if __name__ == "__main__":
    main()
