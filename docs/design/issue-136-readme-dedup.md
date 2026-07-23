---
status: approved
proposed_at: 2026-07-23
approved_at: 2026-07-23
approved_by: PM
implemented_at: 2026-07-23
related: "#136"
---

# 設計提案: Part 内 README スケルトンの重複を整理する

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
  - [4.1. 完全一致 README の現状維持](#41-完全一致-readme-の現状維持)
  - [4.2. consistency test の追加](#42-consistency-test-の追加)
  - [4.3. starter src README の表記統一](#43-starter-src-readme-の表記統一)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

`template/parts/` 配下の README スケルトンに完全一致または高類似の文書が複数存在します。
更新漏れが生じた場合、片方の Part だけ記述が古くなるリスクがあります。

| # | 場所 | 状況 |
| --- | --- | --- |
| R-1 | `architecture/layered/payload/src/{application,domain,infrastructure,interface}/README.md` vs `architecture/ddd/` 同パス | 完全一致（4 ファイル） |
| R-2 | `architecture/layered/payload/tests/integration/README.md` vs `architecture/ddd/` 同パス | 高類似（「モジュール」vs「層」「unit」vs「domain/application」で意図的差異あり） |
| R-3 | `starter/{cli,web-api,web-htmx}/payload/src/README.md` | 高類似（各スターター固有の説明を含む。`web-htmx` のみ括弧スタイルが異なる） |
| R-4 | `scale/medium/payload/docs/design/*/README.md` | 類似構造（各ディレクトリ固有の責任が記述されており重複ではない） |

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `tests/unit/test_payload.py`（consistency test 追加） | R-4（各ディレクトリの責任が異なるため変更不要） |
| `architecture/ddd/payload/src/*/README.md`（4 ファイル、所有者注記のみ追加） | `architecture/ddd/payload/tests/integration/README.md`（意図的差異のため変更不要） |
| `starter/web-htmx/payload/src/README.md`（括弧スタイルを全角に統一） | `starter/cli/src`・`starter/web-api/src`（内容が各スターター固有のため現状維持） |

## 3. 選択肢

| # | 方針 | 評価 |
| --- | --- | --- |
| A | 現状維持 + consistency test | 生成後のユーザー可読性を損なわず、更新漏れを CI で検出できる。採用案 |
| B | 共通ファイルを `base` Part に移動して両 architecture から参照 | `base` はすべてのプロジェクトに適用される層で `src/application` 等は architecture 依存。構成が崩れる |
| C | 完全一致 README をシンボリックリンク化 | git でのシンボリックリンクはプラットフォーム依存があり、生成後にユーザーが混乱する |

採用案は A です。

`architecture/layered` と `architecture/ddd` は `conflicts` 関係にあるため生成時は片方のみが
選ばれます。`src/{application,domain,infrastructure,interface}` の 4 README は両 Part で同一内容が
正しい状態です（DDDもレイヤードも同じ 4 層 src/ 構成を持ちます）。
この「意図的一致」を明記し、consistency test で保護します。

## 4. 設計案

### 4.1. 完全一致 README の現状維持

`architecture/ddd/payload/src/{application,domain,infrastructure,interface}/README.md` の 4 ファイルは
`architecture/layered` との意図的一致であることを追記します。

各ファイルの末尾に以下のコメントを追加します（生成後のユーザーには不要なので HTML コメントで隠します）。

```markdown
<!-- この README は architecture/layered/payload/src/<dir>/README.md と同一内容です。
     consistency test (tests/unit/test_payload.py::test_mirrored_readmes) で保護されています。
     内容を変更する場合は両方を同時に更新してください。 -->
```

### 4.2. consistency test の追加

**`tests/unit/test_payload.py` — 追加テスト 1 本**

`architecture/layered` と `architecture/ddd` の `src/*/README.md` が同一内容であることを
CI で保護します。

```python
def test_mirrored_readmes() -> None:
    """architecture/layered と ddd の src/ 配下 README が一致することを確認します。

    両 Part は conflicts 関係にあり生成時は片方のみ適用されますが、
    src/{application,domain,infrastructure,interface}/README.md は同一内容が正しい状態です。
    """
    layered_root = PARTS_ROOT / "architecture" / "layered" / "payload" / "src"
    ddd_root = PARTS_ROOT / "architecture" / "ddd" / "payload" / "src"

    mirrored_dirs = ["application", "domain", "infrastructure", "interface"]
    mismatches: list[str] = []

    for d in mirrored_dirs:
        layered_file = layered_root / d / "README.md"
        ddd_file = ddd_root / d / "README.md"
        if not layered_file.exists() or not ddd_file.exists():
            mismatches.append(f"{d}/README.md: one or both files missing")
            continue
        layered_text = _strip_sync_comment(layered_file.read_text(encoding="utf-8"))
        ddd_text = _strip_sync_comment(ddd_file.read_text(encoding="utf-8"))
        if layered_text != ddd_text:
            mismatches.append(f"{d}/README.md: content differs")

    assert not mismatches, (
        "architecture/layered と ddd の src/ README が一致しません:\n"
        + "\n".join(f"  {m}" for m in mismatches)
    )
```

`_strip_sync_comment()` はファイル末尾の `<!-- ... -->` コメントブロックを除去してから比較します。

### 4.3. starter src README の表記統一

`starter/web-htmx/payload/src/README.md` の括弧スタイルを `cli` / `web-api` と揃えます
（全角括弧 `（）` + スペース区切りに統一）。

変更箇所：`starter/web-htmx/payload/src/README.md` の表記ゆれを以下のように修正します。

- 半角括弧 `()` → 全角括弧 `（）`
- スペースなし → スペースあり（バッククォート前後）
- 対象行: 「テストコード」・「lang 非依存の骨格」・「言語別のサーバー実装」の責任外記述

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| consistency test が既存の差異を検出して CI が失敗 | 追加した test が RED になる | 調査結果では完全一致のため発生しないはずだが、発生時は両ファイルを同期して再 commit |
| HTML コメントが生成物に含まれてユーザーが混乱 | 軽微（コメントは不可視） | 内容に問題なし。必要なら `<!-- -->` を除去する独立 Issue として切り出す |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| 単体テスト（payload） | `test_mirrored_readmes` が GREEN であること |
| 単体テスト（payload） | 既存の `test_no_duplicate_part_ids`・`test_payload_is_not_empty` 等が回帰しないこと |
| Lint / Format | `treefmt --fail-on-change` が成功すること |
| Docs lint | `rumdl check docs/` が成功すること |

## 7. 未解決事項

| ID | 論点 | 決定者 | ブロックする作業 |
| --- | --- | --- | --- |
| U-01 | HTML コメントを README に含めるか否か（コメントを省いて test のみで保護する選択肢もある） | PM | 実装方針の確定 |
| U-02 | `scale/medium/docs/design/*/README.md` および `scale/small/docs/*/README.md` は類似構造だが意図的差異あり。将来的に consistency test の対象とするか | 次 Issue | 本 Issue 対象外 |
