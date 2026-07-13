# tooling/generator

## 1. 概要

Profile を読み込んでプロジェクト一式を生成する Python パッケージです。loader → resolver → planner → renderer → applier の 5 段階パイプラインで動作します。

## 2. 責任

- `models.py`: パイプライン共通データ型（`LangSpec` / `GenerateRequest` / `PlannedFile` / `GenerationPlan` / `GenerationResult`）
- `errors.py`: 各段階エラー型（`LoadError` / `ResolveError` / `PlanError` / `RenderError` / `ApplyError` / `WorkspaceError`）
- `loader.py`: `profile.toml` / `part.toml` を `ProfileSchema` / `PartSchema` にデシリアライズ（LOAD 段階）
- `resolver.py`: Part 間の `requires` 依存をトポロジカルソートで解決（RESOLVE 段階）
- `planner.py`: 変数束縛・`dot-` プレフィックス除去・`{{変数}}` パス置換・衝突検出で `GenerationPlan` を生成（PLAN 段階）
- `renderer.py`: `{{変数}}` をファイル内容へ適用し staging ディレクトリへ書き込み（RENDER 段階）
- `applier.py`: staging → 出力先への原子的コピー（APPLY 段階）
- `workspace.py`: `init-workspace` ロジック（`template/workspaces/` 固定テンプレートの適用と `nix flake update` 実行）
- `wizard.py`: `create` サブコマンド用対話型ウィザード（`WizardAnswers` / `run_wizard(prefill=)`）。`prefill` で指定したフィールドは質問をスキップ
- `cli.py`: `generate` / `init-workspace` / `create` サブコマンドの実装。`--output` は親ディレクトリ（省略時は `{cwd}/{name}/{name}-main`）
- `__main__.py`: `python3 -m tooling.generator` エントリポイント

## 3. 責任外

- Profile・Part の内容（`template/` が持ちます）
- e2e テスト・生成先での `just verify` 実行（M4 が担当します）
