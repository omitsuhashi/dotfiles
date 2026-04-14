# Operations

mode ごとの標準手順をまとめたファイルです。現在の作業に対応する section だけを読みます。

## Default Stance

- routine な low-risk 更新は自律で進める
- 曖昧さが高く、影響が広く、後戻りコストが大きい変更だけ user と揃える
- durable な wiki documentation は本文を日本語で保つ

## `bootstrap`

新規 local Markdown wiki を作るとき、または既存の Markdown repo / vault を LLM Wiki パターンへ寄せるときに使います。

### Goal

raw source を不変に保ちつつ、knowledge root, wiki の page 種別, `AGENTS.md` の local contract が明確で、汎用運用は `llm-wiki` skill に集約された構成を作ります。

### Check First

- 既存の local Markdown wiki または Markdown repo はあるか
- dedicated wiki repo か、mixed repo 内の subdirectory wiki か
- knowledge root はどこに置くべきか
- knowledge root の `raw/`, `wiki/`, `index.md`, `log.md`, `AGENTS.md` は既にあるか
- 既存の naming convention を維持すべきか
- 小規模な personal wiki か、継続的な research / team wiki か

### Default Procedure

1. dedicated wiki repo か mixed repo かを決め、knowledge root を確定する。
2. mixed repo なら `assets/templates/root-AGENTS.md` を元に repo root に thin router `AGENTS.md` を置き、knowledge root の `AGENTS.md` への導線だけを書く。
3. 無ければ knowledge root に `assets/templates/AGENTS.md`, `index.md`, `log.md` をコピーする。knowledge root の `AGENTS.md` には skill への導線と local override だけを書く。
4. `references/schema-and-conventions.md` の推奨サブディレクトリを knowledge root 配下に作る。
5. YAML frontmatter を使うか決める。
6. 初期構成を knowledge root の `index.md` に記録する。
7. knowledge root の `log.md` に `bootstrap` エントリを追加する。

### Pause And Align When

- directory layout や naming に複数の妥当案があり、後で rename / relink が多発しそう
- repo root を knowledge root のまま使うべきか、subdirectory に切り出すべきかで運用コストが変わる
- 既存 wiki と新規ルールのどちらを canonical にするかで運用コストが変わる
- 1 回の bootstrap で広範囲の page 再配置を伴う

### Output Expectations

- knowledge root に local contract と entrypoint がある
- repo root から wiki に辿りやすい entrypoint がある
- 後続 session が ingest / query / lint のやり方を再発明せずに済む

## `ingest`

`raw/` に新しい source が入り、wiki へ統合するときに使います。

### Goal

新しい source の知識を一度だけコンパイルし、その結果を persistent wiki 全体へ配ることで、後続 query が毎回 synthesis をやり直さなくて済むようにします。

### Check First

- 新しく入った source file はどれか
- 影響を受ける既存 page はどれか
- この source や topic の summary page は既にあるか
- raw source へ直接 citation すべき claim はどれか

### Default Procedure

1. `raw/` から source を読む。
2. `index.md` を見て関連 page を当てる。
3. 編集前に直接関係する entity / concept / synthesis page を開く。
4. source summary page を作るか更新する。
5. 新しい事実、対立点、cross-link を関係 page に反映する。
6. 新規 page や大きく変わった page を `index.md` に反映する。
7. 何を変えたかを `log.md` の `ingest` エントリに記録する。

### Editing Rules

- raw file は不変に保つ。
- 自然に分解できるなら、大きな 1 枚より小さな複数 page を優先する。
- 古い claim を黙って置き換えず、矛盾を明示する。
- source summary から entity / concept へ事実を運ぶときも citation を保つ。

### Pause And Align When

- 1 つの source が複数 page の境界を作り直しそう
- 既存 page の canonical 名称や topic boundary を変える必要がある
- source の解釈が割れ、どの framing を採るかで downstream page が大きく変わる

それ以外の routine な summary 追加、citation 補強、軽い cross-link 追加は自律で進めます。

## `query`

maintained wiki に対して質問へ答えるときに使います。

### Goal

compiled wiki を再利用して根拠付きで素早く答え、その出力自体を wiki に残すべきか判断します。

### Check First

- `index.md` のどこが関連 page を指しているか
- 既に必要 topic をまとめている wiki page はあるか
- 裏取りや dispute resolution に raw source が要るか
- 回答は一時的なものか、durable page にすべきか

### Default Procedure

1. `index.md` から始める。
2. 必要最小限の wiki page を読む。
3. wiki が薄い、争点がある、古い場合だけ raw citation を追加で引く。
4. 必要に応じて wiki page と raw source を引用して答える。
5. 再利用価値があれば `wiki/queries/` か `wiki/syntheses/` に page を作るか更新する。
6. 新しい durable page を `index.md` に登録し、`log.md` に `query` エントリを追加する。

### Pause And Align When

- query の結果をどの page に落とすべきか曖昧で、既存 page を大きく再編しそう
- 回答が複数の durable artifact 候補にまたがり、emphasis の置き方で成果物が変わる
- query への回答が broad rewrite や rename / merge 判断を伴う

### File-Back Rule

次のいずれかに当てはまるなら、回答を wiki へ戻します。

- 比較や synthesis を後で再利用しそう
- taxonomy, table, framing など durable な整理を作れた
- query が露出させた gap を新しい page が埋めた
- user が durable note, memo, briefing, deck, report を明示的に求めた

## `lint`

単一 source の処理ではなく、wiki 全体の health check をするときに使います。

### Goal

wiki が断片的な summary の寄せ集めへ劣化する前に、構造的な弱点を見つけます。

### Check First

- `index.md` が重要 page を網羅しているか
- `log.md` に recent ingest はあるのに wiki 更新が追随していない箇所はないか
- inbound link のない page はどれか
- 新しい source で superseded されていそうな claim はどれか
- 繰り返し言及されるのに独立 page を持たない concept はどれか

### Default Procedure

1. `index.md` と `log.md` を走査する。
2. orphan page, stale page, contradiction candidate, recurring unnamed concept を洗う。
3. 編集前に対象 page を確認して問題を確定する。
4. link 修正、missing page 追加、stale claim の superseded 明記を行う。
5. 具体的な gap がある箇所だけ targeted な source 追加や web check を提案する。
6. 所見と修正を `log.md` の `lint` エントリへ記録する。

### Common Lint Findings

- inbound link を持たない page
- 同じ concept の重複 page
- entity / concept へ波及していない source summary
- citation trail のない assertion
- newer source を反映していない synthesis page

## Page Lifecycle And Canonicalization

重複や強い重なりを見つけたら、page を増やし続けず lightweight に整理します。

### Canonical Page を選ぶ基準

- 最も標準的な名前で表現できる
- 1 page 1 durable topic の境界が明確
- 既存 link の受け皿として中心に置きやすい
- 今後も継続参照されそうな scope を持つ

### Rename

canonical 名称へ寄せます。旧 page を消すだけで discoverability を失うなら、短い案内 stub を残して新 page へ誘導します。

### Merge

destination を 1 つ決め、unique な内容だけを canonical page へ移します。統合元は削除せず、merged / superseded の案内を短く残すか archive します。

### Archive

obsolete, superseded, duplicate のときだけ使います。archive 先または後継 page を明示し、現役 page と誤認される書き方を避けます。

### After Any Lifecycle Action

- `index.md` を canonical 状態に更新する
- `log.md` に rename / merge / archive の事実を残す
- 触った page の outbound link を見直す
- canonical page へ最低 1 本の inbound link が残ることを確認する
