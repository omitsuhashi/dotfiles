---
name: epic-subissue-runner
description: Use when running epic sub-issues where each sub-issue must be committed and closed, and ambiguity must halt progress.
disable-model-invocation: true
argument-hint: [epic-issue]
allowed-tools: Read, Grep, Glob, Edit, Bash(git:*), Bash(gh:*), Bash(bash:*)
---

# Epic Sub-issue Runner (worktree-based)

## Epic本文で doc submodule の参照先を指定できる
以下のどちらかで指定する（どちらも無い場合は pin しない＝現状の submodule commit のまま）。
pin は worktree 準備時に反映される前提（このスキル内で worktree 操作はしない）。

### A) 明示（推奨）
```
## SubmodulePins
- doc=issue:123        # doc repo の epic/123 ブランチ先端を pin
# - doc=pr:456
# - doc=branch:epic/123
# - doc=sha:deadbeef...
```

### B) DependsOn から推測
```
## DependsOn
- https://github.com/<owner>/<doc-repo>/issues/123
```

## 前提/ポリシー（ユーザー指定）
- 起動時に **Epic用 worktree ブランチ** 上だけで作業する（sub-issueごとに別ブランチは作らない）
- worktree は事前に用意済み（このスキルでは作成/削除/移動/切替を行わない）
- sub-issue は **Issue本文（本文・チェックリスト・Acceptance Criteria）を唯一の仕様**として実行する（推測しない）
- コミットは **最低でも sub-issue 完了時に1回** 必須（途中コミットは可）
- sub-issue が完了したら **Issueのstatusを完了**にする（このスキルでは `gh issue close -r completed` を採用）
- sub-issue が全て完了したら **Epicも完了**にする（同様に close）
- 曖昧/矛盾/不足があれば **そこで停止し、依頼者に確認**（勝手に進めない）
- ここで言っているscriptsはこのskillの配下にあるscripts/であることを認識

## 起動引数
- `$ARGUMENTS`: Epic issue（番号/URL/owner-repo#N 等、`gh issue view` が解釈できる形式）

## 実行手順（必ずこの順序）
0) **サブモジュールを同期（必須）**
   - `git submodule sync --recursive`
   - `git submodule update --init --recursive`

1) **epicで全体像を把握**
   - 指定したepic本文から全体像を把握する

2) **sub-issue 一覧を抽出**
   - `bash "$HOME/.codex/skills/epic-subissue-runner/scripts/list_subissues.sh" "$ARGUMENTS"` を実行
   - Sub-issues API を最優先で取得し、0件/失敗時のみ Epic本文の `- [ ]` タスク行から抽出（`- [x]` はスキップ）

3) **sub-issue を順に処理（各件で必須）**
   - 作業ディレクトリは現在の worktree 固定（このスキルでの `cd` はしない）
   - `gh issue view <sub>` で本文を読み、本文に従って実装する
   - 曖昧/衝突/不足（例：期待I/O不明、影響範囲が複数解釈、手順が矛盾）なら **即停止して依頼者に確認**
   - 実装中の途中コミットは任意。ただし **完了時には最低1コミット** 必須
     - もし「変更が不要」なら `git commit --allow-empty` を使って “完了記録” を残す
   - 完了前ゲート
     - `bash "$HOME/.codex/skills/epic-subissue-runner/scripts/run_issue_gates.sh"`
     - 失敗したら停止（修正 or 依頼者確認）
     - 成功したら その後に commit
   - 完了したらPRを作成

## 禁止事項
- Issue本文にない仕様の追加・自己判断での要件補完
- 依頼者確認が必要な曖昧点を抱えたままの続行
- epicを閉じたり、statusを完了にしたりしないこと
- worktree の作成/削除/移動/切替
