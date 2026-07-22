# .codex

## 1. 概要

Codex CLI向けのアダプターを置くディレクトリです。ワークフローの内容そのもの(harness非依存の
決めごと)は`agent-workflow/`が正本で、ここはCodex固有の実行機構だけを持つ薄いアダプターです
(Issue #114/#115/#125)。

## 2. 責任

- `hooks.json`: Codex hook設定
- `hooks/`: Codex hookスクリプトと運用説明

Codex/Claude共通の入口は、リポジトリルートの`AGENTS.md`です。Codexで擬似コマンドや
ワークフローを使う場合も、ルート`AGENTS.md`から`agent-workflow/`の正本へ到達します。

## 3. 責任外

- ワークフローの内容そのもの(`../agent-workflow/`が持ちます)
- Codex/Claude共通の入口(`../AGENTS.md`が持ちます)

## 4. 検証済み事項

`codex debug prompt-input`で、リポジトリ直下から起動したCodexはルート`AGENTS.md`を初期
コンテキストへ入れる一方、`.codex/AGENTS.md`は自動読込しないことを確認しました。
このため`.codex/AGENTS.md`は入口として使わず、ルート`AGENTS.md`へ集約します。
