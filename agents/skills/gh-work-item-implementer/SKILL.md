---
name: gh-work-item-implementer
description: Use when the user provides a GitHub Issue reference (URL, owner/repo#number, or #number) and asks to implement it end-to-end with parent/sub-issue and dependency context.
---

# GitHub Work Item Implementer

## Inputs
Accept exactly one target:
- Full URL: `https://github.com/<owner>/<repo>/issues/<number>`
- Qualified: `<owner>/<repo>#<number>`
- Local: `#<number>` (resolve owner/repo from `git remote origin`)

Optional flags in the same line:
- `mode=auto|epic|issue` (default `auto`)
- `scope=open|all` (default `open`)
- `commit=per-issue|fine-grained` (default `per-issue`)
- `context_dir=<path>` (default `./.work-items`)

## Must Produce (Artifacts)
- `<context_dir>/<owner>-<repo>#<num>/context.json`
- `<context_dir>/<owner>-<repo>#<num>/context.md`

## Strict Workflow
1. Fetch context deterministically.
   - `python3 ".agents/skills/gh-work-item-implementer/scripts/fetch_context.py" <TARGET> --scope <scope> --context-dir <context_dir>`
   - `python3 ".agents/skills/gh-work-item-implementer/scripts/render_context.py" <context.json> > <context.md>`
2. Decide work mode.
   - If `mode=epic` OR issue has `sub_issues` => epic mode.
   - Else => issue mode.
3. Define DoD in chat.
   - Write a short checklist from acceptance criteria.
   - If criteria are missing, infer the minimum and mark assumptions.
4. Implement.

### Epic Mode
- Implement each open sub-issue in the order returned by the Sub-issues API.
- If dependency edges exist among sub-issues, process `blocked_by` before `blocking`.
- After each sub-issue reaches DoD and tests are green, close that sub-issue via `gh issue close`.
- Commit strategy:
  - `per-issue`: at least one commit per sub-issue (default)
  - `fine-grained`: split within each sub-issue into multiple coherent commits when safer/reviewable
  - Never combine multiple sub-issues into a single commit.

### Issue Mode
- If parent exists, read parent + siblings + dependencies before coding.
- Implement only target issue scope.
- Do not conflict with epic plan and sibling responsibilities.
- If the target is a sub-issue and is completed, close it via `gh issue close`.
- Commit strategy:
  - `per-issue`: at least one commit for the target issue (default)
  - `fine-grained`: split the issue into multiple coherent commits when changes span independent concerns

### Standalone Bug
- Parent may be null.
- Use dependencies and issue body/repro steps as primary anchors.

5. Verification.
- Run the most relevant test/lint commands for the repository.
- Fix failures and rerun until clean.

6. Close completed issue(s).
- If a sub-issue is fully implemented and verification is clean, close it:
  - `gh issue close <sub_issue_number> --repo <owner>/<repo> --comment "Implemented and verified in this task."`
- In epic mode, close each completed sub-issue before moving to the next one.
- In issue mode, if the target itself is a sub-issue and DoD is satisfied, close the target issue.

7. Final report.
- Changes summary (group by sub-issue in epic mode)
- Tests run and results
- Assumptions and follow-ups

## Notes
- This skill depends on GitHub CLI authentication (`gh auth status`).
- `fetch_context.py` normalizes all missing links to `null` or empty arrays so downstream steps can handle standalone bugs safely.
- Implement in the current Codex session working directory.
- Do not create/switch git branches or create/use git worktrees unless the user explicitly asks.
