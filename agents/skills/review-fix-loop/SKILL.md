---
name: review-fix-loop
description: Use when the user asks to repeatedly run code review and apply fixes until review findings are zero, especially for requests like "review and fix until clean", "auto re-review loop", or strict pre-merge quality gates.
---

# Review Fix Loop

## Overview

Run a strict "review -> fix -> review" cycle without stopping after the first pass.
Continue until no actionable findings remain or a hard stop condition is met.
Run this in two phases:
1. Loop phase: run review rounds using `$requesting-code-review`.
2. Strict final gate (optional): when loop findings become zero and `strict_mode=true`, run one extra `$requesting-code-review` round against the same baseline as final clean confirmation.

**REQUIRED SUB-SKILL:** Use `$requesting-code-review` for review rubric/context quality.
**REQUIRED SUB-SKILL:** Use `$receiving-code-review` to evaluate and apply feedback rigorously.
**REQUIRED SUB-SKILL:** Use `superpowers:verification-before-completion` before claiming completion.

## Review Invocation Contract

Use `$requesting-code-review` exactly as the review acquisition workflow for every round.
Do not bypass it with direct `codex review` calls or any other ad hoc review command.
Keep the review baseline fixed for the entire loop.

## Sub-Skill Contract

For every loop round, apply both skills explicitly:

1. Review acquisition must follow `$requesting-code-review`.
   - Get SHAs (`BASE_SHA`, `HEAD_SHA`).
   - Use the review path defined by `$requesting-code-review` and its `code-reviewer.md` template.
   - If the template file is unavailable in the runtime, pass the same rubric as inline prompt text and record that fallback.
   - Save reviewer artifact (subagent output summary, stdout summary, or log path) every round.
2. Feedback handling and fixes must follow `$receiving-code-review`.
   - Use the full sequence: `READ -> UNDERSTAND -> VERIFY -> EVALUATE -> RESPOND -> IMPLEMENT`.
   - Do not apply suggestions blindly.
   - If any feedback item is unclear, stop and clarify before implementation.
3. When a loop round returns zero findings:
   - If `strict_mode=true`, run final gate once more with `$requesting-code-review` against the same baseline before declaring clean.
   - If `strict_mode=false`, skip final gate and continue to final verification.
   - Treat strict final gate findings as normal findings (fix and continue loop).

## Defaults

Use these defaults unless the user overrides them:

- `base_sha`: unset by default; when provided, review only the active work item range `BASE_SHA..HEAD_SHA`
- `comparison_branch`: `main` (override allowed, e.g. `release/2026-q1`)
- `max_rounds`: 10
- `severity_scope`: all findings (`Critical`, `Important`, `Minor`)
- `stop_on_repeated_findings`: stop when the same unresolved finding repeats for 2 consecutive rounds
- `commit_after_fix`: required (create a commit after each completed fix phase that has changes)
- `strict_mode`: false (`true` requires one extra final gate review after a clean round)
- `autonomy`: continue looping without asking after each round; ask only for blockers/ambiguity

## Loop Workflow

1. Prepare loop context.
   - If the caller provides `base_sha=<sha>`, treat that as the locked starting point for the active work item and prefer range-scoped review over branch-wide review.
   - Determine `comparison_branch` (default `main`; user may override).
   - Resolve `BASE_SHA`:
     - If `base_sha` is provided, use it directly.
     - Otherwise, derive it from the comparison target (recommended: `git merge-base origin/<comparison_branch> HEAD`).
   - Set current `HEAD_SHA` (`git rev-parse HEAD`).
   - Capture acceptance requirements (issue, plan, or explicit user request).
2. Run review round `N`.
   - Execute `$requesting-code-review` once for the current branch range (`BASE_SHA` -> `HEAD_SHA`).
   - Normalize findings into a checklist with unique IDs:
     - `R<N>-C#` for Critical
     - `R<N>-I#` for Important
     - `R<N>-M#` for Minor
   - Publish the round report with per-finding detail (ID, severity, location, summary, status). Do not output counts only.
3. Decide continuation.
   - If checklist is empty: still publish this round report with `Findings detail: none`.
   - If checklist is empty and `strict_mode=false`: go to final verification.
   - If checklist is empty and `strict_mode=true`: run final gate with one extra `$requesting-code-review` round.
   - If strict final gate returns no findings: go to final verification.
   - If strict final gate returns findings: add them to next round checklist and continue fix phase.
   - If checklist has findings: continue to fix phase.
4. Fix findings one-by-one.
   - Start from highest severity.
   - Handle each finding with `$receiving-code-review` rules before changing code.
   - For each item: implement minimal safe fix, then run relevant tests/lint.
   - Do not batch unrelated fixes into one large speculative refactor.
5. Re-verify implementation quality.
   - Run repository-relevant checks before next review round.
   - If checks fail, fix failures before re-review.
6. Commit validated fixes.
   - If changes exist and checks pass, create a commit for this round (required).
   - Continue in the same existing worktree; do not recreate or switch worktrees as part of this loop.
7. Run next review round.
   - Recompute `HEAD_SHA` from the new commit.
   - If `base_sha` is pinned, keep `BASE_SHA` fixed for the entire active work item.
   - Otherwise refresh branch diff context from `comparison_branch`.
   - Execute the next review round unconditionally.
   - Exit only when a Stop Condition is met.

## Stop Conditions

Stop the loop only when at least one condition is true:

1. No actionable findings remain in scope.
2. `max_rounds` is reached.
3. The same unresolved finding repeats for 2 rounds with no technically valid fix path.
4. Feedback conflicts with requirements and needs user decision.
5. `strict_mode=true` and final gate review cannot run due runtime limitation and no valid fallback is available.

When stopping with unresolved findings, report:
- unresolved item IDs
- why they remain
- exact decision needed from the user

## Operational Rules

- Treat review comments as hypotheses until verified in the codebase.
- Keep changes review-driven and minimal; avoid opportunistic rewrites.
- Preserve existing behavior unless a finding explicitly requires behavior change.
- Run tests after each fix set and again before each re-review.
- Each completed fix phase must end with a commit when changes exist.
- Re-review must stay scoped to the same review baseline for the whole loop: branch-based against `comparison_branch` when `base_sha` is unset, or range-based against the pinned `BASE_SHA` when `base_sha` is set.
- Re-review is mandatory after each committed fix round until findings are zero or another Stop Condition is met.
- Review the committed branch state against the same baseline each round; never widen a `base_sha`-scoped loop back to the whole branch.
- Use the current existing worktree throughout; worktree recreation is out of scope.
- Every review round must record the review workflow actually used through `$requesting-code-review` and the range (`BASE_SHA..HEAD_SHA`).
- Every review round must output the concrete finding list; summary counts alone are not acceptable.
- If a round has zero findings, output `Findings detail: none` explicitly.
- When round findings are zero and `strict_mode=true`, one extra `$requesting-code-review` round against the same baseline is mandatory before declaring clean.
- Never declare "done" without clean review evidence and verification evidence. Include strict final gate evidence only when `strict_mode=true`.

## Round Report Format

Use this compact structure every round:

```markdown
Round N/5
- Review range: <BASE_SHA>..<HEAD_SHA>
- Review workflow: <$requesting-code-review result path used this round>
- Reviewer artifact: <review output summary or saved log path>
- Fix commit: <hash/none>
- Worktree: existing worktree (no recreation)
- Findings: Critical=<n>, Important=<n>, Minor=<n>
- Findings detail: <for each finding -> ID | severity | location | summary | status(open/fixed/deferred); use `none` when empty>
- Final gate: <pending/not-run/pass/fail/skipped(strict_mode=false) + workflow + short reason>
- Fixed in this round: <ID list>
- Verification run: <commands>
- Verification result: <pass/fail + short reason>
- Continue?: <yes/no + reason>
```

## Final Clean Evidence (Required)

When the loop exits because findings are zero, include this evidence block in the final response:

```markdown
Final Clean Evidence
- Clean round: <Round N>
- Review range: <BASE_SHA>..<HEAD_SHA>
- Loop clean workflow: <$requesting-code-review result path used for the clean round>
- Loop clean evidence: <verbatim short line or artifact reference showing "no findings" / empty findings result>
- Final gate: <pass/fail/skipped(strict_mode=false)>
- Final gate workflow: <$requesting-code-review result path | n/a>
- Final gate evidence: <verbatim short line or artifact reference showing "no findings" / empty findings result | n/a when skipped>
- Normalized checklist: [] (0 items)
- Verification run: <commands>
- Verification result: <pass>
```

Rules:
- "No findings" must be evidenced, not asserted.
- Prefer direct reviewer output text; if unavailable, provide a saved artifact/log reference plus extracted empty checklist.
- Final gate result must be included explicitly (`pass/fail` for `strict_mode=true`, `skipped` for `strict_mode=false`).
- Do not finish without this block.

## Active Work Item Integration

When this skill is called from a parent workflow that tracks an active work item:

- Accept `base_sha=<sha>` from the caller and keep it fixed until the loop ends.
- Treat `HEAD_SHA` as the current tip for that same work item after each fix commit.
- Do not silently fall back to whole-branch review when the caller supplied `base_sha`.
- If `$requesting-code-review` cannot honor the requested `BASE_SHA..HEAD_SHA` range, stop and report the constraint instead of widening scope silently.

## Example Trigger Phrases

- "レビューして、指摘ゼロまで直し続けて"
- "Keep reviewing and fixing until clean"
- "Pre-merge quality gate: no review findings allowed"
- "$requesting-code-review と $receiving-code-review を使って、指摘ゼロまで繰り返して"
