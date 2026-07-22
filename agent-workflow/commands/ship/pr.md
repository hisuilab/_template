管理責任: Rigor Modeに応じて出荷を実行します。Prototype Modeは(`/build:docs`が既に
commit済みのmilestoneブランチを)`prototype`へfast-forward merge、Production
Modeはcommit・push・PR作成です。
ワークフロー: ship(実行)
状態確認先: `tmp/{work-dir}/phase-state.json`の`ship`

権限: `git-commit`(Prototype Mode) / `external-write`(Production Mode)
副作用: `prototype`へのfast-forward merge(Prototype Mode)、commit・push・PR作成
(Production Mode)
承認: mergeまたはcommitの実行直前に対象commit一覧を提示します。push・PR作成
(Production Mode)は実行直前に明示承認を得ます。

トレーサビリティを確認し、出荷します。担当Role: Programmer→Reviewer。

## 読み込む文書

1. `tmp/{work-dir}/ship-readiness.md`(`ready`判定であること)を確認します
2. [`workflows.md 1.`](../../rules/workflows.md#1-作業単位とmode検出)でRigor Modeを確認します
3. Production Modeの場合は対象Issue本文を確認します

## 手順

1. 出荷前チェックを実行します
   - `/verify`相当の検証が成功している
   - `phase-state.json`で`review`まで完了している(未実施ならレビューを提案)
   - テスト先行のスキップがある場合、理由が記録されている
   - 差分が1論点に収まっている(上限8ファイル / 500行を超える場合は分割案を提示します)
2. **Prototype Mode**: milestone単位のcommitは`/build:docs`が既に完了させている前提です
   (未commitの変更が残っている場合は`/build:docs`を先に提案します)。`git log
   prototype..HEAD`でcommit一覧を提示し、`prototype`ブランチへのfast-forward mergeを
   提案します(実行は明示承認後)
3. **Production Mode**:
   1. トレーサビリティを確認します: 要件 → 設計提案 → Issue → テスト → 実装の対応が追えること
   2. PR内容を組み立てます
      - title: 英語Conventional Commits形式(`type(scope): description`)。squash merge時のcommit titleになるため英語必須([`naming-policy.md`](../../rules/naming-policy.md))
      - body: `## 背景` / `## 課題` / `## 選択肢` / `## 完了条件` + `## 関連Issue`
        (`Closes #N`) + 必要なら`## 未対応事項`
      - 実行した検証と実行できなかった検証を明記します
   3. commit message、title、body、差分要約を提示し、意思決定レポートで承認を得ます
   4. 承認後にcommitします
   5. remoteまたはGitHub認証が未設定の場合は、pushとPR作成を行わず、作成予定の
      title/bodyと次に必要な設定を報告します
   6. remoteとGitHub認証が利用できる場合はpushし、`gh pr create`でPRを作成します
4. `phase-state.json`の`ship`を完了へ更新し、結果(commit一覧、mergeまたはPR URL、
   または未実施理由)を報告します

---

次のステップ:

1. `/status` — 次のマイルストーン/Issueの確認
