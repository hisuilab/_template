管理責任: 実装済みディレクトリのREADME.md(概要/責任/責任外)、`docs/milestones/`配下の
完了条件・状態、`docs/draft/`のfrontmatter、大きな判断があった場合の`docs/decisions/`
新規作成を、直前の実装差分に同期させます。未commitの差分(テスト・実装本体・この同期分)を
種別ごとに複数commitへ分割し、まとめて1回の承認で連続実行します。
ワークフロー: build(docs)
状態確認先: `docs/milestones/README.md`(一覧・状態)、対象`docs/milestones/m{N}-*.md`
(完了条件チェックリスト)

権限: `git-commit`
副作用: README.md・`docs/draft/`・`docs/milestones/`・`docs/decisions/`配下の文書更新、
未commit差分の複数commitへの分割実行(test→feat→docs)
承認: commit実行直前に、分割したcommit一覧(ファイル・message案)をまとめて1回提示します。
文書更新自体は不要です(直前の実装差分の範囲内で自走します)。

直前の実装差分に対応する文書を同期します。担当Role: Programmer。

## 読み込む文書

1. `git diff`(または`git status`)で直前の変更ファイル一覧を取得します
2. 変更されたディレクトリそれぞれのREADME.mdを読み、概要/責任/責任外が実装内容と一致
   しているか確認します(ディレクトリの担当範囲はREADME.md自身を正本とし、本コマンドは
   説明を複製しません)
3. 該当するマイルストーン文書(`docs/milestones/m{N}-*.md`)があれば完了条件と実装計画を
   照合します
4. `docs/draft/`配下で関連する下書きがあればfrontmatterの`status`を確認します
5. 詳細な同期対象・観点は
   [`agent-workflow/skills/docs-sync/SKILL.md`](../../skills/docs-sync/SKILL.md)を参照します
   (`docs/decisions/`・`docs/development/`を含む同期対象文書リストを持ちます)
6. 新規に文書を作成する場合は
   [`tmp/docs/_template/README.md`](../../../tmp/docs/_template/README.md)から対象種別の
   テンプレートを選び、下敷きにします

## 手順

1. 変更ディレクトリのREADME.mdが概要/責任/責任外を維持しているか確認し、実態とずれて
   いれば更新します。新規ディレクトリは`scripts/check-readme`が要求する構成
   (`# <title>` / `## 1. 概要` / `## 2. 責任` / `## 3. 責任外`、目次なし)で新規作成します
2. 対応するマイルストーン文書の完了条件チェックボックスを実態に合わせて更新します。
   自分で書いた完了条件を実際には満たしていない場合は、正直にチェックを外したまま報告します
3. `docs/draft/`配下の論点が実装で解消されていれば、frontmatterを`status: migrated`・
   `migrated_at`・`migrated_to`に更新します
   ([`naming-policy.md 4.`](../../rules/naming-policy.md#4-文書の状態管理))
4. 大きな判断(設計判断、既存判断との矛盾の解消等)があった場合は、`docs/decisions/`へ
   新規Decision Recordを作成します(テンプレート:
   [`tmp/docs/_template/decision/decision.md`](../../../tmp/docs/_template/decision/decision.md))。
   **実装中に**初めて発覚した判断が対象です(実装前に判明していた設計判断は
   `/plan:architecture`が担当します)
5. `just verify`(check-readme・check-status・rumdl含む)を実行して整合を確認します
6. `tmp/{work-dir}/phase-state.json`の`docs`を完了へ更新します
7. 未commitの差分全体(`git status`)を種別ごとにグルーピングします
   - `tests/**` → test commit
   - `src/`・`config/`・`modules/`等の実装本体 → feat/fix commit(scopeが複数に分かれる
     場合は分割を提案します)
   - 本コマンドがここまでで行った文書同期分(README・完了条件チェックボックス・
     frontmatterの`status`・decisions等) → docs(完了)commit
   design分(`docs/milestones/m{N}-*.md`の新規作成等)がまだcommitされていない場合は、

   `/plan:design`が未実施であるとして報告し、先に済ませることを提案します

8. 各commitのファイル一覧とcommit message案(`AGENTS.md`のConventional Commits形式+
   `Role:`トレーラー)をまとめて1回で提示します。承認後、test→feat→docsの順で連続して
   commitを実行します(各commit時にpre-commit hookが`just verify`相当を自動実行します)。
   承認が得られない場合はcommitせず理由を報告します

---

次のステップ:

1. 同じマイルストーン/Issueに次の作業がある場合: `/build:test`(または内容に応じて
   `/build:implement`)
2. 全作業完了の場合: `/verify` — マイルストーン/Issue全体の最終検証
