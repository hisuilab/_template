管理責任: primary manager worktreeから並列Issue worktreeの観測・cleanupを管理します。
ワークフロー: 横断(全フェーズから参照可能)
状態確認先: `tmp/worktrees.json`、各worktreeの`tmp/issue-{N}/phase-state.json`

権限: `/manage:status`は`tmp-write`、`/manage:cleanup`は`git-commit`
副作用: 状態観測値の同期、承認済みworktree・local branchの削除
承認: status同期は不要です。cleanupの削除対象と操作を提示し、実行直前に承認を得ます

# Worktree Management / Worktree管理

## 目次

- [1. 共通契約](#1-共通契約)
- [2. manage:status](#2-managestatus)
- [3. manage:cleanup](#3-managecleanup)

## 1. 共通契約

primary manager worktreeの`main` branchから実行します。次を読みます。

1. [`naming-policy.md 3.`](../rules/naming-policy.md#3-ファイルとディレクトリ名)
2. [`workflows.md 4.1.`](../rules/workflows.md#41-並列worktree状態)
3. [`roles.md 7.`](../rules/roles.md#7-並列worktreeでの既定配置)
4. `tmp/worktrees.json`(無い場合はversion 1の空レジストリとして扱います)

未知のregistry version、primary manager worktreeの**親ディレクトリ外**を指すpath、
Issue番号とentry keyの不一致を検出した場合は、状態を変更せず停止します。registry更新前は
`tmp/worktrees.lock`を取得し、取得後にregistryとGitの状態を読み直します。

## 2. manage:status

対象省略時は全entry、`issue-{N}`指定時は1件を同期します。

1. `git worktree list --porcelain`でpath・branchの実在を確認します
2. 実在する各worktreeの`phase-state.json`から`current`を読みます。`current`が`null`なら
   completed/skippedから次フェーズを導出し、ファイルが無ければ`phase: null`として報告します
3. `pr`が登録済みならGitHubからPR状態を取得します。未登録ならbranchに対応するPRを検索し、
   一意に特定できた場合だけ番号を記録します
4. lockを取得して状態を読み直し、観測値と`updated_at`を更新して、構文検証後にレジストリを
   原子的に置換します。成功・失敗のどちらでもlockを解放します
5. 登録のみ・実在のみ・branch不一致・phase-state欠落・GitHub参照失敗をdriftとして表示します。
   実在のみのworktreeは担当ツールを推測せず、登録候補として報告します

GitHubが一時的に参照できない場合は既存の`pr`を消去せず、staleとして表示します。

## 3. manage:cleanup

`issue-{N}`指定時は1件、`merged`指定時はマージ済み候補を検出します。人間と外部スケジューラーの
どちらから呼ばれても同じ手順を使い、検出だけでは削除しません。

1. `/manage:status`相当の同期を行います
2. 対象ごとにPRが`MERGED`であること、registryとGitのpath・branchが一致すること、
   `git -C <path> status --short`が空であることを確認します。GitHubからPRのhead SHAを取得し、
   local branch HEADと一致することも確認します。remote-tracking branchが存在する場合は、その
   HEADも同じSHAでなければ候補から除外します
3. 条件を満たすentryを`pending_cleanup_approval`へ更新します。変更・未追跡ファイル、未merge、
   detached HEAD、不一致がある対象は候補から除外して理由を報告します
4. Issue、PR、絶対path、branch、実行予定の`git worktree remove`・branch削除・registry削除を
   意思決定レポートで提示し、PMの承認を得ます
5. 承認後にlockを取得して手順2を再実行します。状態が変化していた場合は承認を使わず停止します。
   lockは手順8のregistry更新完了まで保持し、途中失敗時も必ず解放します
6. `git worktree remove -- <path>`を実行します。`--force`は使用しません
7. `git branch -d <branch>`を実行します。squash mergeにより拒否され、PRが`MERGED`、
   worktree削除済み、削除直前のlocal branch HEADがPR head SHAと一致する場合に限り、
   承認済み操作として`-D`を使えます
8. registryからentryを削除して原子的に置換し、lockを解放して完了した操作を報告します

途中失敗時は完了済み・未完了操作を分け、registryを実在状態へ同期します。再実行では既に
存在しないworktree・branchを成功済みとして扱います。変更の退避・削除、force remove、
未merge branchの削除は本コマンドの通常承認に含めず、対象を特定した別の明示承認を要求します。
