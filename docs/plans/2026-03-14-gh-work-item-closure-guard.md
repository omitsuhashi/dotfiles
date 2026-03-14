# gh-work-item-implementer Closure Guard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `gh-work-item-implementer` の closure フローを Epic 非対応のガード付き経路に置き換え、Epic 誤閉鎖を防ぐ。

**Architecture:** closure は prose 直書きではなく `scripts/close_work_item.py` に寄せる。`SKILL.md` は active work item kind を明示し、その kind をスクリプトへ渡す。テストは `unittest` でスクリプト単体を検証する。

**Tech Stack:** Python 3, unittest, Markdown skill docs

---

### Task 1: 失敗テストで Epic 拒否を固定する

**Files:**
- Create: `agents/skills/gh-work-item-implementer/scripts/test_close_work_item.py`

**Step 1: Write the failing test**

`epic` を渡すと終了コード 2 で拒否するテストを書く。

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest agents.skills.gh-work-item-implementer.scripts.test_close_work_item -v`
Expected: FAIL because `close_work_item.py` does not exist yet.

### Task 2: 最小実装で close ガードを追加する

**Files:**
- Create: `agents/skills/gh-work-item-implementer/scripts/close_work_item.py`
- Modify: `agents/skills/gh-work-item-implementer/scripts/test_close_work_item.py`

**Step 1: Write minimal implementation**

`--kind issue|sub-issue` のみ許可し、`epic` は `argparse` の choices で拒否する。正常系は `gh issue close` を呼ぶ。

**Step 2: Run tests to verify they pass**

Run: `python3 -m unittest agents/skills/gh-work-item-implementer/scripts/test_close_work_item.py -v`
Expected: PASS

### Task 3: Skill 本文をガード経路に置き換える

**Files:**
- Modify: `agents/skills/gh-work-item-implementer/SKILL.md`

**Step 1: Update closure instructions**

`gh issue close` の直書きをやめ、`python3 "agents/skills/gh-work-item-implementer/scripts/close_work_item.py" ...` に置換する。`Issue` という表現は `active Issue unit` / `active work item kind` に寄せる。

**Step 2: Clarify compression handoff**

closure の前に `active kind` と `closable number` を handoff に必須化する。

### Task 4: Validate end-to-end

**Files:**
- Verify: `agents/skills/gh-work-item-implementer/SKILL.md`
- Verify: `agents/skills/gh-work-item-implementer/scripts/close_work_item.py`
- Verify: `agents/skills/gh-work-item-implementer/scripts/test_close_work_item.py`

**Step 1: Run script tests**

Run: `python3 -m unittest agents/skills/gh-work-item-implementer/scripts/test_close_work_item.py -v`
Expected: PASS

**Step 2: Run existing context tests**

Run: `python3 -m unittest agents/skills/gh-work-item-implementer/scripts/test_fetch_context.py -v`
Expected: PASS

**Step 3: Validate skill metadata**

Run: `python3 codex/skills/.system/skill-creator/scripts/quick_validate.py agents/skills/gh-work-item-implementer`
Expected: PASS
