---
status: implemented
proposed_at: 2026-07-23
approved_at: 2026-07-23
approved_by: hisuilab
implemented_at: 2026-07-23
related: "#130"
---

# 設計提案: manifest v2 — write-set・テンプレート由来情報の記録とatomic更新

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

現行 manifest (schema_version = "1") は適用済み Part ID のみを記録します。次の情報が欠落しています。

- `write_set`: 生成時に書き込んだファイルの一覧
- `template_revision`: 生成時の template リポジトリの git SHA
- `generator_version`: generator ツールのバージョン
- `part_digest`: 各 Part 内容の SHA-256 ダイジェスト

この不足により、継続更新・差分監査・再適用・破損復旧の判断材料が得られません。

加えて `write_manifest()` / `update_manifest()` は手動文字列連結と追記を使っており、書き込みが非 atomic です。途中で失敗すると manifest が壊れたまま残る恐れがあります。`read_manifest()` の型・文字種・重複検証も薄く、壊れた manifest を読み込んだ際のエラーが不明確です。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `manifest.py`: write / update / read の刷新 | 既存 manifest (v1) の自動移行・migration CLI |
| `models.py`: `ManifestData` の拡張 | `--role` 部分成功の write-set (Issue #130 スコープ外) |
| `cli.py`: generate / inject での write-set 渡し | Go PoC との API 整合 |
| `tests/unit/test_generator.py`: manifest v2 テスト追加 | 既存 v1 ファイルの read 互換 (※後述) |
| `tests/e2e/test_generate_profiles.py` / `test_inject.py`: e2e 確認 | digest 検証コマンド (別 Issue へ) |

### schema_version 互換方針

- `schema_version = "1"` のファイルを `read_manifest()` で読んだ場合、`ManifestError` を上げて「再生成を促す」メッセージを出します。
- schema_version は `"2"` に上げます。後方互換読み取り(v1→v2 自動変換)はこの Issue のスコープ外とし、未解決事項に記載します。

## 3. 選択肢

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A: TOML 手書きを継続しつつ拡張 | 現行の文字列 join を拡張。atomic write を `tmp → rename` で追加。 | atomic write は追加できるが、フィールドごとに手書き文字列を増やす保守負債が残る |
| B (採用): `tomli_w` でシリアライズ | Python dict を組み立てて `tomli_w.dumps()` → atomic write。 | TOML 手書き不要。フォーマット一貫性が型で保証される。`tomli_w` は既存依存かを確認要 |
| C: JSON 形式に変更 | TOML をやめて JSON に。`json` は標準ライブラリ。 | 既存 TOML フォーマットとの互換が完全に切れる。ユーザーが手編集しにくくなる |

`tomli_w` は現在の Nix 環境・pyproject.toml に含まれておらず、新規依存追加は PM 承認が必要です。そのため案 A (atomic TOML 手書き) を採用します。`tomllib` (読み) + 手書き文字列 (書き) の組み合わせで実装します。

## 4. 設計案

### 4.1. manifest v2 フォーマット

```toml
[manifest]
schema_version = "2"
project_name   = "myapp"
generated_at   = "2026-07-23"
template_revision = "abc1234"   # git rev-parse HEAD of template repo at generation time; "" if unavailable
generator_version = "0.1.0"    # tooling.generator.__version__; "" if unavailable

[[applied]]
part_id      = "base"
applied_at   = "2026-07-23"
part_digest  = "sha256:abcdef…"  # SHA-256 of sorted payload file contents; "" if unavailable
files        = ["README.md", "flake.nix", ".gitignore"]

[[applied]]
part_id      = "starter/cli"
applied_at   = "2026-07-23"
part_digest  = "sha256:…"
files        = ["justfile", "src/main.py"]
```

- `template_revision`: `git -C <template_root> rev-parse HEAD` で取得。git が使えない場合は空文字。
- `generator_version`: `tooling.generator.__version__` 定数。最初は `"0.1.0"` を直書き。
- `part_digest`: Part 内 payload の全ファイルをソートし SHA-256 で連結したダイジェスト。取得できない場合は空文字。
- `files` (write_set): `GenerationResult.files_written` または `InjectResult.files_added` から取得。

### 4.2. 責任マップ

```text
cli.py (_do_generate)
  ├── applier.apply()          → GenerationResult.files_written
  └── manifest.write_manifest(
          project_path, parts, project_name,
          files_by_part,        # dict[part_id, list[str]]
          template_revision,    # str
          generator_version,    # str
      )

cli.py (_cmd_inject)
  ├── applier.inject()         → InjectResult.files_added
  └── manifest.update_manifest(
          project_path, part_id,
          files,                # list[str]
          part_digest,          # str
      )
```

### 4.3. atomic write の実装

```python
def _atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)   # POSIX: atomic rename; Windows: best-effort
```

`write_manifest()` も `update_manifest()` もこの関数を経由します。`update_manifest()` は現在の TOML を `tomllib` で読んで `dict` に変換し、`[[applied]]` エントリを追加して再シリアライズします。

### 4.4. models.py の変更

`ManifestData` に `write_set` と `template_revision`・`generator_version` を追加します。

```python
@dataclass(frozen=True)
class ManifestData:
    project_name: str
    applied_part_ids: tuple[str, ...]
    # v2 additions
    template_revision: str = ""
    generator_version: str = ""
    applied_entries: tuple[ManifestEntry, ...] = ()

@dataclass(frozen=True)
class ManifestEntry:
    part_id: str
    applied_at: str
    part_digest: str = ""
    files: tuple[str, ...] = ()
```

既存の `applied_part_ids` は後方互換のため維持し、`applied_entries` から派生させます。

### 4.5. シリアライズ方針

新規依存の追加はしません。TOML を手書きしますが、フィールドはすべて二重引用符で囲み、`_validate_part_id_for_toml()` で事前に検証します。`files` リストは TOML インライン配列 (`["a.py", "b.txt"]`) で出力します。

### 4.6. read_manifest() の強化

- `schema_version != "2"` の場合: `ManifestError` を上げ再生成を促します。
- `[[applied]]` エントリの重複 `part_id`: `ManifestError` を上げます。
- `part_id` の文字種: 既存の `_validate_part_id_for_toml()` を使います。
- `files` が list[str] でない場合: `ManifestError` を上げます。

## 5. 失敗とロールバック

| フェーズ | 失敗 | 挙動 |
| --- | --- | --- |
| `write_manifest()` の `.tmp` 書き込み | OSError | `.tmp` が残る可能性あり。呼び出し元 (cli.py) が出力ディレクトリを削除するよう案内する |
| `.tmp.replace(path)` | OSError | manifest 不完全。再実行で上書き可能なため自己修復 |
| `update_manifest()` の再読み込み | ManifestError | 呼び出し元が警告を出力し rc=2 で返す (既存の契約を維持) |
| `inject()` I/O エラー | ApplyError + rollback | `applier.inject()` が追加済みファイルを削除 (Issue #145 で実装済み) |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| unit: `TestManifest` | v2 フォーマットの write/read ラウンドトリップ |
| unit | `template_revision` / `generator_version` / `part_digest` / `files` の write/read |
| unit | `schema_version = "1"` ファイルを読んで ManifestError |
| unit | 重複 part_id の ManifestError |
| unit | `files` が不正型の ManifestError |
| unit | `update_manifest()` が atomic write で既存エントリを保持する |
| unit | `update_manifest()` 後に `files` と `part_digest` が追記される |
| e2e: `test_generate_profiles.py` | generate 後の manifest に `files` が存在し空でない |
| e2e: `test_inject.py` | inject 後の manifest に新 Part の `files` が追記される |

## 7. 未解決事項

| 事項 | 決定者 | ブロック |
| --- | --- | --- |
| `tomli_w` の依存追加可否 | 確認済み: 未導入のため手書き TOML で実装する | 解決済み |
| v1 → v2 自動移行 CLI | 別 Issue | 既存生成プロジェクトの upgrade フロー |
| `template_revision` の取得元 (git コマンド vs 環境変数) | Programmer | 実装時に `git -C` 呼び出しを試みて失敗したら空文字とする |
| `--role` 生成時の per-role write-set 記録 | 別 Issue | 各ロールが独立 manifest を持つため追加設計が必要 |
