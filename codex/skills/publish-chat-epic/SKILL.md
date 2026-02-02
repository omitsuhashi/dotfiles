---
name: publish-chat-epic
description: Publish a chat-generated Epic + Issues bundle (~~~markdown blocks) to GitHub as an epic issue and sub-issues using gh CLI when the user pastes those blocks and asks to create GitHub issues.
---

## Purpose
Turn a pasted Epic + Issues bundle (each item in a `~~~markdown` fenced block) into real GitHub Issues.

## Preconditions
- `gh` is installed and authenticated (`gh auth status` succeeds).
- You are in the target repository folder OR you know the target `owner/repo`.

## Input format
- The user pastes multiple fenced blocks like:
  - `~~~markdown` ... `~~~`
- The first block is treated as the Epic.
- Remaining blocks are treated as sub-issues.
- Title extraction:
  - Use the first Markdown heading (`# ...`) inside each block as the issue title.
  - That heading line is removed from the issue body (to avoid duplicate titles).

See `references/input_format.md` for examples.

## Workflow (safe-by-default)
1. Ask the user to paste the Epic/Issue bundle.
2. Save it to a temporary file (e.g. `./.issue-importer/input.md`).
3. Run a dry run first:
   - `python3 ~/.codex/skills/publish-chat-epic/scripts/publish_chat_epic.py --input ./.issue-importer/input.md`
4. Show the plan (epic title + sub-issue titles) and ask for confirmation.
5. On confirmation, apply:
   - `python3 ~/.codex/skills/publish-chat-epic/scripts/publish_chat_epic.py --input ./.issue-importer/input.md --apply`
6. Output:
   - Epic URL + created issue numbers
   - Mapping file path (default: `./.issue-importer/issue_map.json`)

## Options you may ask for (only if needed)
- `--repo owner/repo` if not running inside a git repo.
- `--label <name>` to add labels to all issues (repeatable).
- `--epic-label <name>` to add extra label(s) to epic only (repeatable).

## Trigger tests (manual)
Should trigger:
- "この `~~~markdown` の Epic と Issue を GitHub Issue として作成して"
- "このチャット出力をそのまま GitHub に publish して"

Should NOT trigger:
- Unrelated GitHub operations (listing issues, closing issues, etc.)
- General coding questions without pasted blocks
