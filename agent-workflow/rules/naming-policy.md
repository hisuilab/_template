# Naming Policy / 命名ポリシー

Milestone/Issue、commit、branch、作業ファイルの命名規則を一箇所に集約します。

人間が一覧で読む名前と、CI・Git・AIエージェントが機械処理する名前を分離します。**Issue body・PR bodyは日本語、git履歴に残る識別子（commit・PR title）は英語**を原則とします。

## 目次

- [1. 人間向けの名前](#1-人間向けの名前)
- [2. 機械処理向けの名前](#2-機械処理向けの名前)
  - [2.1. コミットトレーラー](#21-コミットトレーラー)
- [3. ファイルとディレクトリ名](#3-ファイルとディレクトリ名)
- [4. 文書の状態管理](#4-文書の状態管理)
- [5. 例外](#5-例外)

## 1. 人間向けの名前

| 対象 | 形式 | 例 |
| --- | --- | --- |
| マイルストーン文書title | `M{N} 日本語説明` | `M1 検証の深化` |
| Issue title(Production Mode) | `type: 日本語説明` | `feat: base Partの骨格を実装する` |
| Issue / PR body | 日本語、です・ます調。`## 背景` / `## 課題` / `## 選択肢` / `## 完了条件`の4節構成 | - |

`type`は英語のConventional Commits形式(`feat` / `fix` / `docs` / `test` / `refactor` /
`chore`等。`AGENTS.md`が正本)を使います。

## 2. 機械処理向けの名前（git履歴に残るもの）

GitHub の squash merge はPR titleをそのままコミットメッセージ1行目に使うため、
PR titleはcommit messageと同じく英語Conventional Commits形式にします。

## 2. 機械処理向けの名前

| 対象 | 形式 | 例 |
| --- | --- | --- |
| Commit message | 英語Conventional Commits(`AGENTS.md`が正本) | `feat(validator): enforce stack allowed_roles compatibility` |
| PR title(Production Mode) | 英語Conventional Commits形式(`type(scope): description`) | `feat(generator): add create subcommand with questionary wizard` |
| Milestone branch(Prototype Mode) | `m{N}-slug`(slugは短い英語) | `m1-validation-depth` |
| Issue branch(Production Mode) | `type/issue-N-topic`(topicは短い英語) | `feat/issue-12-profile-resolver` |
| Release branch | `chore/release-x.y.z` | `chore/release-0.1.0` |
| Release tag | `vX.Y.Z` | `v0.1.0` |

コミット履歴はCI・ツール・AIエージェントの機械処理対象のため英語へ統一し、パースコストと
トークン消費を抑えます。branchの`slug`/`topic`に日本語・空白・記号を含めません。

### 2.1. コミットトレーラー

AIエージェントのコミットには`Role:`トレーラーを付与します。git履歴からどのロールの作業かを
追跡できます。

```text
<type>(<scope>): <description>

<body>

Co-Authored-By: <エージェント名> <noreply@example.com>
Role: Programmer
```

- `Role:`の値は[`roles.md`](roles.md)のロール名(Manager / Architect / Programmer /
  Reviewer / Tester)です
- 複数ロールにまたがるコミットは、主要な変更種別のロールを1つ記載します
- 人間のコミットでは任意です

## 3. ファイルとディレクトリ名

| 対象 | 形式 | 例 |
| --- | --- | --- |
| マイルストーン文書 | `docs/milestones/m{N}-slug.md` | `docs/milestones/m1-validation-depth.md` |
| Decision Record | `docs/decisions/YYYY-MM-DD-slug.md` | `docs/decisions/2026-07-10-role-revival-validation.md` |
| 作業ディレクトリ(Prototype) | `tmp/milestone-{N}/` | `tmp/milestone-4/` |
| 作業ディレクトリ(Production) | `tmp/issue-{N}/` | `tmp/issue-12/` |
| フェーズ状態 | `tmp/milestone-{N}/phase-state.json` | `tmp/milestone-4/phase-state.json` |
| レビューレポート | `tmp/milestone-{N}/{prefix}-review.md` | `tmp/milestone-4/code-review.md` |

ファイル名・ディレクトリ名は英数字、ハイフン、日付、マイルストーン/Issue番号で構成し、
日本語ファイル名は使いません。

## 4. 文書の状態管理

ライフサイクルを持つ文書種別(draft・milestone・decision・design-proposal)は、ファイル
先頭のYAML frontmatterで状態を管理します。ルール・スキーマ・遷移タイミングの正本は
[`docs/development/document-status.md`](../../docs/development/document-status.md)
です。テンプレートの正本は[`tmp/docs/_template/`](../../tmp/docs/_template/README.md)、
`status`値の妥当性は`scripts/check-status`が`just verify`で検証します。

## 5. 例外

Milestone/Issueに紐づかない横断作業は、用途が分かる英語slugのbranchを使います
(例: `chore/update-fixtures`)。例外を追加する場合は、理由と影響範囲をcommit本文または
PRへ記録します。
