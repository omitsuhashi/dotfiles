# Issue tracker: GitHub

Issue と仕様は omitsuhashi/dotfiles の GitHub Issues に保存する。
作成した Issue は GitHub Projects #8「life」に登録する。

- Repository: https://github.com/omitsuhashi/dotfiles
- Project: https://github.com/users/omitsuhashi/projects/8
- Project owner: omitsuhashi

## 操作

`gh` CLI を使用する。複数行の本文は一時ファイルに書き、
`--body-file` で渡す。

- 作成: `gh issue create --repo omitsuhashi/dotfiles --title "..." --body-file <path>`
- Project 登録: `gh project item-add 8 --owner omitsuhashi --url <issue-url>`
- 取得: `gh issue view <number> --repo omitsuhashi/dotfiles --comments`
- 一覧: `gh issue list --repo omitsuhashi/dotfiles --state open --json number,title,body,labels,comments`
- コメント: `gh issue comment <number> --repo omitsuhashi/dotfiles --body-file <path>`
- ラベル追加・削除: `gh issue edit <number> --repo omitsuhashi/dotfiles --add-label "..." --remove-label "..."`
- 終了: `gh issue close <number> --repo omitsuhashi/dotfiles`

「issue tracker に公開する」は Issue 作成と Project 登録を指す。
登録に失敗した場合は作成済み Issue の URL と失敗を報告し、
再試行では同じ Issue を使用する。

「関連 ticket を取得する」は Issue 本文・ラベル・コメントの確認を指す。

## Pull requests as a triage surface

**PRs as a request surface: no.**

## Wayfinding

- Map は `wayfinder:map` ラベルの Issue とし、Notes / Decisions-so-far / Fog を記録する。
- 子 ticket は Map の sub-issue にする。利用できない場合は Map の task list に追加し、子本文に `Part of #<map>` を記す。
- 子には `wayfinder:research` / `wayfinder:prototype` / `wayfinder:grilling` / `wayfinder:task` の該当ラベルを付ける。
- 依存関係は GitHub の native issue dependencies を使用する。利用できない場合は子本文に `Blocked by: #<number>` を記す。
- 作業対象は Map 順で、未完了・担当者なし・未解決の blocker なしの子から選ぶ。
- 着手時は自分を担当者に設定する。
- 解決時は回答をコメントし、Issue を閉じ、Map の Decisions-so-far に要点とリンクを追記する。
