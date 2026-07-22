---
status: approved
proposed_at: 2026-07-22
approved_at: 2026-07-22
approved_by: PM
implemented_at: null
related: "#128"
---

# 設計提案: テンプレート定義の ID と生成先パスを正規化して検証する

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
  - [4.1. Part ID バリデーション](#41-part-id-バリデーション)
  - [4.2. `[[files]].path` バリデーション](#42-filespath-バリデーション)
  - [4.3. Profile の Part 参照 ID バリデーション](#43-profile-の-part-参照-id-バリデーション)
  - [4.4. ID/ディレクトリ整合チェック](#44-idディレクトリ整合チェック)
  - [4.5. CI 不変条件テスト](#45-ci-不変条件テスト)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

テンプレート定義の安全な内部モデルへの閉じ込めに 4 つのギャップがあります。

| # | ギャップ | 影響 |
| --- | --- | --- |
| G-1 | `loader.py:load_part()` が `data["part"]["id"] != part_id`(ディレクトリ名)を検出しない | 異なる ID を持つ TOML を置いてもエラーなく読まれる |
| G-2 | `part_schema.py` で Part ID / `[[files]].path` の `..`・絶対パス・空文字を拒否しない | パス traversal 攻撃が planner へ到達する |
| G-3 | `profile_schema.py` で Part 参照 ID(文字列リスト)をフォーマット検証しない | プロファイルが `..` や不正 ID を参照できる |
| G-4 | 重複 Part ID / `[[files]].path` 対 payload の不整合を検出する CI 不変条件がない | typo したファイルルールが未使用のまま通る |

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `template/schema/part_schema.py`(ID・path フォーマット検証追加) | `tooling/generator/planner.py`(変換ロジック変更なし) |
| `template/schema/profile_schema.py`(Part 参照 ID フォーマット検証追加) | `[[files]].path` と変数展開後パスの照合(ランタイム、別 Issue) |
| `tooling/generator/loader.py`(ID/dir 整合チェック追加) | `docs/architecture/core.md`(記述は現状で正確) |
| `tests/unit/test_schema.py`(フォーマット違反テスト追加) | `profile_schema.py` の Part ID 存在確認(ロード時チェック済み) |
| `tests/unit/test_payload.py`(重複 ID・files.path 対 payload テスト追加) |  |

## 3. 選択肢

| # | バリデーション位置 | 評価 |
| --- | --- | --- |
| A | フォーマットを `part_schema.py` / `profile_schema.py` で、整合を `loader.py` で検証 | 責務が明確。schema は TOML 構造のみ、loader はファイルシステム整合のみ担当。採用案 |
| B | すべてを `loader.py` で検証 | schema 単体テストでパス traversal を検出できない |
| C | バリデーションなし、テストのみ | 実 TOML ファイルがないテスト環境で素通りする |

採用案は A です。

## 4. 設計案

### 4.1. Part ID バリデーション

**`template/schema/part_schema.py`**

```python
import re

_VALID_ID_RE = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9_-]*(/[a-zA-Z0-9][a-zA-Z0-9_-]*)*$"
)
```

既存 ID の例: `base`、`scale/large`、`features/logging-typescript`、`lang/go`、
`starter/web-api-go`。

`validate_part()` 内で `require_str(part, "id")` 取得直後に追加します。

```python
part_id = require_str(part, "id", source=source, table_name="part")
if not _VALID_ID_RE.match(part_id):
    raise SchemaError(
        f"part.id must match {_VALID_ID_RE.pattern!r}, got {part_id!r}",
        source=source,
        field="part.id",
    )
```

これにより `..`・`/absolute`・空文字・`../../etc/passwd` 形式をすべて拒否します。

### 4.2. `[[files]].path` バリデーション

`[[files]].path` は生成先 dest パスです。`.gitignore`(先頭ドット許容)や
`docs/_templates/draft.md`(ネスト)を含むため、正規表現より
「禁止条件リスト」で検証します。

**`template/schema/part_schema.py` の `_validate_file_rule()` 内**

```python
def _validate_path_safe(path: str, *, source: str, field: str) -> None:
    if not path:
        raise SchemaError("path must not be empty", source=source, field=field)
    if path.startswith("/"):
        raise SchemaError(
            f"path must be relative, got {path!r}", source=source, field=field
        )
    if any(seg == ".." for seg in path.replace("\\", "/").split("/")):
        raise SchemaError(
            f"path must not contain '..', got {path!r}", source=source, field=field
        )
```

`require_str(entry, "path")` 取得直後に `_validate_path_safe(path, ...)` を呼びます。

### 4.3. Profile の Part 参照 ID バリデーション

**`template/schema/profile_schema.py`**

`part_schema` の `_VALID_ID_RE` を `profile_schema` 側でも import して使用します。

```python
from template.schema.part_schema import _VALID_ID_RE as _PART_ID_RE
```

`raw_parts` を `tuple` に変換する前に各要素を検証します。

```python
for item in raw_parts:
    if not _PART_ID_RE.match(item):
        raise SchemaError(
            f"profile.parts contains invalid part id {item!r} "
            f"(must match {_PART_ID_RE.pattern!r})",
            source=source,
            field="profile.parts",
        )
```

### 4.4. ID/ディレクトリ整合チェック

**`tooling/generator/loader.py` の `load_part()` 末尾**

```python
schema = validate_part(data, source=str(path))
if schema.id != part_id:
    raise LoadError(
        f"part.toml declares id={schema.id!r} but is located in directory "
        f"{part_id!r} (they must match)"
    )
return schema
```

`load_parts_for_profile()` も同様に追加します。

### 4.5. CI 不変条件テスト

**`tests/unit/test_payload.py` — 追加テスト 2 本**

```python
def test_no_duplicate_part_ids() -> None:
    """template/parts/ 配下に重複 Part ID がないことを確認します。"""
    ids = [part_id for part_id, _ in PARTS]
    duplicates = [id for id in set(ids) if ids.count(id) > 1]
    assert not duplicates, f"Duplicate part IDs detected: {sorted(duplicates)}"


@pytest.mark.parametrize("part_id,part_dir", PARTS, ids=[p[0] for p in PARTS])
def test_files_rules_match_payload_paths(part_id: str, part_dir: Path) -> None:
    """[[files]].path がすべて実 payload ファイルの変換後パスと対応することを確認します。

    変数置換は行わず dot- プレフィックスのみ変換します。
    """
    part_toml = part_dir / "part.toml"
    with part_toml.open("rb") as f:
        data = tomllib.load(f)
    rules = data.get("files", [])
    if not rules:
        return

    payload_dir = part_dir / "payload"
    dest_paths: set[str] = set()
    if payload_dir.is_dir():
        for path in payload_dir.rglob("*"):
            if not path.is_file():
                continue
            rel = str(path.relative_to(payload_dir)).replace("\\", "/")
            dest = "/".join(
                seg[len("dot-"):].lstrip() and ("." + seg[len("dot-"):])
                if seg.startswith("dot-") else seg
                for seg in rel.split("/")
            )
            dest_paths.add(dest)

    orphan = [r["path"] for r in rules if r.get("path") not in dest_paths]
    assert not orphan, (
        f"part '{part_id}': [[files]].path entries not found in payload: {orphan}\n"
        f"Available payload paths: {sorted(dest_paths)}"
    )
```

> [!NOTE]
> `test_files_rules_match_payload_paths` の `dot-` 変換ロジックは `planner._strip_dot_prefix`
> と意図的に二重実装します。planner の内部関数を直接 import せず、テストが実装の変更から
> 独立するためです。

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| 既存 part.toml の ID が `_VALID_ID_RE` に不一致 | `just verify` が失敗 | `test_all_part_tomls_validate` がガード済みなので実 TOML 修正で対応 |
| `loader.py` の整合チェックが `load_parts_for_profile` で二重適用 | `LoadError` が 2 系統から出る | `load_part` 側で統一し `load_parts_for_profile` の inline logic を `load_part` 呼び出しへ委譲 |
| payload に `dot-` 以外の特殊変換規則が増えた場合 | `test_files_rules_match_payload_paths` が誤検知 | planner の変換規則と揃えて更新する |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| 単体テスト(schema) | `..`・絶対パス・空文字の Part ID および `[[files]].path` が SchemaError になること |
| 単体テスト(schema) | Profile の Part 参照 ID フォーマット違反が SchemaError になること |
| 単体テスト(loader) | ID/dir 不一致が LoadError になること |
| 統合テスト(payload) | 重複 Part ID がないこと |
| 統合テスト(payload) | `[[files]].path` が payload に対応すること |
| 回帰 | `just verify` 全パス(既存テスト群への回帰なし) |

## 7. 未解決事項

| ID | 論点 | 決定者 | ブロックする作業 |
| --- | --- | --- | --- |
| U-01 | `[[files]].path` と変数展開後 dest パスのランタイム整合チェックが必要か | 次 Issue | 生成時の詳細バリデーション |
| U-02 | `load_parts_for_profile` の inline TOML 読み込みを `load_part` 呼び出しへ統一するか | 本 Issue で同時対応可 | `loader.py` の整合チェック追加 |
| U-03 | `_VALID_ID_RE` を `part_schema` から `profile_schema` へ import することが公開 API として適切か | 本設計で暫定採用 | モジュール分割の要否 |
