# gh-work-item-implementer Closure Guard Design

**Goal:** `gh-work-item-implementer` から Epic が誤って閉じられないようにし、Issue/Sub-issue のみを閉じる経路へ限定する。

## Context

現行の skill は `gh issue close` を本文に直接書いており、`Issue` と `Epic` の区別が prose 依存になっている。GitHub 上では Epic も issue として扱われるため、`Issue を閉じる` という一般表現だけでは誤解釈を防げない。

## Approach

1. 閉鎖操作を `scripts/close_work_item.py` に集約する。
2. スクリプトは `--kind sub-issue|issue` のみ受け付け、`epic` は即失敗させる。
3. `SKILL.md` は `gh issue close` の直書きをやめ、ガードスクリプト経由へ置き換える。
4. 実行中の文脈圧縮で target Epic と active work item を混同しないよう、closure 前に `active kind` を明示する指示へ寄せる。

## Non-Goals

- GitHub API から Epic/Issue 判定を再取得する高機能ランタイムは作らない。
- `fetch_context.py` の hierarchy モデルは今回は変更しない。
- skill 全体のワークフロー再設計は行わない。

## Verification

- `scripts/test_close_work_item.py` で `epic` を拒否する失敗ケースを先に固定する。
- 正常系として `issue` と `sub-issue` で `gh issue close` が組み立てられることを確認する。
- `scripts/quick_validate.py` で skill の基本整合性を確認する。
