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

`../../../agent-workflow/commands/build/docs.md`を読み、その指示に従ってください。
