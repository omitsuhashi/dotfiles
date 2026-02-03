#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional, Tuple


FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_-]+)?\s*$")
HEADING_RE = re.compile(r"^\s*#{1,6}\s+(.*\S)\s*$")
ISSUE_URL_RE = re.compile(r"/issues/(\d+)(?:$|[/?#])")
DEFAULT_EPIC_LABEL = "epic"


@dataclass
class Block:
    internal_index: int  # 0-based within parsed blocks
    title: str
    body: str  # markdown body without the title heading line


@dataclass
class EpicGroup:
    epic: Block
    subs: List[Block]


def is_epic_title(title: str) -> bool:
    return "epic" in title.lower()


def group_epic_blocks(blocks: List[Block]) -> List[EpicGroup]:
    epic_indices = [i for i, b in enumerate(blocks) if is_epic_title(b.title)]
    if not epic_indices:
        if not blocks:
            return []
        return [EpicGroup(epic=blocks[0], subs=blocks[1:])]
    groups: List[EpicGroup] = []
    for idx, epic_idx in enumerate(epic_indices):
        epic = blocks[epic_idx]
        start = epic_idx + 1
        end = epic_indices[idx + 1] if idx + 1 < len(epic_indices) else len(blocks)
        subs = blocks[start:end]
        groups.append(EpicGroup(epic=epic, subs=subs))
    return groups


def build_plan_lines(repo: str, groups: List[EpicGroup]) -> List[str]:
    lines = [f"[PLAN] repo={repo}"]
    for group in groups:
        lines.append(f"[PLAN] epic: {group.epic.title}")
        for b in group.subs:
            lines.append(f"[PLAN] sub[{b.internal_index}]: {b.title}")
    return lines


def build_mapping_payload(*, repo: str, epics: List[dict]) -> dict:
    return {
        "repo": repo,
        "epics": epics,
    }


def run(cmd: List[str], *, check: bool = True) -> str:
    p = subprocess.run(cmd, text=True, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(
            f"Command failed ({p.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
        )
    return (p.stdout or "").strip()


def ensure_gh_ready() -> None:
    try:
        run(["gh", "--version"])
    except Exception as e:
        raise RuntimeError("`gh` not found. Install GitHub CLI first.") from e

    # auth status returns non-zero if not authenticated
    try:
        run(["gh", "auth", "status"])
    except Exception as e:
        raise RuntimeError("`gh` is not authenticated. Run `gh auth login`.") from e


def detect_repo() -> Optional[str]:
    # Works when executed inside a git repo where `gh repo view` can resolve the repo.
    try:
        return run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"])
    except Exception:
        return None


def extract_fenced_markdown_blocks(text: str) -> List[str]:
    lines = text.splitlines()
    blocks: List[str] = []
    i = 0
    while i < len(lines):
        m = FENCE_RE.match(lines[i])
        if m:
            fence = m.group(1)
            lang = (m.group(2) or "").lower()
            if lang in ("markdown", "md"):
                i += 1
                buf: List[str] = []
                while i < len(lines) and lines[i].strip() != fence:
                    buf.append(lines[i])
                    i += 1
                blocks.append("\n".join(buf).rstrip() + "\n")
        i += 1
    return blocks


def extract_title_and_body(block: str) -> Tuple[str, str]:
    lines = block.splitlines()

    for idx, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            title = m.group(1).strip()
            body_lines = lines[idx + 1 :]
            while body_lines and body_lines[0].strip() == "":
                body_lines.pop(0)
            body = "\n".join(body_lines).rstrip() + "\n"
            return title, body

    for idx, line in enumerate(lines):
        if line.strip():
            title = line.strip()[:120]
            body_lines = lines[idx + 1 :]
            while body_lines and body_lines[0].strip() == "":
                body_lines.pop(0)
            body = "\n".join(body_lines).rstrip() + "\n"
            return title, body

    return "Untitled", block.rstrip() + "\n"


def parse_blocks(text: str) -> List[Block]:
    raw_blocks = extract_fenced_markdown_blocks(text)
    if not raw_blocks:
        raise RuntimeError("No `~~~markdown` (or ```markdown) fenced blocks found.")

    parsed: List[Block] = []
    for i, raw in enumerate(raw_blocks):
        title, body = extract_title_and_body(raw)
        parsed.append(Block(internal_index=i, title=title, body=body))
    return parsed


def gh_issue_create(*, repo: str, title: str, body: str, labels: List[str]) -> Tuple[int, str]:
    with NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
        f.write(body)
        body_path = f.name

    try:
        cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body-file", body_path]
        for lab in labels:
            cmd += ["--label", lab]
        out = run(cmd)
        # gh prints the URL; parse issue number from it
        m = ISSUE_URL_RE.search(out)
        if not m:
            raise RuntimeError(f"Could not parse issue number from gh output: {out}")
        num = int(m.group(1))
        return num, out.strip()
    finally:
        try:
            os.unlink(body_path)
        except OSError:
            pass


def gh_issue_edit_body(*, repo: str, number: int, body: str) -> None:
    with NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
        f.write(body)
        body_path = f.name
    try:
        run(["gh", "issue", "edit", str(number), "--repo", repo, "--body-file", body_path])
    finally:
        try:
            os.unlink(body_path)
        except OSError:
            pass


def build_epic_labels(*, labels: List[str], epic_labels: List[str]) -> List[str]:
    merged = list(labels) + list(epic_labels)
    if DEFAULT_EPIC_LABEL not in merged:
        merged.append(DEFAULT_EPIC_LABEL)
    seen = set()
    result: List[str] = []
    for lab in merged:
        if lab in seen:
            continue
        seen.add(lab)
        result.append(lab)
    return result


def gh_issue_get_id(*, repo: str, number: int) -> int:
    out = run(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "X-GitHub-Api-Version: 2022-11-28",
            f"repos/{repo}/issues/{number}",
            "--jq",
            ".id",
        ]
    )
    return int(out.strip())


def gh_issue_add_subissue(*, repo: str, parent_number: int, sub_issue_id: int) -> None:
    run(
        [
            "gh",
            "api",
            "-X",
            "POST",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "X-GitHub-Api-Version: 2022-11-28",
            f"repos/{repo}/issues/{parent_number}/sub_issues",
            "-f",
            f"sub_issue_id={sub_issue_id}",
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish chat-generated epic + issues to GitHub.")
    ap.add_argument("--input", "-i", default="-", help="Input file path, or '-' for stdin.")
    ap.add_argument("--repo", "-r", default="", help="Target repo as owner/name. Auto-detected if omitted.")
    ap.add_argument("--apply", action="store_true", help="Actually create/edit issues. Default is dry-run.")
    ap.add_argument("--out", default="./.issue-importer/issue_map.json", help="Write mapping JSON here.")
    ap.add_argument("--label", action="append", default=[], help="Label to add to ALL issues (repeatable).")
    ap.add_argument("--epic-label", action="append", default=[], help="Extra label to add to Epic only (repeatable).")
    args = ap.parse_args()

    text = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")

    blocks = parse_blocks(text)
    groups = group_epic_blocks(blocks)
    if not groups:
        raise RuntimeError("No blocks found after parsing.")

    repo = args.repo.strip() or detect_repo()
    if not repo:
        raise RuntimeError("Could not detect repo. Run inside the repo or pass --repo owner/name.")

    print("\n".join(build_plan_lines(repo, groups)))

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to create issues.")
        return 0

    ensure_gh_ready()

    epic_records = []
    created_lines = []
    for group in groups:
        # 1) Create epic
        epic_labels = build_epic_labels(labels=list(args.label), epic_labels=list(args.epic_label))
        epic_num, epic_url = gh_issue_create(
            repo=repo, title=group.epic.title, body=group.epic.body, labels=epic_labels
        )
        created_lines.append(f"- Epic: #{epic_num} {epic_url}")

        created = []
        # 2) Create sub-issues
        for b in group.subs:
            num, url = gh_issue_create(repo=repo, title=b.title, body=b.body, labels=list(args.label))
            sub_issue_id = gh_issue_get_id(repo=repo, number=num)
            gh_issue_add_subissue(repo=repo, parent_number=epic_num, sub_issue_id=sub_issue_id)
            created.append(
                {
                    "internal_index": b.internal_index,
                    "title": b.title,
                    "number": num,
                    "url": url,
                    "id": sub_issue_id,
                }
            )
            created_lines.append(f"- #{num} {url}")

        # 3) Add epic backlink footer to sub-issues (edit body)
        for item in created:
            internal_idx = item["internal_index"]
            b = next(x for x in group.subs if x.internal_index == internal_idx)
            footer = [
                "",
                "---",
                "",
                f"Epic: #{epic_num}",
                f"Internal-ID: ISSUE-{internal_idx}",
            ]
            sub_body_final = (b.body.rstrip() + "\n") + "\n".join(footer) + "\n"
            gh_issue_edit_body(repo=repo, number=item["number"], body=sub_body_final)

        epic_records.append(
            {
                "epic": {"title": group.epic.title, "number": epic_num, "url": epic_url},
                "sub_issues": created,
            }
        )

    # 4) Save mapping
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_mapping_payload(repo=repo, epics=epic_records)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\n[OK] Created:")
    for line in created_lines:
        print(line)
    print(f"[OK] Mapping: {out_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        raise
