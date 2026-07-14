# tooling/generator

## 1. 概要

Profile を読み込んでプロジェクト一式を生成する Python パッケージです。loader → resolver → planner → renderer → applier の 5 段階パイプラインで動作します。

## 2. 責任

- `models.py`: パイプライン共通データ型（`LangSpec` / `GenerateRequest` / `PlannedFile` / `GenerationPlan` / `GenerationResult` / `InjectResult` / `ManifestData`）
- `errors.py`: 各段階エラー型（`LoadError` / `ResolveError` / `PlanError` / `RenderError` / `ApplyError` / `WorkspaceError` / `ManifestError` / `InjectError`）
- `loader.py`: `profile.toml` / `part.toml` を `ProfileSchema` / `PartSchema` にデシリアライズ（LOAD 段階）。`load_part()` で単一 Part を ID から読み込む
- `resolver.py`: Part 間の `requires` 依存をトポロジカルソートで解決（RESOLVE 段階）
- `planner.py`: 変数束縛・`dot-` プレフィックス除去・`{{変数}}` パス置換・衝突検出で `GenerationPlan` を生成（PLAN 段階）。`strategy="add"` は同名ファイルを先勝ちで維持
- `renderer.py`: `{{変数}}` をファイル内容へ適用し staging ディレクトリへ書き込み（RENDER 段階）
- `applier.py`: staging → 出力先への原子的コピー（APPLY 段階）。`inject()` は既存ファイルをスキップする加算コピー（上書きなし）
- `manifest.py`: `.template-manifest.toml` の読み書き（`write_manifest` / `read_manifest` / `update_manifest`）。生成プロジェクトのルートに置き、適用済み Part ID を記録する
- `workspace.py`: `init-workspace` ロジック（`template/workspaces/` 固定テンプレートの適用と `nix flake update` 実行）
- `wizard.py`: `create` サブコマンド用対話型ウィザード（`WizardAnswers` / `run_wizard(prefill=)`）。`prefill` で指定したフィールドは質問をスキップ
- `cli.py`: `generate` / `inject` / `init-workspace` / `create` サブコマンドの実装。`generate` の `--output` は出力先ディレクトリ（省略時は `{cwd}/{name}/{name}-main`）、`init-workspace` の `--path` はワークスペースディレクトリ（例: `~/Projects`）
- `__main__.py`: `python3 -m tooling.generator` エントリポイント

## 3. 責任外

- Profile・Part の内容（`template/` が持ちます）
- e2e テスト・生成先での `just verify` 実行（M4 が担当します）
