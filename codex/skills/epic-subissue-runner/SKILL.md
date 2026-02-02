---
name: epic-subissue-runner
description: Commit at least once per sub-issue; close issues when complete; stop on ambiguity.
disable-model-invocation: true
argument-hint: [epic-issue]
allowed-tools: Read, Grep, Glob, Edit, Bash(git:*), Bash(gh:*)
---

# Epic Sub-issue Runner (worktree-based)

## 前提/ポリシー（ユーザー指定）
- 起動時に **Epic用 worktree ブランチ** 上だけで作業する（sub-issueごとに別ブランチは作らない）
- sub-issue は **Issue本文（本文・チェックリスト・Acceptance Criteria）を唯一の仕様**として実行する（推測しない）
- コミットは **最低でも sub-issue 完了時に1回** 必須（途中コミットは可）
- sub-issue が完了したら **Issueのstatusを完了**にする（このスキルでは `gh issue close -r completed` を採用）
- sub-issue が全て完了したら **Epicも完了**にする（同様に close）
- 曖昧/矛盾/不足があれば **そこで停止し、依頼者に確認**（勝手に進めない）
- ここで言っているscriptsはこのskillの配下にあるscripts/であることを認識

## 起動引数
- `$ARGUMENTS`: Epic issue（番号/URL/owner-repo#N 等、`gh issue view` が解釈できる形式）

## 実行手順（必ずこの順序）
1) **作業場所を検証（必須）**
   - 事前に依頼者が作成した **Epic用 worktree ディレクトリで Codex を起動**していること
   - `scripts/assert_worktree.sh` を実行し、OK になるまで進めない
   - default branch 上なら停止（依頼者に確認してもらう）

2) **epicで全体像を把握**
   - 指定したepic本文から全体像を把握する

3) **sub-issue 一覧を抽出**
   - `scripts/list_subissues.sh $ARGUMENTS` を実行
   - Sub-issues API を最優先で取得し、0件/失敗時のみ Epic本文の `- [ ]` タスク行から抽出（`- [x]` はスキップ）

4) **sub-issue を順に処理（各件で必須）**
   - `gh issue view <sub>` で本文を読み、本文に従って実装する
   - 曖昧/衝突/不足（例：期待I/O不明、影響範囲が複数解釈、手順が矛盾）なら **即停止して依頼者に確認**
   - 実装中の途中コミットは任意。ただし **完了時には最低1コミット** 必須
     - もし「変更が不要」なら `git commit --allow-empty` を使って “完了記録” を残す
   - 完了前ゲート
     - worktree で bash scripts/run_issue_gates.sh を実行
     - 失敗したら停止（修正 or 依頼者確認）
     - 成功したら その後に commit
   - 完了したらPRを作成

## 禁止事項
- Issue本文にない仕様の追加・自己判断での要件補完
- 依頼者確認が必要な曖昧点を抱えたままの続行
- epicを閉じたり、statusを完了にしたりしないこと

