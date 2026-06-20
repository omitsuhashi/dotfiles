#!/usr/bin/env python3
"""Fail-fast prerequisite check for the grill-to-pr-loop skill."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


REQUIRED_SKILLS = ("grill-with-docs",)
OPTIONAL_SKILLS = ("to-issues", "grill-me", "handoff")


def candidate_roots(extra_roots: list[str]) -> list[Path]:
    roots: list[Path] = []
    for root in extra_roots:
        roots.append(Path(root).expanduser())

    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        roots.append(Path(codex_home).expanduser() / "skills")

    home = Path.home()
    roots.extend(
        [
            home / ".agents" / "skills",
            home / ".codex" / "skills",
            Path.cwd() / ".agents" / "skills",
            Path.cwd() / "agents" / "skills",
        ]
    )

    unique: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        resolved = root.expanduser()
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return unique


def find_skill(skill_name: str, roots: list[Path]) -> Path | None:
    for root in roots:
        skill_file = root / skill_name / "SKILL.md"
        if skill_file.exists():
            return skill_file
    return None


def git_github_remotes() -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "remote", "-v"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []

    if completed.returncode != 0:
        return []

    remotes: list[str] = []
    for line in completed.stdout.splitlines():
        if "github.com" in line:
            remotes.append(line)
    return remotes


def gh_auth_status(gh_path: str | None) -> dict[str, str | int | None]:
    if not gh_path:
        return {
            "status": "not_checked",
            "returncode": None,
            "summary": "gh CLI not found",
        }

    try:
        completed = subprocess.run(
            [gh_path, "auth", "status"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "returncode": None,
            "summary": "gh auth status timed out",
        }
    except OSError as exc:
        return {
            "status": "error",
            "returncode": None,
            "summary": str(exc),
        }

    return {
        "status": "ok" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "summary": "authenticated"
        if completed.returncode == 0
        else "not authenticated or unavailable",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that required skills for grill-to-pr-loop are installed."
    )
    parser.add_argument(
        "--skills-root",
        action="append",
        default=[],
        help="Additional skills root to search. May be repeated.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )
    args = parser.parse_args()

    roots = candidate_roots(args.skills_root)
    required = {name: find_skill(name, roots) for name in REQUIRED_SKILLS}
    optional = {name: find_skill(name, roots) for name in OPTIONAL_SKILLS}
    missing_required = [name for name, path in required.items() if path is None]
    gh_path = shutil.which("gh")
    github = {
        "gh_cli": gh_path,
        "gh_auth_status": gh_auth_status(gh_path),
        "github_remotes": git_github_remotes(),
    }

    result = {
        "ok": not missing_required,
        "checked_roots": [str(path) for path in roots],
        "required": {name: str(path) if path else None for name, path in required.items()},
        "optional": {name: str(path) if path else None for name, path in optional.items()},
        "github_optional": github,
        "missing_required": missing_required,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for name, path in required.items():
            if path:
                print(f"OK required skill: {name} ({path})")
            else:
                print(f"ERROR missing required skill: {name}")
        for name, path in optional.items():
            if path:
                print(f"OK optional skill: {name} ({path})")
            else:
                print(f"WARN missing optional skill: {name}")
        if github["gh_cli"]:
            print(f"OK optional GitHub CLI: {github['gh_cli']}")
        else:
            print("WARN optional GitHub CLI not found: gh")
        auth = github["gh_auth_status"]
        if auth["status"] == "ok":
            print(f"OK optional GitHub auth: {auth['summary']}")
        else:
            print(f"WARN optional GitHub auth: {auth['summary']}")
        if github["github_remotes"]:
            print("OK optional GitHub remote detected")
            for remote in github["github_remotes"]:
                print(f"- {remote}")
        else:
            print("WARN optional GitHub remote not detected in current directory")
        if missing_required:
            print("STOP: install grill-with-docs before using grill-to-pr-loop.")
            print("Checked roots:")
            for root in roots:
                print(f"- {root}")
        else:
            print("PREREQ CHECK PASSED")

    return 2 if missing_required else 0


if __name__ == "__main__":
    sys.exit(main())
