# ログ

append-only で使います。すべての entry は予測しやすい header で始めます。

## [2026-04-12] bootstrap | Initialize wiki

- `raw/`, `wiki/`, `index.md`, `log.md`, `AGENTS.md` を作成
- page category と link convention を確定

## [2026-04-12] ingest | 記事タイトル

- `wiki/sources/2026-04-12 記事タイトル.md` を追加
- `wiki/entities/サンプルエンティティ.md` を更新
- `wiki/concepts/サンプル概念.md` を更新

## [2026-04-12] query | RAG と LLM Wiki を比較する

- `wiki/queries/2026-04-12 RAG と LLM Wiki を比較する.md` を追加
- 比較メモを `index.md` に登録

## [2026-04-12] lifecycle | 重複した概念ページを統合

- `wiki/concepts/サンプル概念.md` を canonical page として維持
- 重複 page を merged 扱いにし、案内 link を追加
- `index.md` と関連 link を更新
