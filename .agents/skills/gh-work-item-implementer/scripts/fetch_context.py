#!/usr/bin/env python3
"""Fetch deterministic GitHub Issue context for implementation workflows."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

API_VERSION = "2022-11-28"
ACCEPT = "application/vnd.github+json"


@dataclass
class Target:
    raw: str
    owner: str
    repo: str
    issue_number: int
    url: str


def run(cmd: Sequence[str]) -> str:
    try:
        proc = subprocess.run(
            list(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Command not found: {cmd[0]}") from exc

    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}"
            + (f"\n{stderr}" if stderr else "")
        )
    return proc.stdout


def try_run(cmd: Sequence[str]) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            list(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    return proc.returncode, proc.stdout, proc.stderr


def parse_owner_repo_from_git_remote() -> Optional[Tuple[str, str]]:
    code, out, _ = try_run(["git", "config", "--get", "remote.origin.url"])
    if code != 0:
        return None

    url = out.strip()
    patterns = [
        r"^git@[^:]+:([^/]+)/(.+?)(?:\.git)?$",
        r"^https?://[^/]+/([^/]+)/(.+?)(?:\.git)?$",
        r"^ssh://[^/]+/([^/]+)/(.+?)(?:\.git)?$",
        r"^git://[^/]+/([^/]+)/(.+?)(?:\.git)?$",
    ]

    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            return match.group(1), match.group(2)
    return None


def parse_target(raw: str) -> Tuple[Optional[Tuple[str, str]], int]:
    text = raw.strip()

    match = re.match(r"^https?://github\.com/([^/]+)/([^/]+)/issues/(\d+)(?:/.*)?$", text)
    if match:
        return (match.group(1), match.group(2)), int(match.group(3))

    match = re.match(r"^([^/\s]+)/([^#\s]+)#(\d+)$", text)
    if match:
        return (match.group(1), match.group(2)), int(match.group(3))

    match = re.match(r"^#?(\d+)$", text)
    if match:
        return None, int(match.group(1))

    raise ValueError(f"Unsupported target format: {raw}")


def _is_not_found(stderr: str) -> bool:
    normalized = stderr.lower()
    tokens = [
        "http 404",
        "http 410",
        "not found",
        "gone",
        "resource not accessible",
    ]
    return any(token in normalized for token in tokens)


def gh_api_json(
    path: str,
    *,
    method: str = "GET",
    fields: Optional[Dict[str, Any]] = None,
    allow_missing: bool = False,
) -> Optional[Any]:
    cmd: List[str] = [
        "gh",
        "api",
        path,
        "-X",
        method,
        "-H",
        f"Accept: {ACCEPT}",
        "-H",
        f"X-GitHub-Api-Version: {API_VERSION}",
    ]
    if fields:
        for key, value in fields.items():
            cmd.extend(["-f", f"{key}={value}"])

    code, out, err = try_run(cmd)
    if code != 0:
        if allow_missing and _is_not_found(err):
            return None
        stderr = err.strip()
        raise RuntimeError(
            f"Command failed ({code}): {' '.join(cmd)}"
            + (f"\n{stderr}" if stderr else "")
        )

    payload = out.strip()
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to decode JSON from gh api response for path: {path}") from exc


def _parse_owner_repo_from_api_urls(
    default_owner: str,
    default_repo: str,
    issue_obj: Dict[str, Any],
) -> Tuple[str, str]:
    repository_url = issue_obj.get("repository_url")
    if isinstance(repository_url, str):
        match = re.match(r"^https?://api\.github\.com/repos/([^/]+)/([^/]+)$", repository_url)
        if match:
            return match.group(1), match.group(2)

    html_url = issue_obj.get("html_url")
    if isinstance(html_url, str):
        match = re.match(r"^https?://github\.com/([^/]+)/([^/]+)/issues/\d+", html_url)
        if match:
            return match.group(1), match.group(2)

    return default_owner, default_repo


def normalize_issue(default_owner: str, default_repo: str, issue_obj: Dict[str, Any]) -> Dict[str, Any]:
    owner, repo = _parse_owner_repo_from_api_urls(default_owner, default_repo, issue_obj)

    labels = []
    for raw_label in issue_obj.get("labels", []):
        if isinstance(raw_label, dict):
            name = raw_label.get("name")
            if isinstance(name, str) and name:
                labels.append(name)
        elif isinstance(raw_label, str) and raw_label:
            labels.append(raw_label)

    assignees = []
    for raw_assignee in issue_obj.get("assignees", []):
        if isinstance(raw_assignee, dict):
            login = raw_assignee.get("login")
            if isinstance(login, str) and login:
                assignees.append(login)

    milestone = issue_obj.get("milestone")
    milestone_title = milestone.get("title") if isinstance(milestone, dict) else None

    number = int(issue_obj["number"])
    url = issue_obj.get("html_url") or f"https://github.com/{owner}/{repo}/issues/{number}"

    return {
        "owner": owner,
        "repo": repo,
        "issue_number": number,
        "url": url,
        "title": issue_obj.get("title", ""),
        "state": issue_obj.get("state", ""),
        "labels": labels,
        "milestone": milestone_title,
        "assignees": assignees,
        "body": issue_obj.get("body") or "",
    }


def issue_ref(default_owner: str, default_repo: str, issue_obj: Dict[str, Any]) -> Dict[str, Any]:
    owner, repo = _parse_owner_repo_from_api_urls(default_owner, default_repo, issue_obj)
    number = int(issue_obj["number"])
    url = issue_obj.get("html_url") or f"https://github.com/{owner}/{repo}/issues/{number}"
    return {
        "owner": owner,
        "repo": repo,
        "issue_number": number,
        "url": url,
        "title": issue_obj.get("title", ""),
        "state": issue_obj.get("state", ""),
    }


def fetch_issue(owner: str, repo: str, number: int) -> Dict[str, Any]:
    raw = gh_api_json(f"/repos/{owner}/{repo}/issues/{number}")
    if not isinstance(raw, dict):
        raise RuntimeError(f"Unexpected issue payload for {owner}/{repo}#{number}")
    return normalize_issue(owner, repo, raw)


def fetch_sub_issues(owner: str, repo: str, number: int) -> List[Dict[str, Any]]:
    raw = gh_api_json(
        f"/repos/{owner}/{repo}/issues/{number}/sub_issues",
        fields={"per_page": 100},
        allow_missing=True,
    )
    if raw is None:
        return []
    if not isinstance(raw, list):
        return []

    numbers: List[int] = []
    seen = set()
    for item in raw:
        if isinstance(item, dict) and "number" in item:
            candidate = int(item["number"])
            if candidate not in seen:
                seen.add(candidate)
                numbers.append(candidate)

    return [fetch_issue(owner, repo, n) for n in numbers]


def fetch_parent(owner: str, repo: str, number: int) -> Optional[Dict[str, Any]]:
    raw = gh_api_json(
        f"/repos/{owner}/{repo}/issues/{number}/parent",
        allow_missing=True,
    )
    if raw is None:
        return None
    if isinstance(raw, dict) and "issue" in raw and isinstance(raw["issue"], dict):
        raw = raw["issue"]
    if not isinstance(raw, dict):
        return None
    return normalize_issue(owner, repo, raw)


def _extract_dependency_items(payload: Any) -> List[Dict[str, Any]]:
    if payload is None:
        return []

    if isinstance(payload, list):
        result = []
        for item in payload:
            if isinstance(item, dict) and "number" in item:
                result.append(item)
            elif isinstance(item, dict) and isinstance(item.get("issue"), dict):
                nested = item["issue"]
                if "number" in nested:
                    result.append(nested)
        return result

    if isinstance(payload, dict):
        for key in ("items", "blocked_by", "blocking", "dependencies"):
            value = payload.get(key)
            if isinstance(value, list):
                return _extract_dependency_items(value)
    return []


def fetch_dependencies(owner: str, repo: str, number: int) -> Dict[str, List[Dict[str, Any]]]:
    blocked_by_raw = gh_api_json(
        f"/repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by",
        fields={"per_page": 100},
        allow_missing=True,
    )
    blocking_raw = gh_api_json(
        f"/repos/{owner}/{repo}/issues/{number}/dependencies/blocking",
        fields={"per_page": 100},
        allow_missing=True,
    )

    blocked_by = [issue_ref(owner, repo, item) for item in _extract_dependency_items(blocked_by_raw)]
    blocking = [issue_ref(owner, repo, item) for item in _extract_dependency_items(blocking_raw)]
    return {"blocked_by": blocked_by, "blocking": blocking}


def _escape_query_token(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def heuristic_neighbors(owner: str, repo: str, issue: Dict[str, Any]) -> List[Dict[str, Any]]:
    labels = [
        label
        for label in issue.get("labels", [])
        if isinstance(label, str)
        and label.lower() not in {"bug", "enhancement", "chore", "docs"}
    ]

    query_parts = [f"repo:{owner}/{repo}", "is:issue", "state:open"]
    if labels:
        for label in labels[:2]:
            query_parts.append(f"label:{_escape_query_token(label)}")
    elif any(isinstance(label, str) and label.lower() == "bug" for label in issue.get("labels", [])):
        query_parts.append("label:bug")

    result = gh_api_json(
        "/search/issues",
        fields={"q": " ".join(query_parts), "per_page": 30},
        allow_missing=True,
    )

    if not isinstance(result, dict):
        return []
    items = result.get("items")
    if not isinstance(items, list):
        return []

    by_num: Dict[int, Dict[str, Any]] = {}
    nums: List[int] = []

    for item in items:
        if isinstance(item, dict) and "number" in item:
            n = int(item["number"])
            by_num[n] = item
            nums.append(n)

    target_n = int(issue["issue_number"])
    ordered_nums = sorted(set(n for n in nums if n != target_n))

    idx = 0
    while idx < len(ordered_nums) and ordered_nums[idx] < target_n:
        idx += 1

    neighbor_nums = ordered_nums[max(0, idx - 2) : idx] + ordered_nums[idx : idx + 2]
    return [issue_ref(owner, repo, by_num[n]) for n in neighbor_nums if n in by_num]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch GitHub issue context for implementation workflows")
    parser.add_argument("target", help="Issue URL, owner/repo#123, or #123")
    parser.add_argument("--scope", choices=["open", "all"], default="open")
    parser.add_argument("--context-dir", default=".work-items")
    args = parser.parse_args()

    repo_override, issue_number = parse_target(args.target)
    if repo_override is None:
        inferred = parse_owner_repo_from_git_remote()
        if inferred is None:
            raise RuntimeError(
                "Cannot infer owner/repo. Use owner/repo#123 or run inside a git repository with origin remote."
            )
        owner, repo = inferred
    else:
        owner, repo = repo_override

    target = Target(
        raw=args.target,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        url=f"https://github.com/{owner}/{repo}/issues/{issue_number}",
    )

    issue = fetch_issue(owner, repo, issue_number)
    parent = fetch_parent(owner, repo, issue_number)
    sub_issues = fetch_sub_issues(owner, repo, issue_number)

    mode = "epic" if sub_issues else "issue"

    if args.scope == "open":
        sub_issues = [entry for entry in sub_issues if entry.get("state") != "closed"]

    siblings: List[Dict[str, Any]] = []
    if parent is not None:
        p_owner = parent["owner"]
        p_repo = parent["repo"]
        p_num = int(parent["issue_number"])
        parent_sub_issues = fetch_sub_issues(p_owner, p_repo, p_num)
        for sibling in parent_sub_issues:
            same_issue = (
                sibling.get("owner") == issue.get("owner")
                and sibling.get("repo") == issue.get("repo")
                and int(sibling.get("issue_number", -1)) == issue_number
            )
            if same_issue:
                continue
            if args.scope == "open" and sibling.get("state") == "closed":
                continue
            siblings.append(sibling)

    dependencies = fetch_dependencies(owner, repo, issue_number)

    related = {"heuristic_neighbors": []}
    if parent is None and not sub_issues:
        related["heuristic_neighbors"] = heuristic_neighbors(owner, repo, issue)

    context = {
        "target": {
            "raw": target.raw,
            "owner": target.owner,
            "repo": target.repo,
            "issue_number": target.issue_number,
            "url": target.url,
        },
        "mode": mode,
        "issue": issue,
        "parent": parent,
        "sub_issues": sub_issues,
        "siblings": siblings,
        "dependencies": dependencies,
        "related": related,
    }

    output_dir = Path(args.context_dir) / f"{owner}-{repo}#{issue_number}"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "context.json"
    output_path.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
