管理責任: 利用可能な検証をすべて実行し、結果と未実行の検証を報告します。何かを修正する
ことはありません。
ワークフロー: run(red)とrun(green)の両方から呼ばれる横断コマンド
状態確認先: `tmp/{work-dir}/phase-state.json`の`verify`

権限: `tmp-write`
副作用: 検証実行と結果レポート(`tmp/`)
承認: 不要です。

利用可能な検証をすべて実行し、結果と未実行の検証を報告します。

## 読み込む文書

1. `justfile`(`verify`レシピの構成)を確認します
2. 対象`docs/milestones/m{N}-*.md`の完了条件を確認します

## 手順

0. `tmp/{work-dir}/phase-state.json`が存在する場合、`docs`フェーズの完了状態を確認します
   - `completed`に`docs`がある → 通過
   - `skipped`に`docs`があり`skip_reasons.docs`に理由がある → 警告を表示して通過
   - いずれでもない → エラーを出力して中断します

     ```text
     ✗ docsフェーズが未完了です。/build:docs を実行してから再試行してください。
       スキップする場合はphase-state.jsonのskippedに"docs"を追加し、
       skip_reasons.docsにスキップ理由を記録してください。
     ```

1. `just verify`(treefmt / rumdl / bats / check-readme)を実行します
2. `nix flake check --print-build-logs`を実行します(サンドボックスやNixキャッシュ権限で
   実行できない場合はnot-runとして理由を報告します)
3. 失敗がある場合は、対象ファイルと修正方針を列挙します
4. 手動テストが必要な変更(コマンド本文、生成物の体験)は、確認手順を提示します
5. `tmp/{work-dir}/`配下で作業中の場合は`phase-state.json`の`verify`を更新します

## 報告形式

```text
🔎 検証結果

実行済み: just verify(OK / NG: 詳細)
未実行:   nix flake check(必要な場合のみ理由)
手動確認: <必要な場合のみ手順>
```

---

次のステップ:

1. 成功時: `/review:code` または `/ship:readiness`
2. 失敗時: 修正後に再実行
