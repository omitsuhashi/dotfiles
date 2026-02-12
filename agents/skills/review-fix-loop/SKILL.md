---
name: review-fix-loop
description: Use when the user asks to repeatedly run code review and apply fixes until review findings are zero, especially for requests like "review and fix until clean", "auto re-review loop", or strict pre-merge quality gates.
---

# Review Fix Loop

## Overview

Run a strict "review -> fix -> re-review" cycle without stopping after the first pass.
Continue until no actionable findings remain or a hard stop condition is met.

**REQUIRED REVIEW COMMAND:** Run `/review` explicitly in every review round.
**REQUIRED SUB-SKILL:** Use `$requesting-code-review` to run each review pass.
**REQUIRED SUB-SKILL:** Use `$receiving-code-review` to evaluate and apply feedback rigorously.
**REQUIRED SUB-SKILL:** Use `superpowers:verification-before-completion` before claiming completion.

## Sub-Skill Contract

For every loop round, apply both skills explicitly:

1. Review acquisition must follow `$requesting-code-review`.
   - Get SHAs (`BASE_SHA`, `HEAD_SHA`).
   - Request review by running `/review` explicitly using the `$requesting-code-review` template (`code-reviewer.md` in that skill).
2. Feedback handling and fixes must follow `$receiving-code-review`.
   - Use the full sequence: `READ -> UNDERSTAND -> VERIFY -> EVALUATE -> RESPOND -> IMPLEMENT`.
   - Do not apply suggestions blindly.
   - If any feedback item is unclear, stop and clarify before implementation.

## Defaults

Use these defaults unless the user overrides them:

- `comparison_branch`: `main` (override allowed, e.g. `release/2026-q1`)
- `max_rounds`: 10
- `severity_scope`: all findings (`Critical`, `Important`, `Minor`)
- `stop_on_repeated_findings`: stop when the same unresolved finding repeats for 2 consecutive rounds
- `commit_after_fix`: required (create a commit after each completed fix phase that has changes)
- `autonomy`: continue looping without asking after each round; ask only for blockers/ambiguity

## Loop Workflow

1. Prepare loop context.
   - Determine `comparison_branch` (default `main`; user may override).
   - Resolve `BASE_SHA` from comparison target (recommended: `git merge-base origin/<comparison_branch> HEAD`).
   - Set current `HEAD_SHA` (`git rev-parse HEAD`).
   - Capture acceptance requirements (issue, plan, or explicit user request).
2. Run review round `N`.
   - Run `$requesting-code-review` for the current branch range (`BASE_SHA` -> `HEAD_SHA`).
   - Invoke `/review` explicitly for that branch diff context (include `comparison_branch`, `BASE_SHA`, `HEAD_SHA`, and requirement context in the review request).
   - Normalize findings into a checklist with unique IDs:
     - `R<N>-C#` for Critical
     - `R<N>-I#` for Important
     - `R<N>-M#` for Minor
3. Decide continuation.
   - If checklist is empty: go to final verification and finish.
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
   - Recompute `HEAD_SHA` from the new commit and refresh branch diff context from `comparison_branch`.
   - Execute the next review round unconditionally.
   - Exit only when a Stop Condition is met.

## Stop Conditions

Stop the loop only when at least one condition is true:

1. No actionable findings remain in scope.
2. `max_rounds` is reached.
3. The same unresolved finding repeats for 2 rounds with no technically valid fix path.
4. Feedback conflicts with requirements and needs user decision.

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
- Re-review must be branch-based against `comparison_branch`, not per-commit-only.
- Re-review is mandatory after each committed fix round until findings are zero or another Stop Condition is met.
- Review the committed branch state against `comparison_branch` each round.
- Every review round must include an explicit `/review` invocation (no implicit-only review round).
- Use the current existing worktree throughout; worktree recreation is out of scope.
- Never declare "done" without a final clean review pass and verification evidence.

## Round Report Format

Use this compact structure every round:

```markdown
Round N/5
- Review range: <BASE_SHA>..<HEAD_SHA>
- Review command: /review (explicitly executed)
- Fix commit: <hash/none>
- Worktree: existing worktree (no recreation)
- Findings: Critical=<n>, Important=<n>, Minor=<n>
- Fixed in this round: <ID list>
- Verification run: <commands>
- Verification result: <pass/fail + short reason>
- Continue?: <yes/no + reason>
```

## Example Trigger Phrases

- "レビューして、指摘ゼロまで直し続けて"
- "Keep reviewing and fixing until clean"
- "Pre-merge quality gate: no review findings allowed"
- "$requesting-code-review と $receiving-code-review を使って、指摘ゼロまで繰り返して"
