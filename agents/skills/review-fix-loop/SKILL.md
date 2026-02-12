---
name: review-fix-loop
description: Use when the user asks to repeatedly run code review and apply fixes until review findings are zero, especially for requests like "review and fix until clean", "auto re-review loop", or strict pre-merge quality gates.
---

# Review Fix Loop

## Overview

Run a strict "review -> fix -> review" cycle without stopping after the first pass.
Continue until no actionable findings remain or a hard stop condition is met.
In Codex runtime, the primary review path is `codex review --base <branch>`.

**REQUIRED SUB-SKILL:** Use `$requesting-code-review` for review rubric/context quality.
**REQUIRED SUB-SKILL:** Use `$receiving-code-review` to evaluate and apply feedback rigorously.
**REQUIRED SUB-SKILL:** Use `superpowers:verification-before-completion` before claiming completion.
**PRECEDENCE RULE:** If this skill conflicts with `$requesting-code-review` on invocation mechanics, this skill wins.

## Review Invocation Contract

Choose review method once at Round 1 and keep it fixed for the entire loop.
Do not improvise per round.

### Method Priority (deterministic)

1. If `codex` CLI is available, use `codex review --base origin/<comparison_branch>`.
2. Else if slash command `/review` is available, use `/review` with the filled `requesting-code-review/code-reviewer.md` template.
3. Else use Task fallback with `superpowers:code-reviewer` and the same template.

### Codex Route Rules (strict)

- Command per round: `codex review --base origin/<comparison_branch> | tee /tmp/review_round<N>_output.txt`
- Allowed with `--base`: no prompt argument and no stdin prompt (`-`).
- Forbidden combination: `codex review --base ... -` or any `[PROMPT]` with `--base` (this errors).
- Do not run `codex review --help` during loop rounds; treat this contract as fixed.
- If you want template context for traceability, save it as artifact only (do not feed it to `codex review --base`).

## Sub-Skill Contract

For every loop round, apply both skills explicitly:

1. Review acquisition must follow `$requesting-code-review`.
   - Get SHAs (`BASE_SHA`, `HEAD_SHA`).
   - In Codex runtime, run `codex review --base origin/<comparison_branch>` and save output artifact for the round.
   - Use `requesting-code-review/code-reviewer.md` as checklist context artifact when needed, but do not pass it as prompt with `--base`.
   - Outside Codex runtime, follow `/review` -> Task fallback order with the same template.
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
   - Pin `review_method` once using Method Priority above. Do not switch method mid-loop unless the selected method is unavailable due hard runtime failure.
   - Resolve `BASE_SHA` from comparison target (recommended: `git merge-base origin/<comparison_branch> HEAD`).
   - Set current `HEAD_SHA` (`git rev-parse HEAD`).
   - Capture acceptance requirements (issue, plan, or explicit user request).
2. Run review round `N`.
   - Run the pinned `review_method` for the current branch range (`BASE_SHA` -> `HEAD_SHA`).
   - For Codex route, run exactly: `codex review --base origin/<comparison_branch> | tee /tmp/review_round<N>_output.txt`.
   - Normalize findings into a checklist with unique IDs:
     - `R<N>-C#` for Critical
     - `R<N>-I#` for Important
     - `R<N>-M#` for Minor
   - Publish the round report with per-finding detail (ID, severity, location, summary, status). Do not output counts only.
3. Decide continuation.
   - If checklist is empty: still publish this round report with `Findings detail: none` and then go to final verification.
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
- Use the current existing worktree throughout; worktree recreation is out of scope.
- Every review round must record review method (`codex review --base`, slash `/review`, or Task fallback) and range (`BASE_SHA..HEAD_SHA`).
- Every review round must output the concrete finding list; summary counts alone are not acceptable.
- If a round has zero findings, output `Findings detail: none` explicitly.
- In Codex route, every round must retain reviewer artifact log at `/tmp/review_round<N>_output.txt`.
- Never declare "done" without a final clean review pass and verification evidence.

## Round Report Format

Use this compact structure every round:

```markdown
Round N/5
- Review range: <BASE_SHA>..<HEAD_SHA>
- Review method: <`codex review --base origin/<comparison_branch>` | slash command `/review` | Task(superpowers:code-reviewer)>
- Reviewer artifact: </tmp/review_round<N>_output.txt | n/a>
- Fix commit: <hash/none>
- Worktree: existing worktree (no recreation)
- Findings: Critical=<n>, Important=<n>, Minor=<n>
- Findings detail: <for each finding -> ID | severity | location | summary | status(open/fixed/deferred); use `none` when empty>
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
- Review method: <`codex review --base origin/<comparison_branch>` | slash command `/review` | Task(superpowers:code-reviewer)>
- Reviewer artifact: </tmp/review_round<N>_output.txt | n/a>
- Reviewer evidence: <verbatim short line or artifact reference showing "no findings" / empty findings result>
- Normalized checklist: [] (0 items)
- Verification run: <commands>
- Verification result: <pass>
```

Rules:
- "No findings" must be evidenced, not asserted.
- Prefer direct reviewer output text; if unavailable, provide a saved artifact/log reference plus extracted empty checklist.
- Do not finish without this block.

## Example Trigger Phrases

- "レビューして、指摘ゼロまで直し続けて"
- "Keep reviewing and fixing until clean"
- "Pre-merge quality gate: no review findings allowed"
- "$requesting-code-review と $receiving-code-review を使って、指摘ゼロまで繰り返して"
