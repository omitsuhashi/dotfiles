# Schema And Conventions

新規 wiki を作るとき、または構造ルールを変えるときに読みます。

## Default Layout

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

### Layer Rules

- `raw/` は不変の source material として扱う。
- `wiki/` は LLM が保守する working knowledge として扱う。
- `AGENTS.md` は後続 session 向けの operating contract として扱う。
- `index.md` は catalog として扱う。
- `log.md` は chronological ledger として扱う。

## Page Types

### `wiki/sources/`

source summary 用です。主要 claim、この source が重要な理由、open question、entity / concept / synthesis への outbound link を持たせます。

### `wiki/entities/`

人、組織、製品、場所、登場人物などの named thing 用です。identity, timeline, claim, 関連 source summary への link を集約します。

### `wiki/concepts/`

複数 source をまたぐ theme, method, argument, framework, recurring idea 用です。

### `wiki/syntheses/`

比較、thesis、timeline、due diligence note、定期 briefing などの上位 synthesis 用です。

### `wiki/queries/`

質問から始まったが保存価値がある回答用です。

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

## Linking Rules

- `[[LLM Wiki Architecture]]` のような Obsidian wikilink を優先する。
- summary page から entity / concept / synthesis へ outward link を張る。
- 新しい durable page には最低 1 本の inbound link を作る。
- 強く重なる 2 page は明示的に link し、境界を説明する。

## Citation Rules

- durable page には `## Sources` section を置く。
- 関連する raw file か source summary page へ戻れるようにする。
- 争点がある claim や驚く claim は、平坦化せず inline で disagreement を書く。

推奨 citation パターン:

```markdown
## Sources

- [[2026-04-12 Article Title]]
- [[raw/sources/article-title.md]]
```

## `index.md` Rules

`index.md` は最初の lookup surface として扱います。

- page type ごとに整理する。
- durable wiki page を 1 回ずつ載せる。
- 各 page に 1 行 summary を付ける。
- frontmatter を安定運用しているなら updated date や source count を足してよい。

良い entry パターン:

```markdown
- [[Persistent Knowledge Base]] — query-time retrieval ではなく compiled layer として wiki を扱う理由を定義する。
```

## `log.md` Rules

`log.md` は append-only で扱います。

- bootstrap, ingest, query filing, lint pass ごとに 1 entry
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
