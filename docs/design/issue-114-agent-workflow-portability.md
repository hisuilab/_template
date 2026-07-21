---
status: proposed
proposed_at: 2026-07-21
approved_at: null
approved_by: null
implemented_at: null
related: "#114"
---

# 設計提案: `.claude`ワークフローをharness非依存な正本とアダプターへ分離する

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
  - [4.1. ディレクトリ構成](#41-ディレクトリ構成)
  - [4.2. 責務分離](#42-責務分離)
  - [4.3. 参照方式](#43-参照方式)
  - [4.4. git追跡方針](#44-git追跡方針)
  - [4.5. 移行方針(Issue #115で実施)](#45-移行方針issue-115で実施)
  - [4.6. Decision Record更新方針](#46-decision-record更新方針)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

現在`.claude/`配下でAIエージェント運用ワークフロー(Rigor Mode・フェーズ・Role・Handoff・
命名・権限・レビューループ・Audit Gate)を管理しています。この中には次の2種類の内容が
混在しています。

- **harness非依存な概念層**: `.claude/rules/*.md`(`workflows.md`・`roles.md`・
  `naming-policy.md`・`policy.md`・`command-permissions.md`)。フェーズ・Role・Handoff・
  命名・権限という「決めごと」であり、どのAIツールが実行するかに依存しません
- **Claude Code実行機構依存の内容**: `.claude/commands/*.md`(スラッシュコマンド)・
  `.claude/agents/*.md`(subagent定義。`tools:`・`model:`フィールド)・
  `.claude/skills/*/SKILL.md`(Skillツールの自動発火)・`.claude/hooks/`(hookイベント)

Codexなど他のagentプラットフォームでもこのワークフローの「決めごと」部分を使えるように
したいという要望があり、既存のGitHub App/OSS([ECC](https://github.com/affaan-m/ECC))の
構成を調査しました。ECCは概念層(`rules/`・`skills/`等)をharness非依存のトップレベル
ディレクトリに置き、`.claude/`・`.codex/`等はそれを参照する薄いadapterとして
git追跡する構成をとっています。

なお`.claude/`が非追跡である現状の理由(`docs/decisions/2026-07-13-ai-agent-claude-scope.md`)
は「実験運用中だから」であり、恒久的な設計判断ではありませんでした。本Issueはこの前提を
明示的に見直します。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `_template`自身の開発ワークフロー(`agent-workflow/`・`.claude/`・`.codex/`の構成設計) | `codex` CLIでの実機動作確認(Issue #115) |
| 正本の置き場所・命名・責務分離の決定 | 生成先プロジェクトへの反映(`features/ai-agent`、Issue #116) |
| git追跡範囲の方針決定 | `.claude/commands`等の実ファイルの書き換え作業そのもの(Issue #115で実施) |
| 既存Decision Recordの更新方針 | Codex以外のharness(Cursor・Gemini等)への対応 |

## 3. 選択肢

| # | 内容 | 評価 |
| --- | --- | --- |
| A | 縮小版: `.claude/rules/`のみ独立・追跡対象にし、`commands`/`agents`/`skills`/`hooks`は現状維持 | 影響ファイル数は最小ですが、Codex側が参照できるのはrulesのみに留まり、「共通ワークフロー」としての体験は限定的です |
| B | フルECC構成: トップレベル`agent-workflow/`を正本にし、`.claude/`・`.codex/`双方を薄いadapterとして再編・追跡する | 影響ファイル数(31件規模、加えて新設ディレクトリ分のREADME.md、4.5節参照)は大きいですが、Codex側でもRole・フェーズ・レビューループの記述に到達でき、「どのagentプラットフォームでも共通ワークフロー」という目的に最も合致します |
| C | 現状維持: `.claude/`を非追跡のまま、Codex側は都度`.claude`を読みに行くローカルadapterにする | `chore/claude-workflow-source`ブランチで検討しましたが、他クローン・CIへ何も伝播しないため目的を達成できず、破棄済みです |

採用案はBです。

## 4. 設計案

### 4.1. ディレクトリ構成

```text
_template/
├── AGENTS.md                    # 既存。薄い入口のまま(32KiB制約を踏まえ本文は増やさない)
├── CLAUDE.md                    # 既存。@AGENTS.md import のまま
├── agent-workflow/               # 【新設・git追跡】harness非依存の正本
│   ├── README.md                 # 責任(概要/責任/責任外)
│   ├── rules/                    # .claude/rules/*.md を移動
│   │   ├── workflows.md
│   │   ├── roles.md
│   │   ├── naming-policy.md
│   │   ├── policy.md
│   │   └── command-permissions.md
│   ├── commands/                  # フェーズ別の実行契約(読む文書・権限・副作用・次フェーズ)
│   │   ├── think/ plan/ build/ review/ ship/ verify/ auto/ template/
│   ├── agents/                    # Role(Architect/Programmer/Reviewer/Tester)の役割記述本文
│   └── skills/                    # design-review/docs-sync/handoff-check/security-review の手順本文
│
├── .claude/                       # 【縮小・git追跡】Claude Code固有の実行機構のみ
│   ├── commands/*.md              # frontmatter + agent-workflow/commands/を読む指示
│   ├── agents/*.md                # tools:/model:等Claude固有フィールド + agent-workflow/agents/参照
│   ├── skills/*/SKILL.md          # frontmatter(name/description) + agent-workflow/skills/参照
│   └── hooks/                     # Claude Code hookイベント(他harness対応物なし、Claude専用のまま)
│
├── .codex/                        # 【新設・git追跡】Codexアダプター
│   ├── README.md                   # 責任(概要/責任/責任外)。check-readme対象
│   ├── AGENTS.md                   # 薄い入口。agent-workflow/rules/を参照(32KiB制約を踏まえる)
│   └── agents/*.toml               # (Codexのprofile機構が使える場合の任意追加。Issue #115で要検証)
│
├── template/                      # 既存。無関係、変更なし(Partシステムの正本)
├── tooling/                       # 既存。無関係、変更なし
└── ...
```

### 4.2. 責務分離

| ディレクトリ | 責務 | 責務外 |
| --- | --- | --- |
| `agent-workflow/README.md` | このディレクトリ自体の概要/責任/責任外(`check-readme`対象) | 個別rules/commands/agents/skillsの内容 |
| `agent-workflow/rules/` | Rigor Mode・フェーズ・Role・Handoff・命名・権限などharness非依存の決めごと | 特定AIツールの実行機構 |
| `agent-workflow/commands/` | フェーズ別実行契約(読む文書・権限・副作用・次フェーズ)のharness非依存な記述 | スラッシュコマンドの起動構文そのもの |
| `agent-workflow/agents/` | Role(Architect/Programmer/Reviewer/Tester)の役割・評価軸の本文 | subagentのツール制限・モデル指定(harness依存)。`.claude/agents/`とは同じ「agents」語を使いますが別物です(注記参照) |
| `agent-workflow/skills/` | レビュー・docs同期・handoff確認の詳細手順本文 | Skillツールの自動発火条件(harness依存) |
| `.claude/commands/`・`.claude/agents/`・`.claude/skills/` | Claude Code固有の実行機構(スラッシュコマンド起動・subagentツール制限・Skill自動発火)。frontmatter + `agent-workflow/`参照のみを持つ | `agent-workflow/`内容の複製 |
| `.claude/hooks/` | Claude Code hookイベント(他harness対応物なし、Claude専用のまま) | `agent-workflow/`との対応(Codex等は「instruction-backed」として扱い、hookの直接的な対応物を持ちません) |
| `.claude/settings.json` | 全開発者で共有するClaude Code設定(hook配線等、秘密情報を含まない) | ローカル権限・セッション状態 |
| `.claude/settings.local.json`・`.claude/scheduled_tasks.lock` | 個人のローカル権限設定・実行中セッションの状態(既存通り非追跡のまま) | 共有すべき設定 |
| `.codex/` | Codex固有の実行機構・入口 | `agent-workflow/`内容の複製 |

**命名の注記**: `agent-workflow/agents/`(Role本文: Architect/Programmer/Reviewer/Tester)と
`.claude/agents/`(Claude Code subagent定義: `tools:`/`model:`フィールド)は同じ「agents」と
いう語を別の意味で使います。混同を避けるため、両ディレクトリのREADME.mdで違いを明記します。

### 4.3. 参照方式

- **Claude Code側**: `CLAUDE.md`の`@AGENTS.md`importで確認済みの通り、Claude Codeは`@file`
  参照が有効です。`.claude/commands/*.md`・`.claude/agents/*.md`・`.claude/skills/*/SKILL.md`
  から`agent-workflow/`配下への`@file`参照は技術的に成立する見込みです
- **Codex側**: 次の2点を分離して検証する必要があります(いずれもIssue #115で実機検証し、
  結果に応じて本設計の4.1〜4.3を更新します)。
  1. **パス発見**: Codexがルート`AGENTS.md`とは別に`.codex/AGENTS.md`というパスを
     自動探索・読み込みする設計になっているか。ECCのリポジトリに`.codex/AGENTS.md`が
     存在すること自体は確認済みですが、これはECCが独自にそのパスへ配置しているだけの
     可能性があり、Codexが自動探索する保証にはなりません。このパス発見が成立しない場合、
     Codexアダプター全体(4.1〜4.3)の前提が崩れるため、最優先で検証します
  2. **`@file`参照構文のサポート**: パス発見が成立した前提で、`.codex/AGENTS.md`から
     `agent-workflow/rules/`への`@file`参照相当が効くか。サポートしない場合、
     `.codex/AGENTS.md`は`agent-workflow/rules/`の要点を手作業で要約する必要があり、
     ECCの`.codex/agents/*.toml`が`developer_instructions`へ本文を直接埋め込んでいるのと
     同じ制約に当たります

### 4.4. git追跡方針

`agent-workflow/`・`.claude/`・`.codex/`のいずれもgit追跡対象にします。理由は次の通りです。

- 秘密情報やユーザー固有の認証状態を含まない(ECCの`.gitignore`も`settings.local.json`等
  真にローカルな状態ファイルのみ除外している)
- 他クローン・CI・将来のコントリビューターへワークフローが伝播しないと、「どのagent
  プラットフォームでも使える」という目的自体を達成できない

現状`.gitignore`は`.claude/`全体を一括除外しています(`.gitignore:12`)。この行を削除して
追跡対象へ切り替えますが、その中でも次のファイルは真にローカルな状態であるため、
個別の除外指定として残します。

| ファイル | 内容 | 追跡方針 |
| --- | --- | --- |
| `.claude/settings.json` | hook配線等、開発者間で共有すべき設定(秘密情報なし) | 追跡する |
| `.claude/settings.local.json` | 個人のツール実行許可リスト(Claude Codeの`.local.json`慣例に基づく個人設定) | 引き続き除外する |
| `.claude/scheduled_tasks.lock` | 実行中セッションのロックファイル(pid/timestamp相当) | 引き続き除外する |

`.gitignore`は次のように書き換えます(具体的な適用はIssue #115で行います)。

```gitignore
# === AI エージェント設定 ===
.claude/settings.local.json
.claude/scheduled_tasks.lock
```

`.codex/`側にも同様のローカル状態ファイルが生成される場合は、Issue #115実施時に同じ方針
(共有設定は追跡・個人設定/lockは除外)で判断します。

### 4.5. 移行方針(Issue #115で実施)

本Issueでは設計のみを行い、実際のファイル移動・書き換えはIssue #115で実施します。移行の
大枠は次の通りです。

1. 現行`.claude/`全体を`tmp/claude-backup-<date>/`へバックアップします
2. `.claude/rules/*.md`を`agent-workflow/rules/`へ移動します
3. `.claude/commands/*.md`・`.claude/agents/*.md`・`.claude/skills/*/SKILL.md`の**本文を
   `agent-workflow/commands/`・`agent-workflow/agents/`・`agent-workflow/skills/`へ移設**
   します(新規に書き起こすのではなく、既存の実運用済み本文をそのまま移す)。移設先の
   対応は次の通りです。
   - `.claude/commands/**/*.md` → `agent-workflow/commands/**/*.md`(フェーズ別実行契約の本文)
   - `.claude/agents/{architect,reviewer,tester}.md` → `agent-workflow/agents/`
     (既存3ファイルのみ移設対象。`programmer`はメインエージェントが兼務、`manager`は
     人間PMのため`.claude/agents/`に対応ファイルが無く、`agent-workflow/agents/`側にも
     追加しません)
   - `.claude/skills/*/SKILL.md` → `agent-workflow/skills/*/SKILL.md`
4. 移設元だった`.claude/commands/*.md`・`.claude/agents/*.md`・`.claude/skills/*/SKILL.md`は、
   frontmatterと`agent-workflow/`参照のみを残す薄い形へ書き換えます
5. `agent-workflow/`配下の新設ディレクトリ(`README.md`・`rules/`・`commands/`配下の各サブ
   ディレクトリ・`agents/`・`skills/*/`)、および`.codex/`(`README.md`含む)に、
   `scripts/check-readme`の要件(概要/責任/責任外)を満たすREADME.mdを作成します
6. `.codex/AGENTS.md`を新設し、`agent-workflow/rules/`への参照(または4.3節の検証結果に
   応じた要約)を記述します
7. `.gitignore`を4.4節の通りに書き換えます
8. 各ステップごとに`nix develop --command just verify`でグリーンを確認します

### 4.6. Decision Record更新方針

`docs/decisions/2026-07-13-ai-agent-claude-scope.md`は「`_template`自身の`.claude/`は
実験運用中でありリスクが高い」という前提で、生成プロジェクトへの同梱を最小限にする判断を
下しています。この前提(実験運用中)は、本ワークフローが20件超のIssueで実運用された実績を
踏まえて成立しなくなっています。本Issueの完了時に、この前提部分を更新する追記を行うか、
新しいDecision Recordとして「`_template`自身の運用は安定運用フェーズへ移行した」ことを
記録します。

`docs/decisions/2026-07-13-ai-agent-unconditional-inclusion.md`(`features/ai-agent`を
全プロファイルに無条件同梱する決定)には本Issueでは触れません。`agent-workflow/`新設後に
`features/ai-agent`の同梱範囲が変わりうる論点はIssue #116のスコープとし、本Issueでは
`features/ai-agent`(生成対象)の同梱範囲そのものの変更を決定しません。

`docs/draft/project-direction.md`のU-08(「`.claude/`が汎用設計に安定するまで確定できない」)は、
本Issueがまさにその前提(`.claude/`の未成熟)を解消しようとする取り組みに対応します。
Issue #116完了時に、U-08の記述を本シリーズ(#114〜#116)の結果を踏まえて更新します。

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| Codexが`@file`参照をサポートしない | `.codex/AGENTS.md`に手動要約が必要になり、`agent-workflow/rules/`更新のたびに追従作業が発生する | Issue #115で確認し、必要なら本設計の4.3を更新する意思決定レポートを別途起票する |
| `agent-workflow/`と`.claude/`の分離が既存コマンドの動作を壊す | フェーズ進行・レビューループが機能しなくなる | Issue #115で1ファイルずつ移行し、都度`just verify`と手動動作確認を行う |
| 本設計が`ready`にならない | Issue #115・#116が着手できない | 本Issue内でレビューループ(上限3回)を回し、解消しない場合は意思決定レポートでPMへ確認する |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| 文書 | `docs/design/`のfrontmatter・目次・リンク・です・ます調を確認する |
| レビュー | reviewer subagentによる設計レビュー(Critical/High = 0) |
| 既存検証 | `nix develop --command just verify`(本Issueではファイル移動を行わないため、原則無影響) |
| 引き継ぎ | Issue #115・#116が本設計を読んで着手できる十分な具体性があることを確認する |

## 7. 未解決事項

| ID | 論点 | 決定者 | ブロックする作業 |
| --- | --- | --- | --- |
| U-01a | Codexがルート`AGENTS.md`とは別に`.codex/AGENTS.md`というパスを自動探索・読み込みするか(パス発見) | Issue #115(実機検証、最優先) | Codexアダプター全体(4.1〜4.3)の前提 |
| U-01b | (U-01aが成立した場合)Codexの`AGENTS.md`が`@file`参照をサポートするか | Issue #115(実機検証) | `.codex/AGENTS.md`の実装方式(参照 or 要約) |
| U-02 | `.codex/agents/*.toml`のようなCodexのprofile機構を追加するか | Issue #115(実機検証結果次第) | Codexアダプターの充実度 |
| U-04 | `features/ai-agent`への反映範囲 | Issue #116 | 生成プロジェクトへの同梱 |

`agent-workflow/`という名称は本設計の決定事項として確定します(未解決事項から除外します)。
3節以降で使用している名称は暫定ではなく本採用です。
