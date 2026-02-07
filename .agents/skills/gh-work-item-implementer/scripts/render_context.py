#!/usr/bin/env python3
"""Render context.json into a stable human-readable Markdown summary."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict


def md_issue(issue: Dict[str, Any]) -> str:
    labels = ", ".join(issue.get("labels", []))
    labels_segment = f" [{labels}]" if labels else ""

    milestone = issue.get("milestone")
    milestone_segment = f" / milestone: {milestone}" if milestone else ""

    return (
        f"- #{issue['issue_number']} **{issue.get('title', '')}** ({issue.get('state', '')})"
        f"{labels_segment}{milestone_segment}\n"
        f"  {issue.get('url', '')}"
    )


def md_issue_ref(issue_ref: Dict[str, Any]) -> str:
    return (
        f"- #{issue_ref['issue_number']} **{issue_ref.get('title', '')}** ({issue_ref.get('state', '')})\n"
        f"  {issue_ref.get('url', '')}"
    )


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: render_context.py <context.json>", file=sys.stderr)
        sys.exit(2)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        ctx = json.load(f)

    target = ctx["target"]
    mode = ctx["mode"]
    issue = ctx["issue"]
    parent = ctx.get("parent")
    sub_issues = ctx.get("sub_issues", [])
    siblings = ctx.get("siblings", [])
    dependencies = ctx.get("dependencies", {"blocked_by": [], "blocking": []})
    neighbors = ctx.get("related", {}).get("heuristic_neighbors", [])

    print(f"# Work Item Context: {target['owner']}/{target['repo']}#{target['issue_number']}\n")
    print(f"- URL: {target['url']}")
    print(f"- Mode: {mode}\n")

    print("## Target Issue\n")
    print(md_issue(issue))

    body = (issue.get("body") or "").strip()
    if body:
        print("\n<details><summary>Body</summary>\n")
        print("```md")
        print(body)
        print("```\n")
        print("</details>\n")

    if parent:
        print("## Parent (Epic)\n")
        print(md_issue(parent))
        print()

    if sub_issues:
        print("## Sub-issues (Implementation scope)\n")
        for sub_issue in sub_issues:
            print(md_issue(sub_issue))
        print()

    if siblings:
        print("## Siblings (Context only)\n")
        for sibling in siblings:
            print(md_issue(sibling))
        print()

    print("## Dependencies\n")
    print("### Blocked by\n")
    blocked_by = dependencies.get("blocked_by", [])
    if blocked_by:
        for dep in blocked_by:
            print(md_issue_ref(dep))
    else:
        print("- (none)")

    print("\n### Blocking\n")
    blocking = dependencies.get("blocking", [])
    if blocking:
        for dep in blocking:
            print(md_issue_ref(dep))
    else:
        print("- (none)")
    print()

    if neighbors:
        print("## Heuristic neighbors (standalone context)\n")
        for neighbor in neighbors:
            print(md_issue_ref(neighbor))
        print()


if __name__ == "__main__":
    main()
