# LLM Wiki Router

この directory は persistent な LLM-maintained wiki の knowledge root です。

## Canonical Procedure

- wiki の `bootstrap`, `ingest`, `query`, `lint`, page lifecycle の汎用手順は `llm-wiki` スキルを canonical source として扱う
- 汎用的な schema, naming, citation, canonicalization, `index.md` / `log.md` 更新規約も `llm-wiki` スキルに従う
- この file はスキルの複製ではなく、この knowledge root 固有の前提と差分だけを書く

## Local Contract

- knowledge root はこの directory とする
- `raw/` は不変の source material として扱い、読んでも編集しない
- `wiki/` は maintained knowledge base として扱い、作成と更新はここで行う
- `index.md` は durable wiki page の catalog として扱う
- `log.md` は bootstrap, ingest, query, lint, lifecycle action の append-only timeline として扱う
- wiki documentation の本文は日本語を基本にする
- superpowers など他 workflow が作る durable な roadmap / ADR / spec / design doc / implementation plan も knowledge root 配下へ保存する
- default routing は、roadmap / ADR / spec / design doc / implementation plan / briefing / comparison note を `wiki/syntheses/`、質問起点の短い判断メモを `wiki/queries/` とする

## Local Overrides

- この knowledge root 固有の命名規則、page type の追加、frontmatter 規約、link 規約、durable doc の保存先 override がある場合だけここへ追記する
- 汎用運用ルールをここへ再掲しない

## Conflict Rule

- この file の local rule が `llm-wiki` スキルと衝突する場合は、この file をこの knowledge root の優先ルールとして扱う
