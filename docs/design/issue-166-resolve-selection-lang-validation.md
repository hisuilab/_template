---
status: implemented
proposed_at: 2026-07-23
approved_at: 2026-07-23
approved_by: hisuilab
implemented_at: 2026-07-23
related: "#166, #132"
---

# 設計提案: resolve_selection に lang バリデーションを追加する

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 設計案](#3-設計案)
  - [3.1. 変更箇所](#31-変更箇所)
  - [3.2. エラー伝播](#32-エラー伝播)
- [4. 失敗とロールバック](#4-失敗とロールバック)
- [5. 検証](#5-検証)
- [6. 未解決事項](#6-未解決事項)

## 1. 問題

`services.resolve_selection` は `lang` が `None` 以外の場合、`validate_lang` を呼ばずに
`LangSpec` を構築し、`lang/cobol` のような存在しない Part を `extra_parts` に追加します。

その結果、`_cmd_generate`(非role経路)で `--lang cobol` を渡すと、フレンドリーなエラーメッセージ
`error: unknown lang 'cobol'. Available: python, typescript, rust, go` の代わりに、
`load_profile` 後のファイルロード時に `LoadError: part 'lang/cobol' not found (looked at ...)` が
発生します。

- `_cmd_create` と `--role` 経路は、`_do_generate` 呼び出し前に `_validate_lang` を呼ぶため
  影響を受けません。
- 非role `generate` 経路 (`_cmd_generate` → `_do_generate`) のみが影響を受けます。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `services.resolve_selection` 内の lang バリデーション追加 | `_cmd_create` / `--role` 経路(既に正しい) |
| 新テスト: `resolve_selection` へ無効 lang を渡すと `LoadError` になること | wizard UI ロジック |
| 新テスト: `generate` CLI で `--lang cobol` が友好的エラーを返すこと | manifest / workspace / inject コマンド |

## 3. 設計案

### 3.1. 変更箇所

**`tooling/generator/services.py` — `resolve_selection` 関数**

`lang is not None` の分岐内、`LangSpec` 構築前に以下を挿入します。

```python
if lang is not None:
    available = _available_langs_from_root(template_root)
    _spec, err = validate_lang(lang, available)
    if err:
        raise LoadError(err)
    lang_spec = LangSpec(lang=lang, role=None)
    ...
```

`_available_langs_from_root` は `cli.py` の `_available_langs` と同等のロジックを
`services.py` 内部ヘルパーとして実装します(依存方向: services→cli の逆依存を避けるため)。

```python
def _available_langs_from_root(template_root: Path) -> list[str]:
    lang_dir = template_root / "parts" / "lang"
    if not lang_dir.exists():
        return []
    return sorted(p.name for p in lang_dir.iterdir() if p.is_dir())
```

`LoadError` は既にインポート済みで、呼び出し元 (`_do_generate`) が `except LoadError` で
捕捉してエラー出力と終了コード 1 を返すため、エラー伝播に追加変更は不要です。

### 3.2. エラー伝播

```text
resolve_selection("starter-cli", "cobol", template_root)
  → validate_lang("cobol", ["go", "python", "rust", "typescript"])
  → (None, "error: unknown lang 'cobol'. Available: go, python, rust, typescript")
  → raise LoadError("error: unknown lang 'cobol'. Available: go, python, rust, typescript")
  ← _do_generate: except LoadError → print(f"Error: {e}") → return 1
```

## 4. 失敗とロールバック

変更は `services.py` の1関数に閉じています。`LoadError` は既存の例外型であり、
新しい依存や例外型の追加はありません。ロールバックはコミット単位で行えます。

## 5. 検証

| 検証 | 方法 |
| --- | --- |
| `resolve_selection` が無効な lang で `LoadError` を raise すること | 単体テスト追加 |
| `generate --lang cobol` が終了コード 1 かつエラーメッセージに 'cobol' を含むこと | 既存 `test_generate_unknown_lang_is_rejected` がカバー |
| `_cmd_create` / `--role` 経路が影響を受けないこと | 既存テストが継続してパスすること |
| linter / formatter | ruff check / ruff format |

## 6. 未解決事項

なし。
