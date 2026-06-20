---
name: grill-to-pr-loop
description: Use when a user requests a repeatable development operating mode for large designs involving Grill with Docs, specs, issue decomposition, git worktrees, test review, goal loops, or PR review.
---

# Grill to PR Loop

## Overview

Coordinate a repo change from design interrogation to PR review without skipping human gates. Keep issue management local-first; use GitHub issues only as an optional remote mirror/tracking layer after approval. Treat `grill-with-docs` as the required front door: if it is unavailable, stop instead of approximating the workflow.

## Immediate Guard

Run the prerequisite check before design, issue, worktree, or PR actions:

```bash
python3 <skill-dir>/scripts/check_prereqs.py
```

If it reports missing `grill-with-docs`, stop and tell the user the skill must be installed first. Do not fall back to plain `grill-me` for this workflow because the required docs are part of the contract.

Read `references/workflow-contract.md` when executing the workflow, resuming from a middle state, creating multiple worktrees, or preparing a Goal prompt.

## Required Operating Rules

- Load and follow repo instructions first: `AGENTS.md`, local skill routers, specs, tests, and CI docs.
- Preserve user work. Inspect `git status --short` and `git worktree list` before changing branches or creating worktrees.
- Keep design decisions in durable docs, not only chat. Prefer repo-local conventions; otherwise write a spec under `docs/grill-to-pr-loop/`.
- Split work into independently reviewable vertical slices in a local issue ledger. Write issue titles, headings, labels, status values, and prose in Japanese; keep IDs, paths, commands, code symbols, and external error text unchanged.
- Build an explicit blocker graph for local issues. Track `ブロック元`, `ブロック先`, and `実行可能/ブロック中` status before any worktree or Goal loop starts.
- Use `to-issues` only for draft breakdown and quiz/review if installed; do not run its publish phase unless this skill's GitHub mirror gate has passed.
- Mirror approved local issues to GitHub only when GitHub access is available, the repo has a GitHub remote, and the user explicitly approves remote issue creation.
- Create one branch and one worktree per approved `実行可能` issue. Do not create worktrees for `ブロック中` issues until their blockers are complete or the user explicitly overrides the dependency.
- Pause for human approval after spec, issue breakdown, proposed worktree map, and initial verification are ready.
- After approval, run the Goal loop per issue/worktree with a short prompt and links to durable docs.
- Before GitHub issue creation, push, PR creation, or any external write, get explicit user approval, then use the relevant GitHub/PR skill or repo convention. Never hide remote writes, permission, billing, or credential actions inside this workflow.

## State Machine

1. **Intake**: Confirm repo root, active branch, dirty state, target outcome, and whether existing spec/issues/PRs already exist.
2. **Grill**: Use `grill-with-docs` to resolve design choices and produce docs. If the user already has docs, review them for unresolved decisions before continuing.
3. **Spec**: Create or update a concise spec with accepted decisions, non-goals, acceptance criteria, verification commands, and rollback/stop conditions.
4. **Spec Gate**: Present the spec and wait for explicit approval before issue decomposition.
5. **Local Issues**: Decompose the approved spec into Japanese vertical-slice issues with acceptance criteria and a blocker graph. Write generated issue headings, labels, status values, and prose in Japanese. Write them to a local issue ledger and ask for approval of granularity, blocker edges, and dependency order.
6. **Optional GitHub Mirror**: If GitHub access is available and the user approves, create GitHub issues from the approved local issues and record the remote issue URLs. If GitHub is unavailable or not approved, continue local-only.
7. **Proposed Worktree Map**: Propose branch/worktree paths for approved `実行可能` local issues before running `git worktree add`.
8. **Worktree Gate**: Wait for explicit approval of the proposed worktree map, then create isolated worktrees. Record local issue, optional remote issue, branch, worktree path, base commit, owner/agent, and status.
9. **Initial Verification Gate**: Run available lightweight verification, summarize the spec/issues/worktree map, and ask the user to approve starting implementation loops.
10. **Goal Loop**: For each approved worktree, run implementation to completion: TDD or existing test discipline, focused changes, fresh verification, code review, fixes, and commit.
11. **PR Review**: After explicit approval for remote writes, open draft or ready PRs according to repo convention. If a remote issue exists, link the PR to it with the repo's preferred `Closes` or `Refs` syntax. Monitor checks/review comments, address actionable feedback, and report remaining risks.

## Goal Prompt Contract

For each issue, keep the prompt short and point at source artifacts:

- Local issue identifier and title.
- GitHub issue URL or number if a remote mirror was created.
- Blocker status: `実行可能` or `ブロック中`, plus `ブロック元` issue IDs.
- Spec path and any ADR/glossary paths from Grill with Docs.
- Worktree path and branch.
- Required behavior and acceptance criteria.
- Verification commands to run fresh after docs/progress updates.
- Stop conditions requiring the human.

Do not paste the full spec into the Goal prompt when a durable path exists.

## Stop Conditions

Stop and ask the user before continuing if:

- `grill-with-docs` is missing.
- The repo has dirty changes that overlap with the planned branches.
- The blocker graph is cyclic, ambiguous, or makes parallel work unsafe.
- A Goal loop is requested for a `ブロック中` issue without explicit override.
- The user requested GitHub issue/PR linkage but GitHub access, repo remote, or permission is unavailable; ask whether to continue local-only.
- Tests fail in a way unrelated to the issue and no local contract explains it.
- A GitHub issue, PR, push, credential, permission, production, billing, or external-write action is required and has not been approved.
- Human review rejects the spec, issue split, worktree map, or implementation result.

## Completion Report

End with:

- Spec/docs paths.
- Local issue list and status.
- GitHub issue links when created, or explicit local-only reason.
- Worktree/branch map.
- Verification commands and results.
- PR URLs or explicit reason PR creation was not done.
- Residual risks and unresolved human decisions.
