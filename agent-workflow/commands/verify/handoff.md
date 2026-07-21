管理責任: 次フェーズを、会話履歴なしで開始できるだけの文書が揃っているか検証します。
何かを修正することはありません。
ワークフロー: 各フェーズ境界の横断チェック
状態確認先: `tmp/verify/YYYY-MM-DD-{phase}.md`

権限: `tmp-write`
副作用: `tmp/verify/YYYY-MM-DD-{phase}.md`の作成・上書き
承認: 不要です。

次フェーズを会話履歴なしで開始できるか検証します。担当Role: Tester。

## 読み込む文書

引数`$ARGUMENTS`から検証対象フェーズを読み取ります。詳細な評価軸は
[`agent-workflow/skills/handoff-check/SKILL.md`](../../skills/handoff-check/SKILL.md)を参照します。
フェーズに応じて読む文書を限定します。

| フェーズ | 読む文書 | 検証する能力 |
| --- | --- | --- |
| `requirements` | `docs/draft/project-direction.md`(Why/Who/What) | アーキテクチャ設計を始められるか |
| `architecture` | 上記 + `docs/draft/project-direction.md`(How) | マイルストーン分解または詳細設計を始められるか |
| `design` | 上記 + 対象`docs/milestones/m{N}-*.md` | テスト先行を始められるか |
| `implement` | 対象マイルストーン文書、対象ディレクトリのREADME.md | 実装を始められるか |
| `ship` | 差分、検証結果、レビュー結果 | 出荷フェーズへ進めるか |

## 手順

1. 利用可能なsubagent機構で、会話履歴を使わず指定文書だけを読ませます
2. 次の形式で`tmp/verify/YYYY-MM-DD-{phase}.md`へ記録します

   ```markdown
   ## Handoff検証: {phase}

   ### 判定: 開始できる / 開始できない / 人間判断が必要

   ### 不足している情報

   - ...

   ### 暗黙知として残っている判断

   - ...

   ### 補完が必要な箇所

   - ...
   ```

3. 結果の要約とレポートパスを提示します

---

次のステップ:

1. 開始できる: 対応フェーズのコマンド
2. 開始できない: `/build:docs`または`/think:clarify`
