---
status: implemented
proposed_at: 2026-07-23
approved_at: 2026-07-23
approved_by: PM
implemented_at: 2026-07-23
related: "#140"
---

# 設計提案: AI agent向けLSP/MCP semantic探索環境の調査とPoC方針

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
  - [4.1. rootへのnixd追加判断](#41-rootへのnixd追加判断)
  - [4.2. 言語テンプレートへのLSP package候補](#42-言語テンプレートへのlsp-package候補)
  - [4.3. MCP adapter評価](#43-mcp-adapter評価)
  - [4.4. agent探索方針（AGENTS.md記載案）](#44-agent探索方針agentsmd記載案)
  - [4.5. fallback方針](#45-fallback方針)
  - [4.6. hooksによる強制の扱い](#46-hooksによる強制の扱い)
  - [4.7. テンプレート反映のfollow-up](#47-テンプレート反映のfollow-up)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

現在のAI agentはリポジトリ探索でテキスト検索（ripgrep）とファイル読み取りに依存しています。
`definition`・`references`・`diagnostics`などのsemantic探索はLSP serverが提供できますが、
rootの`flake.nix`にも生成される言語テンプレートにも、明示的なLSP serverが含まれていません。

改善策として、LSP serverをNix devShellで管理し、必要に応じてMCP server経由でsemantic探索に
使えるようにする案があります。本Issueでは調査とPoC方針の決定を行います。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| rootと言語テンプレートへ追加するLSP package候補の確定 | 生成テンプレートへの実際の反映（#116後のfollow-up Issue） |
| rootへの`nixd`追加判断 | MCP serverの本番採用・標準化 |
| read-only LSP MCP adapterの評価 | hooksによるLSP/MCP強制 |
| `agent-workflow/`へのagent探索方針追記 | Codex以外のharnessへの対応 |
| LSP/MCPが利用できない場合のfallback方針の文書化 | — |

## 3. 選択肢

| # | 内容 | 評価 |
| --- | --- | --- |
| A | agent探索方針のみ`AGENTS.md`/`agent-workflow`へ追記し、LSP/MCP導入は見送る | 調査コストは最小ですが、editorとAI agentがLSP serverを共有できる利点を捨てることになります |
| B（推奨） | LSP serverをNix devShellで管理する方針を検証し、MCPはread-only PoCとして扱う | nixpkgsに候補がすべて揃っていることを確認済みです。MCP adapterは`mcp-language-server`(nixpkgs収録)を対象にread-only toolに絞って評価します |
| C | LSP/MCPを標準化し生成テンプレートにも一括反映する | adapter安定性・security境界・Codex差分の確認前に標準化するのは時期尚早です |

採用案はBです。

## 4. 設計案

### 4.1. rootへのnixd追加判断

rootへの`nixd`追加を推奨します。

`nixd`(2.9.1、nixpkgs収録)はNix言語のLSP serverです。このリポジトリ自体が`flake.nix`・
`treefmt.nix`・`template/parts/**/flake.nix`を多数含むため、Nix編集時のsemantic支援は
有効です。エディタ統合・AI agent・将来のMCP adapter（Nix対応が可能な場合）が同一
binaryを参照できます。

root `flake.nix` の `devShells.default.packages` への追加対象:

```nix
pkgs.nixd
```

> [!NOTE]
> `nixd`は`nix-doc`（ドキュメント生成、同名パッケージ）とは別物です。nixpkgsでは
> `pkgs.nixd`が`sonixd`(Feature-rich Subsonic desktop music player)と混同されることも
> ありますが、`pkgs.nixd`(2.9.1)はNix language serverとして正しく識別されています。

### 4.2. 言語テンプレートへのLSP package候補

nixpkgsで利用可能なパッケージをコードで確認しました。

| 言語テンプレート | LSP package | nixpkgs名 | 確認バージョン |
| --- | --- | --- | --- |
| `lang/python` | Pyright | `pkgs.pyright` | 1.1.411 |
| `lang/typescript` | TypeScript Language Server | `pkgs.typescript-language-server`、`pkgs.typescript` | 5.3.0 / 5.9.3 |
| `lang/rust` | rust-analyzer | `pkgs.rust-analyzer` | 2026-06-15 |
| `lang/go` | gopls | `pkgs.gopls` | 0.23.0 |

これらの追加は#116後のfollow-up Issueで実施します。本Issueでは候補の確認にとどめます。

### 4.3. MCP adapter評価

**対象: `mcp-language-server`（nixpkgs収録、BSD-3）**

nixpkgsに`mcp-language-server`(0.1.1)が存在することを確認しました。
homepage: <https://github.com/isaacphi/mcp-language-server>

このMCP serverはLSP serverを内部で起動し、AI agentへ次の6ツールを提供します。

| ツール | 種別 | 説明 |
| --- | --- | --- |
| `definition` | read-only | シンボルの定義箇所とソースを返します |
| `references` | read-only | シンボルの参照一覧を返します |
| `diagnostics` | read-only | ファイルの警告・エラーを返します |
| `hover` | read-only | シンボルのドキュメント・型情報を返します |
| `rename_symbol` | **write** | プロジェクト全体でシンボルを一括リネームします |
| `edit_file` | **write** | 行番号ベースでファイルを編集します |

**評価結果:**

- read-only 4ツール（definition・references・diagnostics・hover）は副作用のない探索用途としてPoC対象にできます（tool制限・security境界・Codex対応はPoC前の未確認事項のため断定しません）
- `rename_symbol`・`edit_file` はwrite操作であり、信頼性・rollback・review UXが確認できるまで
  標準採用しません
- `mcp-language-server` はbeta版（v0.1.1）です。本番標準化ではなくPoC評価として扱います
- 設定形式はMCPクライアント側の設定（`claude_desktop_config.json`等）で`--workspace`と
  `--lsp`を指定します。Nix管理下のbinaryを指定できるため、devShellと同じLSP serverを
  参照できます

**PoC方針:**

1. read-only 4ツールに限定して利用します（write toolはMCPクライアント側で除外設定を
   推奨します。ただしv0.1.1時点でtool単位の除外APIは未確認のため、利用者判断とします）
2. workspace symbols・definition・referencesなどのsemantic探索をテキスト検索の補完として
   使います（テキスト検索を代替するものではありません）
3. 常時contextへ読み込まず、必要時に発見・接続する方式を優先します
4. index未完了・未対応言語・MCP server未起動時はfallbackに切り替えます

**MCPを延期しない理由:**

nixpkgsに`mcp-language-server`が収録済みであり、LSP serverもすべてnixpkgs経由で管理できます。
PoCとして評価できる条件が揃っているため、評価を延期する理由はありません。
ただし本番標準化は条件（read-only制限確認・security境界確認・Codex差分確認）が満たされるまで
行いません。

### 4.4. agent探索方針（AGENTS.md記載案）

root `AGENTS.md`（このリポジトリ向け）にsemantic探索方針を追記します。
これが本PRの実装範囲です。

`features/ai-agent`のpayload `AGENTS.md`（生成プロジェクト向け）と
`agent-workflow/`へのsemantic探索方針反映は #116 後のfollow-up Issueで実施します。

追記する方針の概要は次の通りです（root `AGENTS.md` に実施済み）。

```text
## リポジトリ探索

AI agentはリポジトリ探索に次の優先順位で使います。

1. テキスト検索（ripgrep）とファイル読み取りを基本とします
2. LSP serverがdevShellで利用可能な場合、semantic探索（definition・references・
   diagnostics・hover）をテキスト検索の補助として使います
3. MCP serverが設定されている場合、read-only toolを任意のsemantic探索補助として使います
4. LSP/MCPが利用できない場合はテキスト検索にfallbackします
```

### 4.5. fallback方針

LSP/MCPが利用できない場合のfallback方針を文書化します。

| 状況 | fallback |
| --- | --- |
| MCP server未起動・設定なし | ripgrep + ファイル読み取りで代替します |
| LSP serverが未インストール | ripgrep + ファイル読み取りで代替します |
| LSP index未完了 | indexが完了するまでテキスト検索で代替し、index完了後に再試行します |
| 未対応言語 | テキスト検索で代替します |
| stale result（indexと実ファイルの乖離） | ファイル読み取りで内容を直接確認します |
| MCP toolがwrite操作を実行しようとした | toolの実行を停止し、ユーザーへ確認します |

fallback方針はhooksで強制しません。agent側の判断で切り替えます（4.6節参照）。

### 4.6. hooksによる強制の扱い

現時点ではhooksによるLSP/MCP強制はscope外です。

理由は次の通りです。

- LSP/MCPはeditorとAI agentの任意の補助ツールであり、必須の実行ゲートにはなりません
- MCP serverが未起動でも`just verify`（lint・test・format）は正常に動作します
- write toolを含むMCP serverをhookで強制すると、意図しない書き換えのリスクがあります
- beta版（v0.1.1）のtoolを必須化するには安定性の根拠が不十分です

将来的にread-only toolの活用が定着し、安定性が確認された段階でhook組み込みを再検討します。

### 4.7. テンプレート反映のfollow-up

本Issueの完了後に実施するtemplate反映のfollow-up Issueを特定します。

| タイミング | 内容 |
| --- | --- |
| #116（`features/ai-agent`同梱方針決定）後 | `features/ai-agent`のpayload `AGENTS.md`にsemantic探索方針を追記します |
| #116後 | 言語テンプレート（lang/python・typescript・rust・go）の`flake.nix`に各LSP packageを追加するfollow-up Issueを作成します |
| MCP PoCの結果確認後 | MCP設定方針を`agent-workflow`または`features/ai-agent`のドキュメントへ反映するかを判断します |

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| `pkgs.nixd`が既存devShellと競合する | devShellの起動が失敗する | rootの`flake.nix`から`pkgs.nixd`を削除してロールバックします |
| `mcp-language-server`がread-only toolで意図しない副作用を持つ | agentが誤った情報を元に作業する | MCP serverを切断し、テキスト検索にfallbackします |
| 言語LSP packageがテンプレートのdevShellサイズを大幅に増加させる | `nix develop`の初期化時間が増加する | 言語別のオプション設定（feature flag等）を検討します |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| 文書 | このdesign docのfrontmatter・目次・リンク・です・ます調を確認します |
| 完了条件チェック | Issue #140の7項目の完了条件がすべて満たされていることを確認します |
| 既存検証 | `nix develop --command just verify`がgreenになることを確認します（コード変更がない場合は無影響） |

## 7. 未解決事項

| ID | 論点 | 決定者 | ブロックする作業 |
| --- | --- | --- | --- |
| U-01 | `mcp-language-server`のwrite tool（rename_symbol・edit_file）をtool単位で除外できるか | MCP adapter評価時に確認 | write tool除外の標準化 |
| U-02 | `nixd`をrootへ追加する実際のflake.nix変更（本Issueはscope外） | follow-up Issue | root devShellでのnixd提供 |
| U-03 | 言語テンプレートへのLSP package追加（#116後のfollow-up Issue） | Issue #116完了後 | テンプレートへのLSP反映 |
| U-04 | Codex環境でのMCP server設定方法（Claude Codeと設定形式が異なる） | MCP PoC時に確認 | Codexでのsemantic探索 |
