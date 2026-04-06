# Codex Worktree Kit

## 目的

`codex-worktree-kit` は、consumer repo ごとに薄い bridge script だけを置けば再利用できる、設定ファイル駆動の Codex 向け worktree bootstrap utility です。

この utility は次を担当します。

- main repo の worktree 作成（任意）
- 関連 repo の linked worktree 作成
- consumer repo 配下への symlink / alias 作成
- consumer repo 固有の post-setup command 実行
- 上記の config-driven な共通化

主実装は Python 3.12+ で、依存は標準ライブラリ中心です。

## 要点

- consumer repo 固有の command は `[[steps]]` に外出しする
- repo 固有の環境変数名は `repos.<name>.repo_env` で追加できる
- `.docs` のような alias は `[[links]]` で宣言する
- linked worktree の branch 方針は `branch_strategy` で切り替える
- `[worktree]` を省略すると primary worktree は外部管理として扱う
- `--dry-run` で副作用なしの plan 確認ができる

## 比較

| 方式 | 利点 | 欠点 | 採用 |
| --- | --- | --- | --- |
| shell script 主体 | 手早い | 分岐追加・テスト・保守が崩れやすい | 不採用 |
| repo 固有ロジックを本体に埋め込む | 初速は出る | backend/web/docs で再利用できない | 不採用 |
| config-driven Python utility | 拡張しやすく、テストしやすい | 初期設計が必要 | 採用 |

## Consumer Repo への組み込み方

1. この repo を共通 utility として clone する
2. utility repo root で `uv sync` を実行して `.venv` を作る
3. consumer repo に `.codex/worktree.toml` を置く
4. consumer repo には薄い bridge script だけを置く
5. Codex App で `Worktree` を選んで main worktree を作る
6. 生成された worktree 内で `bootstrap` を実行する

初回セットアップ:

```bash
cd /path/to/codex-worktree-kit
uv sync
```

`bin/*` wrapper はこの repo の `.venv/bin/python` を使う前提です。consumer repo 側の bridge script では `python3 -m ...` ではなく `KIT_DIR/bin/...` を呼んでください。

bridge script の例:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
KIT_DIR="${CODEX_WORKTREE_KIT:-$HOME/src/codex-worktree-kit}"

"$KIT_DIR/bin/codex-worktree-bootstrap" \
  --root-dir "$ROOT_DIR" \
  --config "$ROOT_DIR/.codex/worktree.toml"
```

primary worktree もこの utility で作りたい repo 向けに、`create-worktree.sh` 相当の bridge も置けます。

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
KIT_DIR="${CODEX_WORKTREE_KIT:-$HOME/src/codex-worktree-kit}"

"$KIT_DIR/bin/codex-worktree-create-worktree" "$1" \
  --root-dir "$ROOT_DIR" \
  --config "$ROOT_DIR/.codex/worktree.toml"
```

## Config Schema

`consumer/.codex/worktree.toml` の基本形:

```toml
version = 1

[git]
hooks_path = ".githooks"

[repos.docs]
repo_env = ["CODEX_DOCS_REPO", "SMARTRA_DOCS_REPO"]
discover = [".docs", "../docs", "docs"]
linked_worktree_path = "../docs"
branch_strategy = "mirror-current-or-parent"
required = true

[[links]]
path = ".docs"
repo = "docs"

[[steps]]
name = "sync-openapi"
cwd = "."
run = ["make", "sync-openapi"]

[[steps]]
name = "docs-catalog"
cwd = ".docs"
run = ["make", "docs-catalog"]
```

主要項目:

- `version`: 現在は `1` のみ対応
- `[git].hooks_path`: `git config core.hooksPath` に設定する相対 path
- `[worktree]`: primary worktree をこの utility で作るときだけ使う任意 section
- `[worktree].default_root_env`: `create-worktree` の root 決定に使う環境変数の優先順
- `[worktree].default_root`: consumer root 基準の既定 worktree root
- `[repos.<name>]`: 関連 repo 解決と linked worktree 作成設定
- `repo_env`: repo path を解決する環境変数の優先順
- `discover`: consumer root から探索する候補 path
- `linked_worktree_path`: consumer worktree 基準で作る linked worktree path
- `branch_strategy`: `mirror-current-or-parent` または `detach`
- `required`: 解決失敗を error にするか
- `[[links]]`: consumer repo に作る symlink
- `[[steps]]`: bootstrap の最後に順次実行する command

repo resolution 優先順位:

1. `repo_env`
2. `discover`
3. main worktree 親 directory 配下の sibling 推定
4. `required = true` なら error

repo 判定条件は `<path>/.git` の存在です。

## App-first と Full-create の使い分け

この utility には 2 つの使い方があります。

1. App-first
   Codex App が primary worktree を作り、この utility は `bootstrap` で linked worktree と symlink と steps だけを担当します。標準はこちらです。
2. Full-create
   この utility が `create-worktree` で primary も作ります。この場合だけ `[worktree]` section が必要です。

`[worktree]` が config に存在しない場合、`create-worktree` は明示的に error になります。primary worktree は Codex App など外部管理の black box として扱う、という意味です。

## CLI Usage

```bash
./bin/codex-worktree-bootstrap --root-dir <path> --config <path> [--dry-run]
./bin/codex-worktree-create-worktree <name> [--root-dir <path>] [--worktree-root <path>] [--config <path>] [--dry-run]
./bin/codex-worktree-resolve-repo --root-dir <path> --config <path> --repo-key docs
./bin/codex-worktree-validate-config --config <path>
```

仮想環境を明示せず Python module として叩きたい場合は、utility repo 内で:

```bash
uv run python -m codex_worktree bootstrap --root-dir <path> --config <path>
uv run python -m codex_worktree create-worktree <name> --root-dir <path> --config <path>
uv run python -m codex_worktree resolve-repo --root-dir <path> --config <path> --repo-key docs
uv run python -m codex_worktree validate-config --config <path>
```

`create-worktree` の worktree root 解決順:

1. `--worktree-root`
2. `worktree.default_root_env`
3. `worktree.default_root`
4. `<project-parent>/.worktrees/<repo-name>`

## Codex App の既定値との対応

Codex App が管理する worktree は `$CODEX_HOME/worktrees` 配下に作られます。`$CODEX_HOME` の既定値は `~/.codex` なので、App の既定 location は `~/.codex/worktrees` です。

一方、この utility の `create-worktree` は project config から App の内部状態を参照できないため、`[worktree]` を有効にした上で `default_root` を省略した場合は utility 独自の安全側 fallback として `<project-parent>/.worktrees/<repo-name>` を使います。

Codex App と同じ系統の場所に寄せたい場合は、`default_root` を明示してください。Full-create 用 examples では `~/.codex/worktrees/<repo-name>` を採用しています。

`CODEX_HOME` を独自値に変えている場合は、この utility 側でも `CODEX_WORKTREE_ROOT="$CODEX_HOME/worktrees/<repo-name>"` のように明示的に渡してください。Codex App 側の worktree 作成先は現状ユーザー設定では変更できません。

## App-first 設定例

`examples/backend.worktree.toml`:

```toml
version = 1

[git]
hooks_path = ".githooks"

[repos.docs]
repo_env = ["CODEX_DOCS_REPO", "SMARTRA_DOCS_REPO"]
discover = [".docs", "../docs", "docs"]
linked_worktree_path = "../docs"
branch_strategy = "mirror-current-or-parent"
required = true

[[links]]
path = ".docs"
repo = "docs"

[[steps]]
name = "sync-openapi"
cwd = "."
run = ["make", "sync-openapi"]

[[steps]]
name = "docs-catalog"
cwd = ".docs"
run = ["make", "docs-catalog"]
```

この形では Codex App が primary worktree を作り、`bootstrap` だけを使います。

## Full-create 設定例

`examples/backend.create-worktree.toml`:

```toml
version = 1

[git]
hooks_path = ".githooks"

[worktree]
default_root = "~/.codex/worktrees/backend"
default_root_env = ["CODEX_WORKTREE_ROOT"]

[repos.docs]
repo_env = ["CODEX_DOCS_REPO", "SMARTRA_DOCS_REPO"]
discover = [".docs", "../docs", "docs"]
linked_worktree_path = "../docs"
branch_strategy = "mirror-current-or-parent"
required = true

[[links]]
path = ".docs"
repo = "docs"

[[steps]]
name = "sync-openapi"
cwd = "."
run = ["make", "sync-openapi"]

[[steps]]
name = "docs-catalog"
cwd = ".docs"
run = ["make", "docs-catalog"]
```

`examples/web.create-worktree.toml`:

```toml
version = 1

[worktree]
default_root = "~/.codex/worktrees/web"
default_root_env = ["CODEX_WORKTREE_ROOT", "WEB_WORKTREE_ROOT"]

[repos.docs]
repo_env = ["CODEX_DOCS_REPO"]
discover = [".docs", "../docs"]
linked_worktree_path = "../docs"
branch_strategy = "mirror-current-or-parent"
required = true

[[links]]
path = ".docs"
repo = "docs"

[[steps]]
name = "docs-catalog"
cwd = ".docs"
run = ["make", "docs-catalog"]

[[steps]]
name = "web-types"
cwd = "."
run = ["pnpm", "generate:types"]
```

この形では `create-worktree` が有効になります。

## `.docs` Linked Worktree の考え方

consumer repo から docs repo を直接参照すると、branch がずれていると差分確認がしづらくなります。`linked_worktree_path = "../docs"` を使うと、consumer worktree に対応した docs worktree を隣に作れます。

その上で `[[links]]` に:

```toml
[[links]]
path = ".docs"
repo = "docs"
```

を置けば、consumer repo からは常に `.docs` 経由で docs worktree を参照できます。

## Dry-run の使い方

副作用を起こさず plan だけ確認したい場合:

```bash
./bin/codex-worktree-create-worktree feature/my-branch \
  --root-dir "$ROOT_DIR" \
  --config "$ROOT_DIR/.codex/worktree.toml" \
  --dry-run
```

この command は `[worktree]` section がある config でのみ使えます。

```bash
./bin/codex-worktree-bootstrap \
  --root-dir "$ROOT_DIR" \
  --config "$ROOT_DIR/.codex/worktree.toml" \
  --dry-run
```

出力には実行予定の `git config`, `git worktree add`, symlink 作成, step command が並びます。

## トラブルシュート

- `unsupported config version`: `version = 1` になっているか確認する
- `failed to resolve repo 'docs'`: `repo_env`, `discover`, sibling path のどこで見つけたいか config を見直す
- `worktree path already exists`: 既存 path を消すか、別 branch 名を使う
- `cannot create symlink`: 競合 path が通常 file / directory なので、手で退避してから再実行する
- step failure: stderr はそのまま流れるので、失敗した step 名と exit code を見て consumer repo 側 command を修正する

## 具体例

新しい backend worktree を作って docs linked worktree まで張る流れ:

```bash
ROOT_DIR="$(git rev-parse --show-toplevel)"
KIT_DIR="${CODEX_WORKTREE_KIT:-$HOME/src/codex-worktree-kit}"

"$KIT_DIR/bin/codex-worktree-create-worktree" feature/openapi-sync \
  --root-dir "$ROOT_DIR" \
  --config "$ROOT_DIR/.codex/worktree.toml"

NEW_ROOT="../.worktrees/backend/feature/openapi-sync"

"$KIT_DIR/bin/codex-worktree-bootstrap" \
  --root-dir "$NEW_ROOT" \
  --config "$NEW_ROOT/.codex/worktree.toml"
```
