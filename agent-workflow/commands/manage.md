管理責任: primary manager worktreeから並列Issue worktreeの観測・cleanupを管理します。
ワークフロー: 横断(全フェーズから参照可能)
状態確認先: `tmp/worktrees.json`、各worktreeの`tmp/issue-{N}/phase-state.json`

権限: `/manage:triage`は`read-only`、`/manage:status`と`/manage:assign`は`tmp-write`、
`/manage:cleanup`は`git-commit`
副作用: triageは画面出力のみ、status・assignは状態観測値と担当ツールの同期、cleanupは
承認済みworktree・local branchの削除
承認: triage・status・assign同期は不要です。cleanupの削除計画を提示し、apply実行直前に承認を
得ます

# Worktree Management / Worktree管理

## 目次

- [1. 共通契約](#1-共通契約)
- [2. manage:status](#2-managestatus)
- [3. manage:assign](#3-manageassign)
- [4. manage:triage](#4-managetriage)
- [5. manage:cleanup](#5-managecleanup)

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

## 4. manage:triage

Open Issueを読み取り、着手候補のグルーピングと優先順位を提案します。Issue更新、worktree作成、
worker起動は行わず、PM承認後の次ステップとして`/plan:issue N`を提示します。

### 4.1. 読み取り対象

1. `gh issue list --state open --limit 200 --json number,title,labels,milestone,assignees,body,url`で
   Open Issueを読みます。GitHub参照に失敗した場合は、ローカル情報だけで順位を確定せず
   停止します。Open Issue数が取得上限に達した場合は、候補漏れの可能性を「要確認」として
   報告し、順位を確定しません
2. 各Issueの本文から、`depends on`、`blocked by`、`requires`、`関連Issue`、`Follow-up of`、
   `#N`参照などの明示的な依存・関連記述を抽出します
3. `gh pr list --state open --json number,title,headRefName,labels,url,body,closingIssuesReferences`で
   関連PRを読み、Issue番号をbranch名、PR本文、タイトル、closing issue参照から推定します。
   推定は事実ではなく「推測」として扱います
4. `tmp/worktrees.json`、`git worktree list --porcelain`、各worktreeの
   `tmp/issue-{N}/phase-state.json`を読み、稼働中Issueと空き枠を確認します。空き枠は
   `3 - 稼働中Issue worktree数`です

### 4.2. 分類

Issueは次のグループへ分類します。1つのIssueが複数に該当する場合は、上から優先して表示します。

| グループ | 条件 |
| --- | --- |
| 進行中 | registry、実在worktree、open PRのいずれかから着手済みと確認できます |
| 統合・重複候補 | 同じ目的のIssue、重複label、または本文の重複記述が確認または推測されます |
| 依存待ち | 明示依存先がopen、または循環依存があり単独着手の判断ができません |
| 要確認 | 本文や完了条件が不足、GitHub参照失敗、labelだけでは意図を確定できません |
| 前提・基盤 | 他Issueを解放する明示依存先、または複数Issueから参照される基盤作業です |
| 着手可能 | 依存待ち・進行中・要確認に該当せず、空き枠があれば開始候補になります |

分類の根拠は「事実」と「推測」に分けます。label、milestone、本文の明示依存、Issue状態、
worktree実在、PR状態は事実です。変更競合、作業規模、agent実行適性、暗黙の関連性は推測です。

### 4.3. 優先順位

着手可能Issueと前提・基盤Issueを、次の評価軸で比較します。

| 評価軸 | 高く評価する条件 |
| --- | --- |
| 重大度 | bug、security、workflow破綻、作業停止に近いlabelや本文があります |
| 依存解除効果 | 複数Issueから明示参照され、完了すると他Issueが着手可能になります |
| 準備度 | 完了条件、対象ファイル、期待挙動が本文に明記されています |
| 作業規模 | 小さく独立しており、1Issueとして完了条件が閉じています |
| 変更競合 | 稼働中worktreeやopen PRと触る領域が重なりにくいです |
| agent実行適性 | read/test/implement/docs/verifyの流れで自律実行しやすく、外部判断が少ないです |

同点時は、重大度、依存解除効果、準備度、Issue番号の昇順で決定します。同じ入力から同じ提案に
なるよう、表示順を決定論的に保ちます。

### 4.4. 出力形式

次の形式で報告します。空き枠を超えるIssueは「次点」に残し、自動開始しません。

```text
## Triage Report

空き枠: 2 / 3

### 推奨
1. #147 — 前提・基盤
   - 事実: #142 follow-up、完了条件あり
   - 推測: 進行中worktreeと変更領域が分離されています
   - 次: /plan:issue 147

### 保留
- #148 — #147の完了待ちです

### 要確認
- #149 — 完了条件が不足しています
```

## 5. manage:cleanup

`issue-{N}`指定時は1件、`merged`指定時はマージ済み候補を検出します。人間と外部スケジューラーの
どちらから呼ばれても同じ手順を使い、検出だけでは削除しません。

1. `/manage:status`相当で対象候補を観測し、対象PR番号を特定します。stateやSHAを引数で指定しては
   いけません
2. 対象ごとに`scripts/worktree-safety plan-cleanup --manager-root <root> --issue <N>
   --pr <pr-number>`を実行します。helperがGitHubからrepository、state、head SHA、head branchを
   取得します
3. helperが非0終了した対象は候補から除外し、dirty・detached HEAD・path/branch/SHA不一致等の
   理由をそのまま報告します
4. helperのJSONにあるIssue、repository、PR番号・state、PR head branch、絶対path、local branch、
   head SHA、worktree/branchの有無、`force_branch`、`plan_token`を意思決定レポートで提示し、
   PMの承認を得ます
5. 承認後、同じ入力と`--approved-head <sha> --approved-plan <plan_token>`を付けて
   `apply-cleanup`を実行します。helper自身がlockを取得し、GitHub状態を再取得して承認対象全体と
   状態を再検証してから
   worktreeを削除し、期待SHAとのcompare-and-deleteでlocal branchを削除してregistryを更新します
6. helperが状態変化を検出した場合は承認を再利用せず停止します。返却JSONと完了済み操作を
   報告し、必要なら同じplanからやり直します

再実行ではhelperが既に存在しないworktree・branchを成功済みとして扱います。変更の退避・削除、
force remove、未merge branchの削除は本コマンドの通常承認に含めず、対象を特定した別の
明示承認を要求します。stale lockは`lock-status`のowner tokenと判定を提示してPM承認を得た後だけ、
`reclaim-lock --owner-token <token>`で回収します。
