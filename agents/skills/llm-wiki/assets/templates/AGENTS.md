# LLM Wiki Schema

この repository は persistent な LLM-maintained wiki です。毎 session で次のルールに従います。

## Layer Model

- `raw/` は不変の source material として扱い、読んでも編集しない。
- `wiki/` は maintained knowledge base として扱い、作成と更新はここで行う。
- `AGENTS.md` は operating contract として扱い、workflow 自体が変わるときだけ更新する。

## Required Files

- `index.md`: durable wiki page の catalog。type ごとに整理し、各 page に 1 行 summary を付ける
- `log.md`: bootstrap, ingest, query, lint の append-only timeline

## Operating Modes

### `bootstrap`

- `raw/` と `wiki/` の境界を確定する
- page type ごとの directory を確認する
- 無ければ `index.md` と `log.md` を作る

### `ingest`

- `raw/` から新しい source を読む
- source summary を作るか更新する
- 重要な変化を entity, concept, synthesis に波及させる
- `index.md` を更新し、`log.md` に追記する

### `query`

- `index.md` から始める
- raw source を開き直す前に maintained wiki page を再利用する
- durable な回答は `wiki/queries/` か `wiki/syntheses/` へ戻す
- durable artifact を作ったら `index.md` と `log.md` を更新する

### `lint`

- contradiction, stale claim, orphan page, missing cross-link を探す
- 足りない情報が具体的なときだけ targeted な source gap を提案する
- findings と fixes を `log.md` に記録する

## Writing Rules

- 1 page 1 durable topic を守る
- Obsidian wikilink を優先する
- durable page には `## Sources` section を置く
- 黙って上書きせず disagreement を記録する
- wiki の整合を保つために必要な page 数だけ触る
