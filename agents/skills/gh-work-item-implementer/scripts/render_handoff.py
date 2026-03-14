#!/usr/bin/env python3
"""Render compact restart artifacts from context and work item state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Sequence


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected object JSON in {path}")
    return payload


def active_item(state: Dict[str, Any]) -> Dict[str, Any]:
    for item in state.get("items", []):
        if item.get("status") != "closed":
            return item
    raise RuntimeError("No active work item found")


def find_issue_unit(context: Dict[str, Any], item: Dict[str, Any]) -> Dict[str, Any] | None:
    parent_issue_number = item.get("parent_issue_number")
    for unit in context.get("hierarchy", {}).get("issues", []):
        issue = unit.get("issue") or {}
        issue_number = issue.get("issue_number")
        if item.get("kind") == "issue" and issue_number == item.get("number"):
            return unit
        if item.get("kind") == "sub-issue" and issue_number == parent_issue_number:
            return unit
    return None


def active_unit_label(context: Dict[str, Any], item: Dict[str, Any]) -> str:
    unit = find_issue_unit(context, item)
    if not unit:
        return f"{item['kind']} #{item['number']}"

    issue_number = unit["issue"]["issue_number"]
    if item["kind"] == "sub-issue":
        return f"Issue #{issue_number} / Sub-issue #{item['number']}"
    return f"Issue #{issue_number}"


def build_handoff(context: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    target = context["target"]
    item = active_item(state)
    return {
        "target": {
            "owner": target["owner"],
            "repo": target["repo"],
            "issue_number": target["issue_number"],
            "url": target["url"],
        },
        "work_state_path": str(Path(state.get("_path", ""))),
        "active_unit": active_unit_label(context, item),
        "active_item": {
            "kind": item["kind"],
            "number": item["number"],
            "parent_issue_number": item.get("parent_issue_number"),
            "title": item.get("title", ""),
            "status": item["status"],
            "objective": item.get("objective", ""),
            "constraints": item.get("constraints", []),
            "acceptance_criteria": item.get("acceptance_criteria", []),
            "assumptions": item.get("assumptions", []),
            "dependencies": item.get("dependencies", []),
            "next_action": item.get("next_action", ""),
            "verification_summary": item.get("verification_summary", ""),
            "review_summary": item.get("review_summary", ""),
            "base_sha": item.get("base_sha"),
            "head_sha": item.get("head_sha"),
            "updated_at": item.get("updated_at"),
        },
    }


def bullet_lines(items: Sequence[str]) -> str:
    if not items:
        return "- (none)"
    return "\n".join(f"- {item}" for item in items)


def render_markdown(handoff: Dict[str, Any]) -> str:
    target = handoff["target"]
    item = handoff["active_item"]
    return "\n".join(
        [
            f"Target: {target['owner']}/{target['repo']}#{target['issue_number']}",
            f"Active unit: {handoff['active_unit']}",
            f"Work state: {handoff['work_state_path']}",
            f"Closable kind: {item['kind']}",
            f"Closable number: {item['number']}",
            f"Objective: {item['objective'] or '(none)'}",
            "Constraints:",
            bullet_lines(item["constraints"]),
            "DoD:",
            bullet_lines(item["acceptance_criteria"]),
            "Assumptions:",
            bullet_lines(item["assumptions"]),
            "Dependencies:",
            bullet_lines(item["dependencies"]),
            f"Status: {item['status']}",
            f"Verification: {item['verification_summary'] or '(none)'}",
            f"Review: {item['review_summary'] or '(none)'}",
            f"Range: base_sha={item['base_sha']} head_sha={item['head_sha']}",
            f"Next: {item['next_action'] or '(none)'}",
        ]
    )


def write_text(path: str, text: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render restart-safe handoff artifacts from context and state."
    )
    parser.add_argument("--context", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--markdown-out")
    parser.add_argument("--json-out")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    context = load_json(args.context)
    state = load_json(args.state)
    state["_path"] = args.state
    handoff = build_handoff(context, state)
    markdown = render_markdown(handoff)

    if args.json_out:
        write_text(args.json_out, json.dumps(handoff, ensure_ascii=False, indent=2) + "\n")
    if args.markdown_out:
        write_text(args.markdown_out, markdown + "\n")

    if not args.markdown_out:
        sys.stdout.write(markdown + "\n")


if __name__ == "__main__":
    main()
