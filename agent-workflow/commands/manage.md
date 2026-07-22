管理責任: primary manager worktreeから並列Issue worktreeの観測・cleanupを管理します。
ワークフロー: 横断(全フェーズから参照可能)
状態確認先: `tmp/worktrees.json`、各worktreeの`tmp/issue-{N}/phase-state.json`

権限: `/manage:status`と`/manage:assign`は`tmp-write`、`/manage:cleanup`は`git-commit`
副作用: 状態観測値と担当ツールの同期、承認済みworktree・local branchの削除
承認: status・assign同期は不要です。cleanupの削除計画を提示し、apply実行直前に承認を得ます

# Worktree Management / Worktree管理

## 目次

- [1. 共通契約](#1-共通契約)
- [2. manage:status](#2-managestatus)
- [3. manage:assign](#3-manageassign)
- [4. manage:cleanup](#4-managecleanup)

## 1. 共通契約

primary manager worktreeの`main` branchから実行します。次を読みます。

1. [`naming-policy.md 3.`](../rules/naming-policy.md#3-ファイルとディレクトリ名)
2. [`workflows.md 4.1.`](../rules/workflows.md#41-並列worktree状態)
3. [`roles.md 7.`](../rules/roles.md#7-並列worktreeでの既定配置)
4. `tmp/worktrees.json`(無い場合はversion 1の空レジストリとして扱います)

worktree作成・削除、local branch削除、担当変更、stale lock回収は`scripts/worktree-safety`を
必須経路とします。コマンド本文の手順をシェル操作へ読み替えて独自実装してはいけません。
未知のregistry version、primary manager worktreeの親ディレクトリ外を指すpath、Issue番号と
entry keyの不一致を検出した場合は、状態を変更せず停止します。

## 2. manage:status

対象省略時は全entry、`issue-{N}`指定時は1件を同期します。

1. `git worktree list --porcelain`でpath・branchの実在を確認します
2. 実在する各worktreeの`phase-state.json`から`current`を読みます。`current`が`null`なら
   completed/skippedから次フェーズを導出し、ファイルが無ければ`phase: null`として報告します
3. `pr`が登録済みならGitHubからPR状態を取得します。未登録ならbranchに対応するPRを検索し、
   一意に特定できた場合だけ番号を記録します
4. lockを取得して状態を読み直し、観測値と`updated_at`を更新して、構文検証後にレジストリを
   原子的に置換します。成功・失敗のどちらでもlockを解放します。担当ツールは変更せず、
   `/manage:assign`を使います
5. 登録のみ・実在のみ・branch不一致・phase-state欠落・GitHub参照失敗をdriftとして表示します。
   実在のみのworktreeは担当ツールを推測せず、登録候補として報告します

GitHubが一時的に参照できない場合は既存の`pr`を消去せず、staleとして表示します。

## 3. manage:assign

`issue-{N}`と`claude`・`codex`・`human`・`null`のいずれかを指定します。

1. `scripts/worktree-safety assign --manager-root <root> --issue <N> --tool <tool>`を実行します
2. helperがlock取得後にregistryを再検証し、`assigned_tool`と`updated_at`を原子的に更新します
3. helperが返したJSONを報告します。独自にregistryを書き換えてはいけません

## 4. manage:cleanup

`issue-{N}`指定時は1件、`merged`指定時はマージ済み候補を検出します。人間と外部スケジューラーの
どちらから呼ばれても同じ手順を使い、検出だけでは削除しません。

1. `/manage:status`相当で対象候補を観測し、GitHubからPR stateとhead SHAを取得します
2. 対象ごとに`scripts/worktree-safety plan-cleanup --manager-root <root> --issue <N>
   --pr-state <state> --pr-head <sha>`を実行します
3. helperが非0終了した対象は候補から除外し、dirty・detached HEAD・path/branch/SHA不一致等の
   理由をそのまま報告します
4. helperのJSONにあるIssue、絶対path、branch、head SHA、worktree/branchの有無、`force_branch`
   を意思決定レポートで提示し、PMの承認を得ます
5. 承認後、同じ入力と`--approved-head <sha>`を付けて`apply-cleanup`を実行します。helper自身が
   lockを取得し、状態を再検証してからworktree・local branch・registry entryを削除します
6. helperが状態変化を検出した場合は承認を再利用せず停止します。返却JSONと完了済み操作を
   報告し、必要なら同じplanからやり直します

再実行ではhelperが既に存在しないworktree・branchを成功済みとして扱います。変更の退避・削除、
force remove、未merge branchの削除は本コマンドの通常承認に含めず、対象を特定した別の
明示承認を要求します。stale lockは`lock-status`のowner tokenと判定を提示してPM承認を得た後だけ、
`reclaim-lock --owner-token <token>`で回収します。
