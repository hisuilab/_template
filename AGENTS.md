# AGENTS

## 目次

- [1. AIエージェント運用ワークフロー](#1-aiエージェント運用ワークフロー)
- [2. コミットメッセージ](#2-コミットメッセージ)

## 1. AIエージェント運用ワークフロー

このプロジェクトのAIエージェント運用ワークフロー(Rigor Mode・フェーズ・Role・Handoff・
命名・権限・レビューループ・Audit Gate)の正本は、リポジトリ直下の`agent-workflow/`です。
Claude Codeは`CLAUDE.md`からこのファイルを参照し、Codexはルート`AGENTS.md`を自動読込するため、
Claude/Codex共通の入口はこのファイルです。

作業開始時は、依頼内容に応じて次の正本を確認します。

- ワークフロー全体、フェーズ、自然言語ルーティング: `agent-workflow/rules/workflows.md`
- Role(Manager/Architect/Programmer/Reviewer/Tester)の責務: `agent-workflow/rules/roles.md`
- commit・branch・作業ファイルの命名規則: `agent-workflow/rules/naming-policy.md`
- 操作の権限レベルと承認ルール: `agent-workflow/rules/command-permissions.md`
- 作業開始・変更・Gitと外部操作・完了報告の基本方針: `agent-workflow/rules/policy.md`

ユーザーが`/auto:issue`、`/plan:design`、`/build:implement`、`/review:code`、`/verify`などの
ワークフローコマンド名を指定した場合は、対応する`agent-workflow/commands/`配下のMarkdownを
読んで、その指示に従います。たとえば`/auto:issue`は
`agent-workflow/commands/auto/issue.md`を確認します。

`/issue:auto`のように順序が入れ替わった表記を受けた場合は、正しい表記(`/auto:issue`)へ
読み替えられるかを確認し、対応する正本を読んでから作業します。

## 2. コミットメッセージ

- 英語で、[Conventional Commits](https://www.conventionalcommits.org/)形式(`type(scope): description`)で書きます
- `type`は`build`/`chore`/`ci`/`docs`/`feat`/`fix`/`perf`/`refactor`/`revert`/`style`/`test`のいずれかを使います
- この形式は`.pre-commit-config.yaml`の`conventional-pre-commit`フック(`--strict`)で強制されており、違反するコミットは`commit-msg`フックで拒否されます
