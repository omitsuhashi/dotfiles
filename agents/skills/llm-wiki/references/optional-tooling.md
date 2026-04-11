# Optional Tooling

追加の ergonomics, search, visualization, output format を user が求めたときだけ読みます。どれも base の LLM Wiki パターンには必須ではありません。

## Obsidian Web Clipper

web article から local Markdown source へ素早く落としたいときに使います。

- article ingest workflow と相性がよい
- clipped article を `raw/sources/` へ保存する運用に向く
- Official page: <https://obsidian.md/clipper>

## Local Image Handling

clipped source や downloaded source が screenshot, figure, diagram, photo に依存するときに使います。

- referenced image は `raw/assets/` へ保存する運用を優先する
- 先に Markdown source を読み、その後で必要な画像だけを見る
- 後続 session が再利用できるよう image path を安定させる

## Dataview

page frontmatter から動的な table や list を出したいときに使います。

- recent ingest, uncited page, tag 別 page などの dashboard に向く
- metadata を一貫して保守する wiki でだけ価値が出る
- Docs: <https://blacksmithgu.github.io/obsidian-dataview/>

## Marp

query の答えを plain note ではなく slide deck にしたいときに使います。

- briefing, comparison, research readout と相性がよい
- raw document から再構築せず、wiki を source of truth にする
- Docs: <https://marp.app/>

## `qmd`

wiki が `index.md` だけでは追いにくい規模まで育ったときに使います。

- 手動 grep より強い local Markdown search を提供する
- 数百規模の page や source を持つ vault で効きやすい
- Repository: <https://github.com/tobi/qmd>

## When To Stay Simple

存在するからという理由だけで optional tooling を足さないでください。

- 小さな wiki は `index.md`, `log.md`, shell search だけで回せる
- frontmatter が不安定なら Dataview は保守コストだけ増える
- まだ `index.md` で十分見渡せるなら search tooling は早い
- durable artifact が Markdown note だけで足りるなら slide 生成は不要
