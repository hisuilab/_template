# .codex

## 1. 概要

Codex CLI向けのアダプターを置くディレクトリです。ワークフローの内容そのもの(harness非依存の決めごと)は`agent-workflow/`が正本で、ここは薄いアダプターです(Issue #114/#115)。

## 2. 責任

- `AGENTS.md`: Codexへの入口。`agent-workflow/rules/`を読むよう指示する薄いプローズ

## 3. 責任外

- ワークフローの内容そのもの(`../agent-workflow/`が持ちます)

## 4. 未検証事項

- Codexがルート`AGENTS.md`とは別に`.codex/AGENTS.md`というパスを自動探索・読み込みするかは、実際の`codex` CLIでの動作確認が必要です(このセッションでは`codex` CLIが利用できず検証できていません)。自動探索が成立しない場合、ルート`AGENTS.md`への追記など別方式への切り替えが必要になります(設計doc `docs/design/issue-114-agent-workflow-portability.md` 4.3節・7節U-01a参照)
