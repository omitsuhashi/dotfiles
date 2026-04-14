# Schema And Conventions

新規 wiki を作るとき、または構造ルールを変えるときに読みます。

## Default Layout

まず knowledge root を 1 つ決めます。dedicated wiki repo なら repo root 自体を knowledge root にしてよく、mixed repo なら wiki 専用の subdirectory を knowledge root に切り出します。

### Recommended Layout For Mixed Repositories

```text
repo-root/
├── AGENTS.md
└── <knowledge-root>/
    ├── raw/
    │   ├── sources/
    │   └── assets/
    ├── wiki/
    │   ├── sources/
    │   ├── entities/
    │   ├── concepts/
    │   ├── syntheses/
    │   └── queries/
    ├── index.md
    ├── log.md
    └── AGENTS.md
```

- repo root の `AGENTS.md` は thin router として扱い、knowledge root の `AGENTS.md` への導線だけを置く。
- detailed な schema と workflow contract は knowledge root の `AGENTS.md` に置く。
- `raw/`, `wiki/`, `index.md`, `log.md` は knowledge root の内側に揃える。

### Default Layout For Dedicated Wiki Repositories

```text
repo-root/
├── raw/
│   ├── sources/
│   └── assets/
├── wiki/
│   ├── sources/
│   ├── entities/
│   ├── concepts/
│   ├── syntheses/
│   └── queries/
├── index.md
├── log.md
└── AGENTS.md
```

local Markdown wiki であればこの構成をそのまま使ってよく、Obsidian はその一例です。mixed repo でなければ、この layout でも問題ありません。

### Layer Rules

- `knowledge root` は wiki 運用の単位として扱う。
- `raw/` は不変の source material として扱う。
- `wiki/` は LLM が保守する working knowledge として扱う。
- knowledge root の `AGENTS.md` は後続 session 向けの operating contract として扱う。
- repo root の `AGENTS.md` は mixed repo のときだけ thin router として置いてよい。
- `index.md` は catalog として扱う。
- `log.md` は chronological ledger として扱う。
- durable な本文は日本語を基本にする。

## Page Types

### `wiki/sources/`

source summary 用です。主要 claim、この source が重要な理由、open question、entity / concept / synthesis への outbound link を持たせます。

### `wiki/entities/`

人、組織、製品、場所、登場人物などの named thing 用です。identity, timeline, claim, 関連 source summary への link を集約します。

### `wiki/concepts/`

複数 source をまたぐ theme, method, argument, framework, recurring idea 用です。

### `wiki/syntheses/`

比較、thesis、timeline、due diligence note、briefing、短い report などの上位 synthesis 用です。

### `wiki/queries/`

質問から始まったが保存価値がある回答、比較メモ、判断材料メモ、短報用です。

## Naming Defaults

- wiki page の filename は読みやすい Title Case を基本にする。
- 1 file 1 durable topic を守る。
- raw source の filename はそのまま保つ。
- chronology が重要な source summary や query note は date prefix を付ける。

推奨 filename パターン:

- `wiki/sources/2026-04-12 Article Title.md`
- `wiki/entities/Vannevar Bush.md`
- `wiki/concepts/Persistent Knowledge Base.md`
- `wiki/syntheses/LLM Wiki Architecture.md`
- `wiki/queries/2026-04-12 Compare RAG And LLM Wiki.md`

## Page Boundary And Canonicalization

- 1 file 1 durable topic を守る。
- 強く重なる page を見つけたら、どちらを canonical page にするか決める。
- canonical page は標準的な名前、明確な scope、継続参照しやすさを優先して選ぶ。
- rename / merge / archive は lightweight に扱い、後継 page と discoverability を残す。

rename / merge / archive を行ったら、最低限次を更新します。

- `index.md`
- `log.md`
- 触った page の link
- canonical page への inbound link

## Linking Rules

- Markdown link を基本にする。
- `[[LLM Wiki Architecture]]` のような wikilink は使える環境なら歓迎する。
- summary page から entity / concept / synthesis へ outward link を張る。
- 新しい durable page には最低 1 本の inbound link を作る。
- 強く重なる 2 page は明示的に link し、境界を説明する。

## Citation Rules

- durable page には `## 出典` section を置く。
- 関連する raw file か source summary page へ戻れるようにする。
- 争点がある claim や驚く claim は、平坦化せず inline で disagreement を書く。

推奨 citation パターン:

```markdown
## 出典

- [2026-04-12 Article Title](wiki/sources/2026-04-12%20Article%20Title.md)
- [raw/sources/article-title.md](raw/sources/article-title.md)
```

wikilink を使う環境なら、次のように置き換えても構いません。

```markdown
## 出典

- [[2026-04-12 Article Title]]
- [[raw/sources/article-title.md]]
```

## `index.md` Rules

`index.md` は最初の lookup surface として扱います。

- page type ごとに整理する。
- durable wiki page を 1 回ずつ載せる。
- 各 page に 1 行 summary を付ける。
- rename / merge / archive 後は canonical page だけを現役一覧に残す。
- frontmatter を安定運用しているなら updated date や source count を足してよい。

良い entry パターン:

```markdown
- [[Persistent Knowledge Base]] — query-time retrieval ではなく compiled layer として wiki を扱う理由を定義する。
```

## `log.md` Rules

`log.md` は append-only で扱います。

- bootstrap, ingest, query filing, lint pass ごとに 1 entry
- rename / merge / archive の lifecycle action も 1 entry
- 予測しやすい prefix で始める
- 何が変わり、どの page を触ったかを残す

推奨 entry header:

```markdown
## [2026-04-12] ingest | Article Title
```

こうしておくと shell tool で追いやすくなります。

```bash
grep '^## \[' log.md | tail -5
```

## Frontmatter Guidance

frontmatter は必須ではありませんが、Dataview や構造化 audit を使うなら推奨です。

最小限に保ちます。

```yaml
---
kind: concept
created: 2026-04-12
updated: 2026-04-12
tags:
  - llm-wiki
source_files:
  - raw/sources/article-title.md
---
```

実際に保守しない metadata は増やさないでください。
