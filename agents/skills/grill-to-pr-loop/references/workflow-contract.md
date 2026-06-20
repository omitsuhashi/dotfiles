# Grill to PR Loop Workflow Contract

Use this reference for execution details after loading `grill-to-pr-loop`.

## Artifact Contract

Prefer repo-local conventions. If none exist, use:

- Spec: `docs/grill-to-pr-loop/<topic>-spec.md`
- Local issue ledger: `docs/grill-to-pr-loop/<topic>-issues.md`
- Worktree map: `docs/grill-to-pr-loop/<topic>-worktrees.md`
- Goal prompt snippets: `docs/grill-to-pr-loop/goals/<issue-slug>.md`

For repos with a knowledge wiki or Goal convention, keep the short prompt separate from the detailed contract. Put durable detail in the repo's canonical spec/synthesis location and link to it from the prompt.

## Spec Minimum

The spec must contain:

- Problem statement and success criteria.
- Accepted decisions from Grill with Docs.
- Non-goals.
- Issue decomposition strategy.
- Acceptance criteria.
- Verification commands.
- Human review gates.
- Stop conditions and known risks.

Self-review the spec for placeholders, contradictory decisions, ambiguous acceptance criteria, stale paths, and hidden implementation assumptions.

## Local-First Issue Policy

Local issues are the source of truth for decomposition. Write local issue titles, headings, field labels, status values, ledger labels, blocker summaries, and prose in Japanese. Keep stable IDs, file paths, commands, code symbols, API names, branch names, error messages, and external issue/PR references in their original form.

GitHub issues are optional mirrors for collaboration and PR traceability. When creating GitHub issues, write titles, headings, labels, status values, and prose in Japanese using the same local issue contract.

Do not use English display labels such as `Ready`, `Blocked`, `Blocked by`, `Blocks`, `None`, or `Not created` in generated issues or ledgers. Use `実行可能`, `ブロック中`, `ブロック元`, `ブロック先`, `なし`, and `未作成` instead. Only keep English when it is a command, path, identifier, product name, API name, branch name, URL, or copied external error text.

Local ledgers must use these `レビュー状態` values: `下書き`, `承認済み`, `差し戻し`, `未解決`. Do not use `approved`, `rejected`, `draft`, or `unresolved` as generated review state values.

Use local-only mode by default when:

- The user has not explicitly approved remote issue creation.
- GitHub access, authentication, or permissions are unavailable.
- The repo has no GitHub remote.
- The issue split is still under review.

Use GitHub mirror mode only after local issue approval. Record the relationship in the local ledger:

```markdown
| ローカルID | タイトル | レビュー状態 | 実行状態 | ブロック元 | ブロック先 | GitHub Issue | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G2PR-001 | <日本語タイトル> | 承認済み | 実行可能 | なし | G2PR-002 | https://github.com/<org>/<repo>/issues/<n> | 未作成 |
```

If GitHub publication fails, keep the approved local ledger intact and ask whether to continue local-only.

## ブロッカーグラフ

Build a blocker graph before the Issue Gate. Treat each blocker edge as `blocked issue -> required prerequisite`.

Rules:

- Every local issue must declare `ブロック元`.
- Every local issue should declare `ブロック先` when known.
- `実行可能` means `ブロック元` is `なし` or all blockers are completed.
- `ブロック中` means at least one blocker is not completed.
- Parallel work may start only for `実行可能` issues with no dependency edge between them.
- Worktree creation and Goal loops are allowed only for `実行可能` issues unless the user explicitly overrides the blocker.
- Detect cycles. If a cycle exists, stop and ask the user to revise the issue split or blocker graph.
- When a blocker completes, update dependent issues from `ブロック中` to `実行可能` before proposing new worktrees.

Use this compact graph summary in the local ledger:

```markdown
## ブロッカーグラフ

- G2PR-001: 実行可能; ブロック先 G2PR-002, G2PR-003
- G2PR-002: ブロック中; ブロック元 G2PR-001
- G2PR-003: ブロック中; ブロック元 G2PR-001
```

## ローカルIssueテンプレート

Use vertical slices. Each issue should be independently verifiable. Write the title, headings, labels, status values, and prose in Japanese.

```markdown
## ローカルID

G2PR-<number>

## タイトル

<日本語の短いタイトル>

## 作るもの

<このスライスで実現する一連の振る舞い。>

## 受け入れ条件

- [ ] <観測可能な条件>
- [ ] <検証またはレビュー条件>

## ブロッカー

- 実行状態: <実行可能 または ブロック中>
- ブロック元: <ローカルIssue ID または なし>
- ブロック先: <ローカルIssue ID または なし>

## 必要な文脈

- 仕様: <path>
- ADR / 用語集 / 関連ドキュメント: <paths または なし>

## 検証

- <command>

## リモート追跡

- GitHub Issue: <URL または 未作成>
- PR: <URL または 未作成>
```

Avoid brittle file-path instructions unless a path is the stable public surface being changed.

## Optional GitHub Mirror Gate

Before creating GitHub issues:

1. Confirm the repo remote points to GitHub.
2. Confirm a GitHub app, MCP tool, or `gh` CLI is available and authenticated.
3. Present the exact local issues to publish, including `実行可能/ブロック中` status and blocker edges.
4. Ask for explicit approval to create remote issues.
5. Create one GitHub issue per approved local issue.
6. Update the local ledger with remote issue URLs.

Do not create GitHub issues for `差し戻し`, `下書き`, or `未解決` local issues. Local issues with `レビュー状態: 承認済み` and `実行状態: ブロック中` may be mirrored only when the GitHub Mirror Gate explicitly includes blocked tracking issues and the user approves them.

Remote issue bodies should preserve the Japanese local issue contract, blocker fields, and spec path. Use the repo's normal labels/milestones only when they are discoverable from repo docs or approved by the user.

If using `to-issues`, use only its context gathering, draft vertical-slice breakdown, and quiz/review phases until this gate passes. Do not let `to-issues` publish remote issues as a side effect before explicit GitHub mirror approval.

## Worktree Map

Propose this table before creating worktrees, and record it after approval:

```markdown
| ローカルIssue | GitHub Issue | ブランチ | 作業ツリー | ベース | 実行状態 | 準備状態 | 検証 | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G2PR-001 | #123 または ローカルのみ | codex/g2pr-001-slug | <path> | <sha> | 実行可能 | 準備済み | <commands> | 未作成 |
```

Default branch naming: `codex/<issue-id-or-slug>`. Use the repo's documented convention if it differs.

Default worktree placement: use the repo's existing worktree convention. If none exists, choose a sibling directory that includes the repo name and issue slug, then report it before implementation.

Do not include `ブロック中` issues in the proposed worktree map unless the user explicitly overrides the blocker. Do not run `git worktree add` until the user approves the proposed map.

## Approval Gates

Run these gates in order:

1. **Spec Gate**: Present the spec path, accepted decisions, non-goals, acceptance criteria, verification commands, and stop conditions. Wait for explicit approval before local issue decomposition.
2. **Issue Gate**: Present Japanese local issues, blocker graph, dependency order, `実行可能/ブロック中` status, and acceptance criteria. Wait for explicit approval before GitHub mirroring or worktree planning.
3. **GitHub Mirror Gate**: Optional. If the user wants remote tracking, present the exact local issues to publish, including blocked tracking issues if any, and wait for explicit approval before creating GitHub issues.
4. **Worktree Map Gate**: Present proposed branch/worktree paths, base commit, and dependency constraints. Wait for explicit approval before creating worktrees.
5. **Initial Verification Gate**: Run lightweight verification, summarize current artifacts, and wait for explicit approval before starting Goal loops.

Approval must be specific to the current gate packet. Vague approval from an earlier gate does not authorize later remote writes, worktree creation, pushes, or PR creation.

## Parallelization Rules

- Parallelize only `実行可能` issues with no dependency edge between them.
- Assign exactly one worktree per agent/thread.
- Do not let two agents edit the same worktree.
- Keep shared docs changes in a parent/prep issue when possible; otherwise serialize them.
- Rebase or merge only after checking the repo's contribution policy.
- Do not start a dependent branch until its blocker is complete unless the user explicitly approves stacked/dependent PR work.

## Review Gate Packet

Before Goal loops, present:

- Spec path and summary of accepted decisions.
- Issue list with blocker graph, `実行可能/ブロック中` status, and dependency order.
- Worktree map.
- Verification already run.
- Exact question: whether the user approves starting implementation loops.

Do not proceed on vague approval. Require approval of the current packet.

## Goal Loop Definition

For each approved issue:

1. Confirm the worktree path and branch.
2. Re-read the issue and spec.
3. Confirm the issue is `実行可能`. If it is `ブロック中`, stop unless the user explicitly approved an override.
4. Write or update tests first when behavior changes.
5. Implement the narrowest change that satisfies the issue.
6. Run targeted verification.
7. Update docs/progress required by the repo.
8. Run fresh final verification.
9. Request code review or perform a review pass.
10. Fix actionable findings.
11. Commit only the issue's scoped changes.
12. Mark completed blockers and update dependent issues from `ブロック中` to `実行可能` when applicable.

If the platform has a native Goal command, use it with the short prompt and linked docs. If not, execute the same loop manually and report that no native Goal runner was available.

## PR Review Definition

Create PRs only after final verification and review fixes. Prefer draft PRs when multiple dependent branches remain in flight. Include:

- What changed.
- Spec, local issue, and remote issue links when available.
- ブロッカー状態と、必要な場合は stacked/dependent PR の関係.
- Verification results.
- Known risks.
- Dependency/stacking notes.

If a GitHub issue exists, link the PR with the repo's preferred closing syntax:

- Use `Closes #<n>` when merging the PR should close the issue.
- Use `Refs #<n>` when the PR is partial, stacked, exploratory, or should not auto-close the issue.

If no GitHub issue exists, include the local issue ID and ledger path instead. Do not create a remote issue during PR creation unless the user explicitly approves that remote write.

Push and PR creation are remote writes. Use the relevant GitHub/PR skill or repo convention only after explicit user approval for the current branch/issue. For blocked or dependent work, prefer stacked draft PRs only when the user explicitly approves stacked/dependent PR work and the blocker PR relationship is documented. After PR creation, inspect checks and actionable review comments. Fix only scoped feedback in the same worktree/branch. For broad redesign requests, return to Grill with Docs or spec update.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Skipping Grill with Docs because the design seems obvious | Run it or stop if unavailable. |
| Creating horizontal layer issues | Rewrite as vertical slices that are independently verifiable. |
| Writing issues in English by habit | Write issue titles, headings, labels, status values, and prose in Japanese; keep technical identifiers unchanged. |
| Leaving English labels in issue templates | Replace `Ready`, `Blocked`, `Blocked by`, `Blocks`, `None`, and `Not created` with `実行可能`, `ブロック中`, `ブロック元`, `ブロック先`, `なし`, and `未作成`; replace review values with `下書き`, `承認済み`, `差し戻し`, or `未解決`. |
| Treating blockers as notes only | Maintain `ブロック元`, `ブロック先`, and `実行可能/ブロック中` status in the local ledger. |
| Treating GitHub as the default issue source | Keep local issues canonical; mirror only after approval. |
| Starting Goal loops before human review | Stop at the review packet and wait for approval. |
| Starting Goal loops for blocked issues | Wait until blockers complete or get explicit override for stacked/dependent work. |
| Reusing one worktree for multiple parallel issues | Create isolated worktrees and branches. |
| Putting full specs into Goal prompts | Keep prompts short and link durable docs. |
| Treating PR creation as implicit | Get explicit approval first, then use the repo's PR skill/convention. |
