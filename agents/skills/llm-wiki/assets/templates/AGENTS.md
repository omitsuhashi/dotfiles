# LLM Wiki 運用契約

この repository は persistent な LLM-maintained wiki です。毎 session で次のルールに従います。

## レイヤーモデル

- `raw/` は不変の source material として扱い、読んでも編集しない。
- `wiki/` は maintained knowledge base として扱い、作成と更新はここで行う。
- `AGENTS.md` は operating contract として扱い、workflow 自体が変わるときだけ更新する。

## 必須ファイル

- `index.md`: durable wiki page の catalog。type ごとに整理し、各 page に 1 行 summary を付ける
- `log.md`: bootstrap, ingest, query, lint, lifecycle action の append-only timeline

## 記述ルール

- wiki documentation の本文は日本語を基本にする
- local Markdown wiki として読める形を優先し、Obsidian は使える環境での最適化例として扱う
- 1 page 1 durable topic を守る
- Markdown link を基本にし、wikilink は使える環境なら歓迎する
- durable page には `## 出典` section を置く
- 黙って上書きせず disagreement を記録する
- wiki の整合を保つために必要な page 数だけ触る

## 運用モード

### `bootstrap`

- `raw/` と `wiki/` の境界を確定する
- page type ごとの directory を確認する
- 無ければ `index.md` と `log.md` を作る
- 構成や命名に複数の妥当案があり、後戻りコストが高いときだけ user と揃える

### `ingest`

- `raw/` から新しい source を読む
- source summary を作るか更新する
- 重要な変化を entity, concept, synthesis に波及させる
- `index.md` を更新し、`log.md` に追記する
- 1 source が複数 page 境界を崩しそう、または解釈が割れるときだけ止まる

### `query`

- `index.md` から始める
- raw source を開き直す前に maintained wiki page を再利用する
- durable な回答は `wiki/queries/` か `wiki/syntheses/` へ戻す
- durable artifact を作ったら `index.md` と `log.md` を更新する
- 保存先や page boundary が曖昧で大きな再編が必要なときだけ user と揃える

### `lint`

- contradiction, stale claim, orphan page, missing cross-link を探す
- 足りない情報が具体的なときだけ targeted な source gap を提案する
- findings と fixes を `log.md` に記録する

## ページライフサイクル

- duplicate や強い重なりを見つけたら canonical page を 1 つ決める
- rename は canonical 名称へ寄せ、必要なら旧 page を短い案内 stub として残す
- merge は unique な内容だけ canonical page へ寄せ、統合元は merged / superseded と分かる短い案内にする
- archive は obsolete / superseded / duplicate のときだけ使い、後継 page を明示する
- lifecycle action の後は `index.md`, `log.md`, 関連 link, canonical page への inbound link を更新する
