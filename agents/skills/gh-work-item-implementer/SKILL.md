---
name: gh-work-item-implementer
description: Use when the user provides a GitHub Issue reference (URL, owner/repo#number, or #number) and asks to implement it end-to-end with Epic/Issue/Sub-issue hierarchy and dependency context.
---

# GitHub Work Item Implementer

## Inputs
Accept exactly one target:
- Full URL: `https://github.com/<owner>/<repo>/issues/<number>`
- Qualified: `<owner>/<repo>#<number>`
- Local: `#<number>` (resolve owner/repo from `git remote origin`)

Optional flags in the same line:
- `mode=auto|epic|issue|sub-issue` (default `auto`)
- `scope=open|all` (default `open`)
- `review=on|off` (default `on`; `off` skips `$review-fix-loop`)
- `commit=per-issue|fine-grained` (default `per-issue`; both enforce at least one commit per completed Sub-issue and per completed Issue-level integration)
- `context_dir=<path>` (default `./.work-items`)

## Must Produce (Artifacts)
- `<context_dir>/<owner>-<repo>#<num>/context.json`
- `<context_dir>/<owner>-<repo>#<num>/context.md`

## REQUIRED SUPER_POWERS (in order)
1. `superpowers:writing-plans`
2. `superpowers:subagent-driven-development` (prefer for large Epics or any independent Issue units to keep context local to each unit and reduce compression risk) or `superpowers:executing-plans` (if tightly coupled)
3. `$review-fix-loop` (required when `review=on`; skip entirely when `review=off`)
4. `superpowers:verification-before-completion`
5. `superpowers:finishing-a-development-branch` (optional, and only after completed Sub-issues/Issues are closed and the user asks to merge/PR/cleanup)

## Strict Workflow
1. Fetch context deterministically.
   - `python3 "agents/skills/gh-work-item-implementer/scripts/fetch_context.py" <TARGET> --scope <scope> --context-dir <context_dir>`
   - `python3 "agents/skills/gh-work-item-implementer/scripts/render_context.py" <context.json> > <context.md>`
2. Build execution units from 3-level hierarchy (`Epic -> Issue -> Sub-issue`).
   - If target is an Epic: expand to `Issue units`, each with its own `Sub-issues`.
   - If target is an Issue: create one `Issue unit` with its `Sub-issues`.
   - If target is a Sub-issue: create one `Issue unit` using the parent Issue, and scope implementation to the target Sub-issue.
   - Unit order:
     - Keep API order by default.
     - If dependency edges exist, process `blocked_by` before `blocking`.
3. Define DoD in chat for each Issue unit.
   - Write a short checklist from acceptance criteria.
   - If criteria are missing, infer minimum viable acceptance and mark assumptions.
   - Restate the Issue unit in chat before implementation: objective, constraints, acceptance criteria, dependencies, and any parent/child scope that matters to the current unit.
   - If the issue body is long, compress it into a short implementation-oriented recap instead of pasting it verbatim.
4. Implement Issue units one-by-one.
   - For each Issue unit, complete Sub-issues first, then Issue-level integration.
   - Prefer assigning independent Issue units or clearly bounded Sub-issues to subagents so each unit carries its own local implementation context.
   - After finishing a Sub-issue's implementation, do not leave it open "for later". Run the needed gate for that Sub-issue, and close it immediately once that gate is green before starting the next sibling Sub-issue.
   - If a completed Sub-issue cannot be closed at that point for any reason (permissions, policy ambiguity, GitHub/API error, uncertainty about whether closure is appropriate), stop and ask the user how to proceed.
   - Commit strategy:
     - `per-issue`: at least one commit per completed Sub-issue, and at least one commit for the Issue-level integration.
     - `fine-grained`: keep the same minimums, and split into coherent commits as needed.
   - A work item is not considered finished for this workflow until its own commit exists.
   - Never mix multiple Issue units into a single commit.
5. Verification before review gate.
   - Run repository-relevant tests/lint with fresh evidence for the work item about to be closed.
   - Fix failures and rerun until clean.
6. Review gate per completed work item.
   - If `review=on`: run `$review-fix-loop` before each closure action.
   - Scope for `review=on`:
     - Completed Sub-issue: review/fix loop before closing that Sub-issue.
     - Issue-level integration: review/fix loop before closing the Issue.
   - If `review=off`: skip the review gate entirely and rely on fresh verification evidence only.
   - Do not proceed to the next sibling Sub-issue or next Issue unit until the active gate is green (`review=on`: zero findings + verification green, `review=off`: verification green).
   - If the execution skill would normally jump to branch-finish/PR options after implementation, override that default and return to this workflow first.
7. Commit completed work items immediately after their own active gate is green.
   - Create at least one commit dedicated to the active completed work item before closing it and before starting any other Sub-issue/Issue unit.
   - The commit must contain only the changes for that completed Sub-issue or Issue-level integration.
   - If review or verification produces follow-up fixes, rerun the active gate as needed and then commit the final green state.
   - If you cannot produce that commit at the required moment, stop and ask the user instead of continuing.
8. Close completed work items immediately after their own active gate is green and their required commit exists.
   - Determine the active work item kind before any closure command. The only closable kinds in this skill are `sub-issue` and `issue`. Treat `epic` as non-closable even though GitHub stores it as an issue.
   - Close each completed Sub-issue as soon as its implementation is done and its own gate is green. Do not batch Sub-issue closure until the end of the parent Issue unit:
     - `python3 "agents/skills/gh-work-item-implementer/scripts/close_work_item.py" --kind sub-issue --repo <owner>/<repo> --number <sub_issue_number>`
   - Close the active Issue as soon as its Sub-issues (if any) are already closed, its Issue-level DoD is complete, and its own gate is green:
     - `python3 "agents/skills/gh-work-item-implementer/scripts/close_work_item.py" --kind issue --repo <owner>/<repo> --number <issue_number>`
   - If any work item cannot be closed at the moment it becomes eligible, stop there and ask the user for a decision instead of continuing with later work items.
   - Never close the Epic in this skill, even if all child work is complete, unless the user explicitly asks in a separate follow-up.
9. Final report.
   - Changes summary grouped by `Issue -> Sub-issue`
   - Commits created for each completed Sub-issue/Issue
   - Tests/lint run and results
   - Review-gate evidence (clean round + final gate result) when `review=on`, or explicit `review skipped by flag` note when `review=off`
   - Assumptions and follow-ups
10. Optional branch finishing.
   - Only after step 9, and only if the user asks to merge/PR/cleanup, use `superpowers:finishing-a-development-branch`.

## Context Compression Handoff
- Do not resume from file paths alone. Re-state the active `Issue unit`.
- Include only:
  - Target + active `Issue unit`
  - Active work item kind (`sub-issue` or `issue`) and exact closable number
  - Short recap: problem, intended behavior, constraints
  - Acceptance criteria or DoD
  - Dependencies, blockers, assumptions
  - Done status: implemented, verified, reviewed, committed, closed
  - Exact next action
- `context.json` and `context.md` are source artifacts, not substitutes for this recap.
- Prefer one subagent or isolated execution thread per independent unit so compression stays local.

```md
Target: Epic/Issue/Sub-issue ...
Active unit: ...
Active work item kind: sub-issue|issue (never epic here)
Closable number: ...
Recap: problem / intended behavior / constraints
DoD:
- ...
Dependencies: ...
Status: implemented ...; verified ...; reviewed ...; committed ...; closed ...
Next: ...
```

### Commit Invariant (All Modes)
- Minimum requirement: at least one commit per completed Issue/Sub-issue in this task.
- `fine-grained` allows extra commits within one work item, but does not relax per-item minimum.
- Each completed Sub-issue/Issue must have its own commit before closure and before work begins on the next sibling or next Issue unit.
- The per-item commit should represent the final green state for that work item after verification/review fixes.
- A single commit must not mix changes from multiple Issue units.

### Standalone Bug
- Parent may be null.
- Use dependencies and issue body/repro steps as primary anchors.

## Notes
- This skill depends on GitHub CLI authentication (`gh auth status`).
- `fetch_context.py` normalizes missing links to `null` or empty arrays so standalone issues are safe.
- Implement in the current Codex session working directory.
- Do not create/switch git branches or create/use git worktrees unless the user explicitly asks.
- Commit timing is mandatory in this skill: do not defer a completed Sub-issue/Issue commit until "later" or batch multiple completed items into one commit.
- Parent workflow owns GitHub work-item closure. Close each completed Sub-issue/Issue at the first valid opportunity defined in step 8, and do not treat generic plan/task completion or branch-finishing as a substitute.
- If closure is blocked or ambiguous, stop and escalate to the user immediately rather than deferring closure or guessing.
- `review=off` is a user-controlled speed/strictness tradeoff. Do not silently skip review unless the flag is explicitly set.
