#!/usr/bin/env python3
"""Close a GitHub issue-like work item while forbidding Epic closure."""

from __future__ import annotations

import argparse
import subprocess
from typing import Sequence

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
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--number", required=True, type=int)
    parser.add_argument("--comment", default=DEFAULT_COMMENT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
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
