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
```

Python バージョンはこの skill では固定しません。プロジェクト要件があるときだけ `uv python pin <version>` を使います。

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
uv run pre-commit install --install-hooks
```

`pre-commit install` はリポジトリごとに必要です。`pyproject.toml` に `pre-commit` を入れただけでは Git commit 時には実行されません。

ただし、コミット時に「自動修正後の内容を同じ commit に含める」挙動を採用する場合は、ここで一度止まり、後述の「自動修正を同じコミットへ含めたい場合」を先に選びます。その場合は `core.hooksPath` を `.githooks` に向けるため、標準の `.git/hooks/pre-commit` へ入れる `pre-commit install` だけでは効きません。

5. 最初の検証を流す

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run pre-commit run --all-files --show-diff-on-failure
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

`requires-python` も必須ではありません。公開パッケージにする、対応バージョンを明示したい、といった要件があるときだけ追加します。

### 最小 `.pre-commit-config.yaml`

コミットを遅くしすぎないため、最初は `ruff` だけを hook に載せます。

標準の `pre-commit` 挙動でよい場合、つまり自動修正が入ったら commit を止めて人間が確認し、再度 `git add` する運用なら次を使います。

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: vX.Y.Z
    hooks:
      - id: ruff-check
        args: [--fix]
        types_or: [python, pyi]
      - id: ruff-format
        types_or: [python, pyi]
```

`rev` は固定値ではなく、その時点の最新安定版へ更新してください。導入後も `pre-commit autoupdate` で追従します。

自動修正を同じ commit へ含める運用を選ぶ場合、この mutating な設定は commit hook として使いません。`pre-commit run --all-files` や CI で状態確認しやすいよう、check-only にします。

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: vX.Y.Z
    hooks:
      - id: ruff-check
        types_or: [python, pyi]
      - id: ruff-format
        args: [--check]
        types_or: [python, pyi]
```

### コミット時の期待挙動

標準の `pre-commit` では、hook がファイルを自動修正した場合、そのコミットは失敗します。これは異常ではなく、修正後の差分を人間が確認して `git add` し直すための安全な挙動です。

期待される流れは次です。

```bash
git add .
git commit -m "change"
# ruff-check --fix または ruff-format がファイルを更新したら commit は止まる
git diff
git add .
git commit -m "change"
```

`ruff` や `ruff-format` が走ってファイルが変更されたにもかかわらず commit が成立する場合は、設定ではなく hook 実行経路を疑います。

確認点は次です。

- `.git/hooks/pre-commit` が存在するか
- `git config --get core.hooksPath` で別の hook ディレクトリへ向いていないか
- GUI / IDE の commit が Git hook を無視する設定になっていないか
- `git commit --no-verify` 相当で実行されていないか
- 独自の hook wrapper が `pre-commit` の終了コードを握りつぶしていないか

最低限の診断コマンドは次です。

```bash
test -f .git/hooks/pre-commit && sed -n '1,80p' .git/hooks/pre-commit
git config --get core.hooksPath
uv run pre-commit run --all-files --show-diff-on-failure
```

### 自動修正を同じコミットへ含めたい場合

「自動修正できるものは修正して、その修正後の内容を同じコミットに含める」挙動は、標準の `pre-commit` 設定だけでは実現しません。実現するなら project-local な Git hook を明示的に管理します。

ただしこの方式は、部分 staging との相性が悪いです。未 stage の変更まで formatter が触れて同じ commit に混ざるリスクがあるため、同じファイルに staged / unstaged の両方の変更がある場合は commit を止めます。

このモードを選ぶ場合の基本方針は次です。

- `.pre-commit-config.yaml` は check-only にする
- commit 時の自動修正と `git add` は `.githooks/pre-commit` が担当する
- `.githooks/pre-commit` は repo に commit する
- `git config core.hooksPath .githooks` は clone ごとの初期設定として実行する
- 同じファイルに staged / unstaged の両方がある場合は commit を止める

`.githooks/pre-commit` 例:

```bash
#!/usr/bin/env bash
set -euo pipefail

files=()
while IFS= read -r -d '' file; do
  files+=("$file")
done < <(git diff --cached --name-only --diff-filter=ACMR -z -- '*.py' '*.pyi')

if [ "${#files[@]}" -eq 0 ]; then
  exit 0
fi

for file in "${files[@]}"; do
  if ! git diff --quiet -- "$file"; then
    echo "error: $file has both staged and unstaged changes."
    echo "Stage or stash the unstaged changes before committing."
    exit 1
  fi
done

uv run ruff check --fix --exit-zero --force-exclude -- "${files[@]}"
uv run ruff format --force-exclude -- "${files[@]}"
git add -- "${files[@]}"

uv run ruff check --force-exclude -- "${files[@]}"
uv run ruff format --check --force-exclude -- "${files[@]}"
```

有効化:

```bash
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

チームで同じ挙動を共有したい場合は、`.githooks/pre-commit` をリポジトリ管理し、初期セットアップ手順に `git config core.hooksPath .githooks` を含めます。

この方式を採用した repo では、次の確認を必ず行います。

```bash
git config --get core.hooksPath
test -x .githooks/pre-commit
.githooks/pre-commit
uv run pre-commit run --all-files --show-diff-on-failure
```

`core.hooksPath` を設定すると、標準の `.git/hooks/pre-commit` は使われません。`.git/hooks/pre-commit` と `.githooks/pre-commit` の両方を見て判断すると誤診しやすいため、必ず `git config --get core.hooksPath` を先に見ます。

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
