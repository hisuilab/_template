管理責任: 失敗しているテストを通す実装(GREEN)を行い、リファクタリングします。
ワークフロー: build(impl) → run(green)
状態確認先: `tmp/{work-dir}/phase-state.json`の`implement`

権限: `source-write`
副作用: 実装・文書の作成・更新
承認: 不要です(マイルストーン/Issue・設計の範囲内で自走します)。

失敗しているテストを通す実装(GREEN)を行い、リファクタリングします。担当Role: Programmer。

## 読み込む文書

1. `phase-state.json`と対象の設計(`docs/milestones/m{N}-*.md`または設計提案)を読み、
   `test`フェーズの完了(REDあり)またはスキップ理由を確認します(どちらも無い場合は
   `/build:test`を先に提案します)
2. 対象モジュールのディレクトリのREADME.md(概要/責任/責任外)を読みます
3. 対応するREDテストを読みます

## 手順

1. テストを通す最小の実装を行います(GREEN)
2. GREEN後にリファクタリングします(責任の分離、命名、重複排除)。テストは常に成功状態を
   保ちます
3. 対象ディレクトリのREADMEは`/build:docs`で同期するため、ここでは実装のみに集中します
   (README更新まで一括で終える場合は`/build:docs`の手順に従います)
4. `just verify`を実行します。失敗した場合は対象と修正方針を報告し、必要な修正だけを行います
5. `phase-state.json`の`implement`を完了へ更新します
6. commitは行わず、検証・レビュー後に出荷フェーズでまとめます

---

次のステップ:

1. `/build:docs` — 文書同期(未実施の場合)
2. `/verify` — 検証の実行
