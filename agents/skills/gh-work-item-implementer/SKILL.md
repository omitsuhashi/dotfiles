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
- `review=on|off` (default `off`; `off` skips `$review-fix-loop`)
- `commit=per-issue|fine-grained` (default `per-issue`; both enforce at least one commit per completed Sub-issue and per completed Issue-level integration)
- `context_dir=<path>` (default `./.work-items`)

## Must Produce (Artifacts)
- `<context_dir>/<owner>-<repo>#<num>/context.json`
- `<context_dir>/<owner>-<repo>#<num>/context.md`
- `<context_dir>/<owner>-<repo>#<num>/work_state.json`
- `<context_dir>/<owner>-<repo>#<num>/handoff.json`
- `<context_dir>/<owner>-<repo>#<num>/handoff.md`

## REQUIRED SUPER_POWERS (in order)
1. `superpowers:writing-plans`
2. `superpowers:subagent-driven-development` (default when there is more than one independent Issue/Sub-issue unit; keep context local to each unit and minimize compression risk) or `superpowers:executing-plans` (allowed only when there is a single tightly coupled unit and batch execution is safer)
3. `$review-fix-loop` (required when `review=on`; skip entirely when `review=off`)
4. `superpowers:verification-before-completion`
5. `superpowers:finishing-a-development-branch` (optional, and only after completed Sub-issues/Issues are closed and the user asks to merge/PR/cleanup)

## Autonomy Contract
- Default operating mode is `continue-unless-blocked`.
- Do not stop after each task, each batch, or each completed work item just to report progress. Continue directly to the next eligible work item.
- Return control to the user only when:
  - Requirements or issue hierarchy are contradictory.
  - The next action is irreversible or meaningfully risky.
  - Permissions, authentication, or repository policy block execution.
  - GitHub closure eligibility is ambiguous.
  - Verification/review fails repeatedly and the workflow cannot make forward progress.
  - All scoped work items are completed and the final report is ready.
- If an execution skill normally pauses between tasks or batches, override that behavior inside this workflow. Parent workflow regains control only on a blocker or at full completion.
- Every time the active work item changes, or its status/DoD/blocker state changes, refresh both `handoff.json` and `handoff.md` before continuing.

## Strict Workflow
1. Fetch context deterministically.
   - `python3 "agents/skills/gh-work-item-implementer/scripts/fetch_context.py" <TARGET> --scope <scope> --context-dir <context_dir>`
   - `python3 "agents/skills/gh-work-item-implementer/scripts/render_context.py" <context.json> > <context.md>`
   - `python3 "agents/skills/gh-work-item-implementer/scripts/work_item_state.py" init --context <context.json>`
   - `python3 "agents/skills/gh-work-item-implementer/scripts/render_handoff.py" --context <context.json> --state <work_state.json> --json-out <handoff.json> --markdown-out <handoff.md>`
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
   - Persist the active unit recap before implementation:
     - `python3 "agents/skills/gh-work-item-implementer/scripts/work_item_state.py" annotate --state <work_state.json> --kind <sub-issue|issue> --number <n> --objective "<objective>" --constraint "<constraint>" --acceptance-criterion "<criterion>" --assumption "<assumption>" --dependency "<dependency>" --next-action "<next step>"`
   - Restate the Issue unit in chat before implementation: objective, constraints, acceptance criteria, dependencies, and any parent/child scope that matters to the current unit.
   - If the issue body is long, compress it into a short implementation-oriented recap instead of pasting it verbatim.
   - Refresh handoff artifacts immediately after annotation so the next subagent/session can resume from them alone.
4. Implement Issue units one-by-one.
   - For each Issue unit, complete Sub-issues first, then Issue-level integration.
   - Prefer assigning independent Issue units or clearly bounded Sub-issues to subagents so each unit carries its own local implementation context.
   - New subagents or new sessions should read `handoff.md` first and only then load the minimum repo files needed for the active item. `context.md` is background context, not the primary restart artifact.
   - At the start of each active work item, capture `WORK_ITEM_BASE_SHA=$(git rev-parse HEAD)` and move its state from `planned` to `implemented`:
     - `python3 "agents/skills/gh-work-item-implementer/scripts/work_item_state.py" advance --state <work_state.json> --kind <sub-issue|issue> --number <n> --status implemented --base-sha "$WORK_ITEM_BASE_SHA"`
   - After each status transition or blocker update, regenerate handoff artifacts:
     - `python3 "agents/skills/gh-work-item-implementer/scripts/render_handoff.py" --context <context.json> --state <work_state.json> --json-out <handoff.json> --markdown-out <handoff.md>`
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
   - When verification is green, update the active work item to `verified`:
     - `python3 "agents/skills/gh-work-item-implementer/scripts/work_item_state.py" advance --state <work_state.json> --kind <sub-issue|issue> --number <n> --status verified`
6. Checkpoint commit before review gate.
   - Create a dedicated checkpoint commit for the active work item before any review action.
   - Record the checkpoint commit and current `HEAD_SHA` in state:
     - `HEAD_SHA=$(git rev-parse HEAD)`
     - `python3 "agents/skills/gh-work-item-implementer/scripts/work_item_state.py" advance --state <work_state.json> --kind <sub-issue|issue> --number <n> --status checkpoint_committed --head-sha "$HEAD_SHA" --commit-sha "$HEAD_SHA"`
   - If the active work item is not committed at this point, stop instead of continuing to review or closure.
7. Review gate per completed work item.
   - If `review=on`: run `$review-fix-loop` before each closure action.
   - Scope for `review=on`:
     - Completed Sub-issue: review/fix loop before closing that Sub-issue.
     - Issue-level integration: review/fix loop before closing the Issue.
   - When invoking `$review-fix-loop`, scope it to the active work item with the checkpoint range:
     - `base_sha="$WORK_ITEM_BASE_SHA"`
   - If `review=off`: skip the review gate entirely and rely on fresh verification evidence only.
   - After the active review gate is green, record the final clean `HEAD_SHA`:
     - `HEAD_SHA=$(git rev-parse HEAD)`
     - `python3 "agents/skills/gh-work-item-implementer/scripts/work_item_state.py" advance --state <work_state.json> --kind <sub-issue|issue> --number <n> --status review_clean --head-sha "$HEAD_SHA"`
   - Do not proceed to the next sibling Sub-issue or next Issue unit until the active gate is green (`review=on`: zero findings + verification green + `review_clean`, `review=off`: verification green + `review_clean`).
   - If the execution skill would normally jump to branch-finish/PR options after implementation, override that default and return to this workflow first.
8. Close completed work items immediately after their own active gate is green and their required commit exists.
   - Determine the active work item kind before any closure command. The only closable kinds in this skill are `sub-issue` and `issue`. Treat `epic` as non-closable even though GitHub stores it as an issue.
   - Verify closure eligibility through state before calling GitHub:
     - `python3 "agents/skills/gh-work-item-implementer/scripts/work_item_state.py" assert-closable --state <work_state.json> --kind <sub-issue|issue> --number <n>`
   - Close each completed Sub-issue as soon as its implementation is done and its own gate is green. Do not batch Sub-issue closure until the end of the parent Issue unit:
     - `python3 "agents/skills/gh-work-item-implementer/scripts/close_work_item.py" --kind sub-issue --state <work_state.json> --repo <owner>/<repo> --number <sub_issue_number>`
   - Close the active Issue as soon as its Sub-issues (if any) are already closed, its Issue-level DoD is complete, and its own gate is green:
     - `python3 "agents/skills/gh-work-item-implementer/scripts/close_work_item.py" --kind issue --state <work_state.json> --repo <owner>/<repo> --number <issue_number>`
   - After GitHub closes the work item, persist the final `closed` state:
     - `python3 "agents/skills/gh-work-item-implementer/scripts/work_item_state.py" advance --state <work_state.json> --kind <sub-issue|issue> --number <n> --status closed`
   - If any work item cannot be closed at the moment it becomes eligible, stop there and ask the user for a decision instead of continuing with later work items.
   - Never close the Epic in this skill, even if all child work is complete, unless the user explicitly asks in a separate follow-up.
9. Final report.
   - Changes summary grouped by `Issue -> Sub-issue`
   - Commits created for each completed Sub-issue/Issue
   - Tests/lint run and results
   - Review-gate evidence (clean round + final gate result) when `review=on`, or explicit `review skipped by flag` note when `review=off`
   - Assumptions, blockers encountered, and the final `handoff` location used during execution
10. Optional branch finishing.
   - Only after step 9, and only if the user asks to merge/PR/cleanup, use `superpowers:finishing-a-development-branch`.

## Context Compression Handoff
- Do not resume from file paths alone. Re-state the active `Issue unit`.
- `handoff.json` and `handoff.md` are mandatory runtime artifacts, not optional notes.
- Prefer `handoff.md` as the only restart prompt input plus the minimum repo files needed for the active item.
- Include only:
  - Target + active `Issue unit`
  - `work_state.json` path
  - Active work item kind (`sub-issue` or `issue`) and exact closable number
  - Objective, constraints, acceptance criteria, assumptions, dependencies
  - Verification summary and review summary when present
  - Done status: implemented, verified, checkpoint_committed, review_clean, closed
  - `base_sha` and latest `head_sha`
  - Exact next action
- `context.json` and `context.md` are source artifacts, not substitutes for this recap.
- Prefer one subagent or isolated execution thread per independent unit so compression stays local.

```md
Target: Epic/Issue/Sub-issue ...
Active unit: ...
Work state: ...
Active work item kind: sub-issue|issue (never epic here)
Closable number: ...
Objective: ...
Constraints:
- ...
DoD:
- ...
Assumptions:
- ...
Dependencies:
- ...
Status: implemented ...; verified ...; checkpoint_committed ...; review_clean ...; closed ...
Verification: ...
Review: ...
Range: base_sha=...; head_sha=...
Next: ...
```

### Commit Invariant (All Modes)
- Minimum requirement: at least one commit per completed Issue/Sub-issue in this task.
- `fine-grained` allows extra commits within one work item, but does not relax per-item minimum.
- Each completed Sub-issue/Issue must have its own checkpoint commit before review/closure and before work begins on the next sibling or next Issue unit.
- The per-item commit sequence may include review-fix follow-up commits, but the checkpoint commit is mandatory even when `review=off`.
- The per-item final clean state must be recorded in `work_state.json`.
- A single commit must not mix changes from multiple Issue units.

### Standalone Bug
- Parent may be null.
- Use dependencies and issue body/repro steps as primary anchors.

## Notes
- This skill depends on GitHub CLI authentication (`gh auth status`).
- `fetch_context.py` normalizes missing links to `null` or empty arrays so standalone issues are safe.
- Implement in the current Codex session working directory.
- Do not create/switch git branches or create/use git worktrees unless the user explicitly asks.
- `work_state.json` is the runtime source of truth for lifecycle progress; do not rely on memory alone.
- Commit timing is mandatory in this skill: do not defer a completed Sub-issue/Issue checkpoint commit until "later" or batch multiple completed items into one commit.
- Parent workflow owns GitHub work-item closure. Close each completed Sub-issue/Issue at the first valid opportunity defined in step 8, and do not treat generic plan/task completion or branch-finishing as a substitute.
- If closure is blocked or ambiguous, stop and escalate to the user immediately rather than deferring closure or guessing.
- `review=off` is a user-controlled speed/strictness tradeoff. Do not silently skip review unless the flag is explicitly set, but still require `verified -> checkpoint_committed -> review_clean` state progression before closure.
- Long-running execution should assume chat context is disposable. The persistent source of resume truth is `work_state.json` plus the latest `handoff.json` / `handoff.md`.
