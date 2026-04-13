---
name: llm-wiki
description: Use when building or maintaining a persistent knowledge base in a local Markdown wiki (Obsidian-friendly) where raw sources stay immutable and the LLM incrementally updates wiki pages, index.md, and log.md. Covers bootstrap, ingest, query, and lint workflows for raw sources, entity/concept pages, durable Markdown outputs, citations, and schema guidance stored in AGENTS.md.
---

# LLM Wiki

## Overview

この skill は、local Markdown wiki（Obsidian-friendly）を都度再発見する RAG ではなく、蓄積される knowledge base として運用するためのものです。耐久性のある成果物は wiki であり、`raw/` は不変、`index.md` と `log.md` は first-class の運用ファイルとして扱います。wiki documentation は本文を日本語で保つことを基本にします。

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
6. Pause only for ambiguous, high-impact, or multi-page changes. Routine low-risk updates proceed autonomously.

## Mode Entry Checks

### `bootstrap`

wiki / repo の境界を確認し、`raw/`, `wiki/`, `index.md`, `log.md`, `AGENTS.md` の置き場所を確定します。新規 wiki を作るときは `assets/templates/` の雛形を使います。構成や命名に複数の妥当案があり、後戻りコストが高いときだけ user と揃えます。

Read:

- `references/schema-and-conventions.md`
- `references/operations.md`

### `ingest`

新しい source と `index.md`, `log.md`, 既存の関連ページを確認します。まず source summary を作るか更新し、その後で entity / concept / synthesis へ変更を波及させます。1 source が複数 page 境界を崩しそう、または解釈が割れるときだけ立ち止まって揃えます。

Read:

- `references/operations.md`
- `references/schema-and-conventions.md`

### `query`

`index.md` から入り、関連する wiki page と必要な raw citation へ掘ります。まず maintained wiki を再利用して答え、再利用価値がある結果なら query note か synthesis page として保存し、`index.md` と `log.md` に登録します。保存先や page boundary が曖昧で、既存 page を広く組み替える必要があるときだけ user と揃えます。

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
  `bootstrap`, `ingest`, `query`, `lint` の標準手順、pause rules、page lifecycle の実務ルール。
- `references/schema-and-conventions.md`
  推奨ディレクトリ構成、page 種別、page boundary、canonicalization、リンク規約、citation 規約、`index.md` / `log.md` 更新規約。
- `references/optional-tooling.md`
  Obsidian Web Clipper, local image handling, Dataview, Marp, `qmd` などの任意ツール。どれも必須ではありません。
- `assets/templates/`
  `AGENTS.md`, `index.md`, `log.md`, source/entity/concept/synthesis/query note の初期雛形。

## Common Mistakes

- `raw/` の source file を編集すること。
- 既存 wiki を見ずに記憶だけで答えること。
- page を更新したのに `index.md` や `log.md` を更新しないこと。
- 価値のある query output を chat にだけ残して wiki に還元しないこと。
- 重複 page を見つけても canonical page を決めずに増やし続けること。
- wiki documentation を英語へ寄せて、継続運用の読みやすさを落とすこと。
- 全 reference を最初から読み込むこと。必要な section だけ読むこと。
