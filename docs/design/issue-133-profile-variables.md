---
status: approved
proposed_at: 2026-07-22
approved_at: 2026-07-22
approved_by: PM
implemented_at: null
related: "#133"
---

# 設計提案: Profile variables を Planner へ渡して置換を有効にする

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
  - [4.1. 変数優先順位](#41-変数優先順位)
  - [4.2. 変更箇所](#42-変更箇所)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

`ProfileSchema.variables` に値を定義しても、`planner.plan()` が
`{"project_name": request.name}` のみで変数束縛を初期化しており、Profile 変数が
一切置換に使われない。全プロファイルの `[variables]` セクションが現時点で空であるため
ユーザー影響はないが、スキーマが約束する機能が動作しないデッドコードになっている。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `tooling/generator/planner.py`(変数マージ追加) | ファイル内容の `{{placeholder}}` 置換(既実装) |
| `tooling/generator/cli.py`(profile variables 引き渡し) | `part.toml` の `placeholders_required` 検証(既実装) |
| `tests/unit/test_generator.py`(テスト追加) | Profile variables の CLI 上書きオプション |
| `docs/design/`(本ファイル) | `[variables]` を使う既存プロファイルへの値追加 |

## 3. 選択肢

| # | 内容 | 評価 |
| --- | --- | --- |
| A | `plan()` に profile variables を渡して実装する | スキーマの約束を果たす。変更行数が少ない。採用案 |
| B | `variables` フィールドを schema・profile・docs から削除する | 既存 TOML の `[variables]` セクションも全削除が必要。現状誰も使えない機能を「なかったこと」にするだけで、将来の再実装コストが増える |

採用案はAです。

## 4. 設計案

### 4.1. 変数優先順位

```text
予約語 > Profile variables
```

- `project_name` は予約語とし、Profile 側から上書きできない
- Profile variables は `project_name` 以外の任意キーを定義できる
- 将来の予約語拡張に備え、予約語セットは `planner.py` 内の定数として管理する

### 4.2. 変更箇所

**`tooling/generator/planner.py`**

```python
# 変更前
variables: dict[str, str] = {"project_name": request.name}

# 変更後
_RESERVED: frozenset[str] = frozenset({"project_name"})

def plan(
    request: GenerateRequest,
    parts: list[PartSchema],
    template_root: Path,
    profile_variables: Mapping[str, str] | None = None,
) -> GenerationPlan:
    variables: dict[str, str] = dict(profile_variables or {})
    # 予約語は上書き不可
    variables["project_name"] = request.name
```

**`tooling/generator/cli.py`**

```python
# 変更前
gen_plan = plan(request, parts, template_root=_TEMPLATE_ROOT)

# 変更後
gen_plan = plan(
    request,
    parts,
    template_root=_TEMPLATE_ROOT,
    profile_variables=extended_profile.variables,
)
```

**`tests/unit/test_generator.py`**

Profile variables がパス置換・コンテンツ置換に使われることを確認するテストを追加します。

```python
def test_plan_profile_variables_substituted_in_path(tmp_path):
    # profile_variables={"app_name": "myapp"} が
    # ファイルパス {{app_name}}/main.py → myapp/main.py へ展開されることを確認
    ...

def test_plan_profile_variables_cannot_override_project_name(tmp_path):
    # profile_variables={"project_name": "evil"} を渡しても
    # variables["project_name"] == request.name になることを確認
    ...
```

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| Profile が `project_name` を `variables` に定義している | 予約語チェックで黙って無視される | エラーにせずログ警告として扱う(厳格化は別 Issue) |
| `profile_variables=None` のコードパス | 既存テストがすべて None を渡すため後方互換 | デフォルト引数 `None` で対応済み |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| 単体テスト | Profile variables がパス・コンテンツ置換に反映されること |
| 予約語テスト | `project_name` が Profile 側から上書きできないこと |
| 既存テスト | `just verify` 全パス(既存 test_generator.py への回帰なし) |

## 7. 未解決事項

| ID | 論点 | 決定者 | ブロックする作業 |
| --- | --- | --- | --- |
| U-01 | Profile variables で `project_name` を上書き試行した場合に警告を出すか | 次 Issue | 厳格化の要否 |
| U-02 | CLI から `--var key=value` で変数を追加上書きする機能を追加するか | 次 Issue | ユーザー向け拡張 |
