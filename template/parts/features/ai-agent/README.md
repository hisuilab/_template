# template/parts/features/ai-agent

## 1. 概要

AI エージェント向け設定ファイル（`AGENTS.md`・`CLAUDE.md`・`.claude/rules/dev-policy.md`）を追加する features/ai-agent Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言
- `payload/` 配下の生成対象ファイル群（`AGENTS.md`・`CLAUDE.md`・`dot-claude/rules/dev-policy.md`）
- `AGENTS.md` に生成プロジェクト向けの基本方針（リポジトリ探索・コミット規約）を提供する

## 3. 責任外

- AI エージェント以外の features（他 features Part が担当）
- `.claude/commands/`・`.claude/skills/` 等のプロジェクト固有ファイル
