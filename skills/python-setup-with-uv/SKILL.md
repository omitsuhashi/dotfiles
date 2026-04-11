---
name: python-setup-with-uv
description: Use when starting a new Python project with uv and deciding the minimum development packages and setup steps for reproducible local development.
---

# Python Setup With uv

## 定義

この skill は、`uv` を前提に Python プロジェクトを始めるときの最小セットを固定するためのものです。

前提は次の通りです。

- `uv` は Python 本体、仮想環境、依存解決、`uv.lock` 管理まで担当する
- 追加パッケージは「継続開発に必要なもの」だけ入れる
- 便利そうでも、最初から全部は入れない

この skill のデフォルトは次です。

- 必須: `ruff`, `pytest`, `pre-commit`
- 条件付き推奨: `mypy`
- 任意: `poethepoet`

## 要点

### 最低限の判断基準

`uv` で `uv init` した直後に、まず入れるのは以下です。

- `ruff`: lint と format を 1 つに寄せる
- `pytest`: テストの土台を最初から用意する
- `pre-commit`: `ruff` をコミット時に自動実行する

次は条件付きです。

- `mypy`: 型注釈を保守対象にするなら入れる。小さな捨てスクリプトなら後回しでよい
- `poethepoet`: `uv run ruff check .` のようなコマンドが増えてから入れる。最初は不要

### セットアップ手順

1. プロジェクトを初期化する

```bash
uv init
uv python pin 3.12
```

2. 最低限の開発依存を入れる

```bash
uv add --dev ruff pytest pre-commit
```

3. 必要なら追加する

```bash
uv add --dev mypy
uv add --dev poethepoet
```

4. 環境を同期し、Git hook を入れる

```bash
uv sync
uv run pre-commit install
```

5. 最初の検証を流す

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

型チェックを使うなら:

```bash
uv run mypy .
```

## 比較

| ツール | この skill での扱い | 入れる理由 | 後回しにしてよい条件 |
|---|---|---|---|
| `uv` | 前提 | Python / venv / lock を一元化する | なし |
| `ruff` | 必須 | lint と format を一体化できる | ほぼなし |
| `pytest` | 必須 | テストの入口を最初から揃える | 使い捨てワンショットのみ |
| `pre-commit` | 必須 | コミット前に `ruff` を自動化できる | Git を使わないローカル実験のみ |
| `mypy` | 条件付き推奨 | 型注釈を壊さず育てられる | 型をまだ運用しない小規模スクリプト |
| `poethepoet` | 任意 | 長いコマンドをタスク名へ寄せられる | `uv run ...` が数個で済む段階 |

記事系の構成だと `uv + ruff + mypy + poethepoet + pre-commit` まで一括導入しがちですが、実務では最初から必須なのはそこまで多くありません。

この skill では次を採用します。

- まずは `uv + ruff + pytest + pre-commit`
- 型チェックが保守対象になった時点で `mypy`
- コマンド整理が面倒になった時点で `poethepoet`

## 具体例

### 最小 `pyproject.toml` のイメージ

`uv add --dev ...` を使えば自動で更新されますが、完成形のイメージは次です。

```toml
[project]
name = "example"
version = "0.1.0"
requires-python = ">=3.12"

[dependency-groups]
dev = [
  "ruff",
  "pytest",
  "pre-commit",
  # "mypy",
  # "poethepoet",
]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

### 最小 `.pre-commit-config.yaml`

コミットを遅くしすぎないため、最初は `ruff` だけを hook に載せます。

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: vX.Y.Z
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
```

`rev` は固定値ではなく、その時点の最新安定版へ更新してください。導入後も `pre-commit autoupdate` で追従します。

`pytest` や `mypy` は、次のどちらかで回すのが無難です。

- 手元で `uv run pytest`, `uv run mypy .`
- CI で常時実行

### `poethepoet` を入れる境界

次のようなコマンドが増えてからで十分です。

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
uv run mypy .
```

この段階で長いと感じたら、`poethepoet` を追加して `lint`, `fmt`, `test`, `typecheck` に束ねます。

## References

- `uv init`, `.python-version`, `uv.lock`: https://docs.astral.sh/uv/guides/projects/
- `uv add --dev`, dependency groups: https://docs.astral.sh/uv/concepts/projects/dependencies/
- `uv python pin`: https://docs.astral.sh/uv/concepts/python-versions/
- Ruff overview: https://docs.astral.sh/ruff/
- Ruff formatter: https://docs.astral.sh/ruff/formatter/
- pytest get started: https://docs.pytest.org/en/stable/getting-started.html
- pre-commit usage: https://pre-commit.com/
- mypy getting started: https://mypy.readthedocs.io/en/stable/getting_started.html
- Poe the Poet: https://poethepoet.natn.io/
