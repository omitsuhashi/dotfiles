#!/usr/bin/env python3
"""Persist and validate per-work-item execution state."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence

STATUSES = [
    "planned",
    "implemented",
    "verified",
    "checkpoint_committed",
    "review_clean",
    "closed",
]
STATUS_INDEX = {name: index for index, name in enumerate(STATUSES)}
ANNOTATION_LIST_FIELDS = (
    "constraints",
    "acceptance_criteria",
    "assumptions",
    "dependencies",
)
ANNOTATION_SCALAR_FIELDS = (
    "objective",
    "next_action",
    "verification_summary",
    "review_summary",
)


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected object JSON in {path}")
    return payload


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
        fp.write("\n")


def build_items(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    hierarchy = context.get("hierarchy") or {}
    issue_units = hierarchy.get("issues") or []
    epic = hierarchy.get("epic")
    items: List[Dict[str, Any]] = []
    now = utc_now_iso()

    for unit in issue_units:
        issue = unit.get("issue") or {}
        issue_number = int(issue["issue_number"])
        for sub_issue in unit.get("sub_issues") or []:
            items.append(
                {
                    "kind": "sub-issue",
                    "number": int(sub_issue["issue_number"]),
                    "title": sub_issue.get("title", ""),
                    "parent_issue_number": issue_number,
                    "status": "planned",
                    "base_sha": None,
                    "head_sha": None,
                    "commit_shas": [],
                    "closed_at": None,
                    "objective": "",
                    "constraints": [],
                    "acceptance_criteria": [],
                    "assumptions": [],
                    "dependencies": [],
                    "next_action": "",
                    "verification_summary": "",
                    "review_summary": "",
                    "updated_at": now,
                }
            )
        items.append(
            {
                "kind": "issue",
                "number": issue_number,
                "title": issue.get("title", ""),
                "parent_issue_number": (
                    int(epic["issue_number"]) if isinstance(epic, dict) else None
                ),
                "status": "planned",
                "base_sha": None,
                "head_sha": None,
                "commit_shas": [],
                "closed_at": None,
                "objective": "",
                "constraints": [],
                "acceptance_criteria": [],
                "assumptions": [],
                "dependencies": [],
                "next_action": "",
                "verification_summary": "",
                "review_summary": "",
                "updated_at": now,
            }
        )
    return items


def init_state(context_path: Path, output_path: Path | None) -> Path:
    context = load_json(context_path)
    state_path = output_path or context_path.with_name("work_state.json")
    payload = {
        "target": context["target"],
        "mode": context["mode"],
        "items": build_items(context),
    }
    write_json(state_path, payload)
    return state_path


def load_state(path: Path) -> Dict[str, Any]:
    payload = load_json(path)
    items = payload.get("items")
    if not isinstance(items, list):
        raise RuntimeError(f"State file is missing items array: {path}")
    return payload


def find_item(payload: Dict[str, Any], kind: str, number: int) -> Dict[str, Any]:
    for item in payload["items"]:
        if item.get("kind") == kind and int(item.get("number", -1)) == number:
            return item
    raise RuntimeError(f"Work item not found: {kind} #{number}")


def validate_transition(item: Dict[str, Any], next_status: str) -> None:
    current = item["status"]
    if next_status not in STATUS_INDEX:
        raise RuntimeError(f"Unknown status: {next_status}")
    if STATUS_INDEX[next_status] != STATUS_INDEX[current] + 1:
        raise RuntimeError(
            f"Invalid status transition: {current} -> {next_status}"
        )


def update_item_from_args(item: Dict[str, Any], args: argparse.Namespace) -> None:
    next_status = args.status
    validate_transition(item, next_status)

    if next_status == "implemented":
        if not args.base_sha and not item.get("base_sha"):
            raise RuntimeError("implemented requires --base-sha")
        if args.base_sha:
            item["base_sha"] = args.base_sha

    if next_status == "checkpoint_committed":
        if not args.head_sha:
            raise RuntimeError("checkpoint_committed requires --head-sha")
        if not args.commit_sha:
            raise RuntimeError("checkpoint_committed requires --commit-sha")
        item["head_sha"] = args.head_sha
        for sha in args.commit_sha:
            if sha not in item["commit_shas"]:
                item["commit_shas"].append(sha)

    if next_status == "review_clean":
        item["head_sha"] = args.head_sha or item.get("head_sha")
        if not item.get("head_sha"):
            raise RuntimeError("review_clean requires --head-sha or existing head_sha")

    if next_status == "closed":
        item["closed_at"] = args.closed_at or utc_now_iso()

    if args.base_sha and not item.get("base_sha"):
        item["base_sha"] = args.base_sha
    if args.head_sha and next_status not in {"checkpoint_committed", "review_clean"}:
        item["head_sha"] = args.head_sha
    if args.commit_sha and next_status != "checkpoint_committed":
        for sha in args.commit_sha:
            if sha not in item["commit_shas"]:
                item["commit_shas"].append(sha)

    item["status"] = next_status
    item["updated_at"] = utc_now_iso()


def annotate_item_from_args(item: Dict[str, Any], args: argparse.Namespace) -> None:
    changed = False

    for field in ANNOTATION_SCALAR_FIELDS:
        value = getattr(args, field, None)
        if value is not None:
            item[field] = value
            changed = True

    for field in ANNOTATION_LIST_FIELDS:
        value = getattr(args, field, None)
        if value is not None:
            item[field] = value
            changed = True

    if changed:
        item["updated_at"] = utc_now_iso()


def show_active(payload: Dict[str, Any]) -> Dict[str, Any] | None:
    for item in payload["items"]:
        if item["status"] != "closed":
            return item
    return None


def assert_closable(payload: Dict[str, Any], kind: str, number: int) -> Dict[str, Any]:
    if kind == "epic":
        raise RuntimeError("Epic closure is not supported in this workflow")
    item = find_item(payload, kind, number)
    if item["status"] != "review_clean":
        raise RuntimeError(f"{kind} #{number} is not review_clean")
    if not item.get("head_sha"):
        raise RuntimeError(f"{kind} #{number} is missing head_sha")
    if not item.get("commit_shas"):
        raise RuntimeError(f"{kind} #{number} is missing commit_shas")

    if kind == "issue":
        child_items = [
            entry
            for entry in payload["items"]
            if entry.get("kind") == "sub-issue"
            and entry.get("parent_issue_number") == number
        ]
        open_children = [
            entry for entry in child_items if entry.get("status") != "closed"
        ]
        if open_children:
            child_numbers = ", ".join(str(entry["number"]) for entry in open_children)
            raise RuntimeError(
                f"Child sub-issues are not closed for issue #{number}: {child_numbers}"
            )
    return item


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage runtime work item state for GitHub issue workflows."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--context", required=True)
    init_parser.add_argument("--output")

    show_parser = subparsers.add_parser("show-active")
    show_parser.add_argument("--state", required=True)

    advance_parser = subparsers.add_parser("advance")
    advance_parser.add_argument("--state", required=True)
    advance_parser.add_argument("--kind", choices=["issue", "sub-issue"], required=True)
    advance_parser.add_argument("--number", type=int, required=True)
    advance_parser.add_argument("--status", choices=STATUSES[1:], required=True)
    advance_parser.add_argument("--base-sha")
    advance_parser.add_argument("--head-sha")
    advance_parser.add_argument("--commit-sha", action="append", default=[])
    advance_parser.add_argument("--closed-at")

    annotate_parser = subparsers.add_parser("annotate")
    annotate_parser.add_argument("--state", required=True)
    annotate_parser.add_argument("--kind", choices=["issue", "sub-issue"], required=True)
    annotate_parser.add_argument("--number", type=int, required=True)
    annotate_parser.add_argument("--objective")
    annotate_parser.add_argument("--constraint", dest="constraints", action="append")
    annotate_parser.add_argument(
        "--acceptance-criterion",
        dest="acceptance_criteria",
        action="append",
    )
    annotate_parser.add_argument("--assumption", dest="assumptions", action="append")
    annotate_parser.add_argument("--dependency", dest="dependencies", action="append")
    annotate_parser.add_argument("--next-action")
    annotate_parser.add_argument("--verification-summary")
    annotate_parser.add_argument("--review-summary")

    assert_parser = subparsers.add_parser("assert-closable")
    assert_parser.add_argument(
        "--kind", choices=["epic", "issue", "sub-issue"], required=True
    )
    assert_parser.add_argument("--number", type=int, required=True)
    assert_parser.add_argument("--state", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "init":
        state_path = init_state(
            Path(args.context),
            Path(args.output) if args.output else None,
        )
        print(str(state_path))
        return

    payload = load_state(Path(args.state))
    if args.command == "show-active":
        print(json.dumps(show_active(payload), ensure_ascii=False))
        return

    if args.command == "advance":
        item = find_item(payload, args.kind, args.number)
        update_item_from_args(item, args)
        write_json(Path(args.state), payload)
        print(json.dumps(item, ensure_ascii=False))
        return

    if args.command == "annotate":
        item = find_item(payload, args.kind, args.number)
        annotate_item_from_args(item, args)
        write_json(Path(args.state), payload)
        print(json.dumps(item, ensure_ascii=False))
        return

    item = assert_closable(payload, args.kind, args.number)
    print(json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    main()
