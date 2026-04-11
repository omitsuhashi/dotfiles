---
name: llm-wiki
description: Use when building or maintaining a persistent knowledge base in Obsidian or another local Markdown wiki where raw sources stay immutable and the LLM incrementally updates wiki pages, index.md, and log.md. Covers bootstrap, ingest, query, and lint workflows for raw sources, entity/concept pages, synthesis notes, source citations, and schema guidance stored in AGENTS.md.
---

# LLM Wiki

## Overview

この skill は、ローカル Markdown wiki を都度再発見する RAG ではなく、蓄積される knowledge base として運用するためのものです。耐久性のある成果物は wiki であり、`raw/` は不変、`index.md` と `log.md` は毎回更新する前提で扱います。

作業のたびに、まずどの層を触るかを決めます。

- `raw/`: source of truth. Read only. Never edit.
- `wiki/`: LLM-managed pages. Create and update freely.
- `AGENTS.md`: schema and workflow contract. Update only when operating conventions need to change.

## Quick Workflow

1. Identify the mode: `bootstrap`, `ingest`, `query`, or `lint`.
2. Read only the matching reference file sections instead of loading everything.
3. Inspect `index.md` before touching wiki pages unless the task is pure bootstrap.
4. Update `log.md` for every ingest, durable query output, or lint pass.
5. If an answer creates durable value, file it back into the wiki instead of leaving it in chat only.

## Mode Entry Checks

### `bootstrap`

vault / repo の境界を確認し、`raw/`, `wiki/`, `index.md`, `log.md`, `AGENTS.md` の置き場所を確定します。新規 wiki を作るときは `assets/templates/` の雛形を使います。

Read:

- `references/schema-and-conventions.md`
- `references/operations.md`

### `ingest`

新しい source と `index.md`, `log.md`, 既存の関連ページを確認します。まず source summary を作るか更新し、その後で entity / concept / synthesis へ変更を波及させます。

Read:

- `references/operations.md`
- `references/schema-and-conventions.md`

### `query`

`index.md` から入り、関連する wiki page と必要な raw citation へ掘ります。まず maintained wiki を再利用して答え、再利用価値がある結果なら query note か synthesis page として保存し、`index.md` と `log.md` に登録します。

Read:

- `references/operations.md`
- `references/schema-and-conventions.md`

### `lint`

`index.md`, `log.md`, orphan page, contradictions, stale claim, 独立 page を持たない recurring concept を点検します。missing source や web 調査は、具体的な gap が見えたときだけ提案します。

Read:

- `references/operations.md`
- `references/schema-and-conventions.md`
- `references/optional-tooling.md` only if better search or reporting is needed

## Reference Map

- `references/operations.md`
  `bootstrap`, `ingest`, `query`, `lint` の標準手順とチェック項目。
- `references/schema-and-conventions.md`
  推奨ディレクトリ構成、page 種別、リンク規約、citation 規約、`index.md` / `log.md` 更新規約。
- `references/optional-tooling.md`
  Obsidian Web Clipper, local image handling, Dataview, Marp, `qmd` などの任意ツール。
- `assets/templates/`
  `AGENTS.md`, `index.md`, `log.md`, 各種 page の初期雛形。

## Common Mistakes

- `raw/` の source file を編集すること。
- 既存 wiki を見ずに記憶だけで答えること。
- page を更新したのに `index.md` や `log.md` を更新しないこと。
- 価値のある query output を chat にだけ残して wiki に還元しないこと。
- 全 reference を最初から読み込むこと。必要な section だけ読むこと。
