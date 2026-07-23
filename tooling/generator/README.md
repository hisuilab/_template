# tooling/generator

## 1. 概要

Profile を読み込んでプロジェクト一式を生成する Python パッケージです。loader → resolver → planner → renderer → applier の 5 段階パイプラインで動作します。

## 2. 責任

- `models.py`: パイプライン共通データ型（`LangSpec` / `GenerateRequest` / `PlannedFile` / `GenerationPlan` / `GenerationResult` / `InjectResult` / `ManifestData`）
- `errors.py`: 各段階エラー型（`LoadError` / `ResolveError` / `PlanError` / `RenderError` / `ApplyError` / `WorkspaceError` / `ManifestError`）
- `loader.py`: `profile.toml` / `part.toml` を `ProfileSchema` / `PartSchema` にデシリアライズ（LOAD 段階）。`load_part()` で単一 Part を ID から読み込み、Part ID とディレクトリ名の一致を検証する。`load_parts_for_profile()` は `load_part()` に委譲する
- `resolver.py`: Part 間の `requires` 依存をトポロジカルソートで解決（RESOLVE 段階）
- `planner.py`: 変数束縛・`dot-` プレフィックス除去・`{{変数}}` パス置換・衝突検出で `GenerationPlan` を生成（PLAN 段階）。変数は Profile variables を基底に予約語（`project_name`）で上書きする優先順位。`strategy="add"` は同名ファイルを先勝ちで維持。`strategy="append"` は同一 `dest_path` の複数断片をすべて収集し、`renderer.py` が結合する（issue #134）
- `renderer.py`: `{{変数}}` をファイル内容へ適用し staging ディレクトリへ書き込み（RENDER 段階）。同一 `dest_path` の `PlannedFile` が複数ある場合は空行区切りで結合する（`append` 戦略対応）
- `applier.py`: staging → 出力先への原子的コピー（APPLY 段階）。`inject()` は既存ファイルをスキップする加算コピー（上書きなし）。I/O 失敗時は追加済みファイルをロールバックする
- `manifest.py`: `.template-manifest.toml` の読み書き（`write_manifest` / `read_manifest` / `update_manifest`）。生成プロジェクトのルートに置き、適用済み Part ID を記録する
- `workspace.py`: `init-workspace` ロジック（`template/workspaces/` 固定テンプレートの適用と `nix flake update` 実行）
- `wizard.py`: `create` サブコマンド用対話型ウィザード（`WizardAnswers` / `run_wizard(prefill=)`）。`prefill` で指定したフィールドは質問をスキップ
- `cli.py`: `generate` / `inject` / `init-workspace` / `create` サブコマンドの実装。`generate` の `--output` は出力先ディレクトリ（省略時は `{cwd}/{name}/{name}-main`）、`init-workspace` の `--path` はワークスペースディレクトリ（例: `~/Projects`）。`inject` 全skip時は manifest を更新せず exit 0。manifest 書き込み失敗時は復旧案内を出して exit 2。`--role` 部分成功時は失敗 role を案内して exit 2
- `__main__.py`: `python3 -m tooling.generator` エントリポイント

## 3. 責任外

- Profile・Part の内容（`template/` が持ちます）
- e2e テスト・生成先での `just verify` 実行（M4 が担当します）
