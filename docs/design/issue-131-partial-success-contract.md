---
status: approved
proposed_at: 2026-07-22
approved_at: 2026-07-22
approved_by: PM
implemented_at: 2026-07-22
related: "#131"
---

# 設計提案: 生成と inject の部分成功契約を明確化して復旧可能にする

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 失敗分類表](#2-失敗分類表)
- [3. 対象範囲](#3-対象範囲)
- [4. 設計案](#4-設計案)
  - [4.1. inject I/O失敗時のロールバック](#41-inject-io失敗時のロールバック)
  - [4.2. inject 全skip時のmanifest非記録](#42-inject-全skip時のmanifest非記録)
  - [4.3. manifest書き込み失敗の復旧案内](#43-manifest書き込み失敗の復旧案内)
  - [4.4. --role 部分成功時の継続と案内](#44---role-部分成功時の継続と案内)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

`generate` / `inject` / `--role` の成功・失敗・部分成功に関して 4 つのギャップがあります。

| # | ギャップ | 現在地 |
| --- | --- | --- |
| G-1 | `inject()` I/O失敗時に追加済みファイルをロールバックしない | `applier.py:44-54` |
| G-2 | `inject()` 全skip時でも manifest に Part を適用済みとして記録する | `cli.py:399` |
| G-3 | `apply()` / `inject()` 成功後に manifest 書き込みが失敗した場合、ファイルと manifest の整合が崩れる | `cli.py:149-152` / `cli.py:398-399` |
| G-4 | `--role` で最初に失敗した role で即 return し、成功・失敗 role の案内がない | `cli.py:209-213` |

## 2. 失敗分類表

| コマンド | フェーズ | 結果 | ユーザーへの影響 | 復旧方法 |
| --- | --- | --- | --- | --- |
| `generate` | plan/render失敗 | 出力なし | 再実行可 | そのまま再実行 |
| `generate` | apply失敗(ディレクトリ存在) | 出力なし | 再実行可 | 出力を削除して再実行 |
| `generate` | apply中I/O失敗 | 出力ディレクトリ削除済み | 再実行可 | `apply()` 自身がrollback済み |
| `generate` | manifest書き込み失敗 | ファイルあり・manifest なし | 部分状態 | G-3: エラーメッセージで案内 |
| `inject` | plan/render失敗 | target 変更なし | 再実行可 | そのまま再実行 |
| `inject` | I/O失敗(途中) | 一部ファイルが追加済み | **部分状態** | **G-1: rollback** |
| `inject` | 全skip | target 変更なし | manifest 記録済み → 再実行不能 | **G-2: 記録しない** |
| `inject` | manifest書き込み失敗 | ファイルあり・manifest未更新 | 部分状態 | G-3: エラーメッセージで案内 |
| `--role` | N番目role失敗 | 0〜N-1 role は生成済み | 部分状態 | **G-4: 継続+案内** |

## 3. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `tooling/generator/applier.py`(inject rollback 追加) | `generate` の apply rollback(既実装) |
| `tooling/generator/cli.py`(G-2・G-3・G-4 対応) | manifest のアトミック書き込み(別 Issue #130) |
| `tests/e2e/test_inject.py`(異常系テスト追加) | `inject` 部分成功後の undo log(別 Issue) |
| `docs/design/`(本ファイル・失敗分類表) | `generate` manifest 失敗の自動復旧 |

## 4. 設計案

### 4.1. inject I/O失敗時のロールバック

**`tooling/generator/applier.py` の `inject()` 内**

`files_added` を追跡し、OSError 時に削除します。

```python
def inject(staging_dir: Path, target_path: Path) -> InjectResult:
    files_added: list[str] = []
    files_skipped: list[str] = []
    try:
        for src in sorted(staging_dir.rglob("*")):
            if not src.is_file():
                continue
            rel = str(src.relative_to(staging_dir))
            dest = target_path / rel
            if dest.exists():
                files_skipped.append(rel)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            files_added.append(rel)
    except OSError as e:
        for rel in files_added:
            (target_path / rel).unlink(missing_ok=True)
        raise ApplyError(f"I/O error during inject: {e}") from e

    return InjectResult(
        target_path=target_path,
        files_added=tuple(files_added),
        files_skipped=tuple(files_skipped),
    )
```

`unlink(missing_ok=True)` はロールバック失敗を握りつぶさず、ロールバック途中の
2次エラーをユーザーに見せないため採用します。ロールバック中の OSError は無視し、
元の ApplyError を伝播させます。

### 4.2. inject 全skip時のmanifest非記録

**`tooling/generator/cli.py` の `_cmd_inject()` 内**

`inject()` が `files_added=()` を返した場合、manifest を更新せずに終了します。

```python
result = inject(staging, target)
if not result.files_added:
    print(
        f"Injected '{part_id}': all {len(result.files_skipped)} file(s) already existed. "
        "No changes made; manifest not updated. Re-run inject to retry.",
        file=sys.stderr,
    )
    return 0
update_manifest(target, part_id=part_id)
print(
    f"Injected '{part_id}': "
    f"{len(result.files_added)} added, {len(result.files_skipped)} skipped"
)
```

ステータス: exit 0（エラーではない）。

> [!NOTE]
> 全skip は「対象ファイルがすべて既存」を意味します。manifest 未記録のまま
> にすることで再実行が可能になり、ファイルの追加状況が変わった際に retry できます。

### 4.3. manifest書き込み失敗の復旧案内

**`tooling/generator/cli.py` の `_cmd_inject()` および `_do_generate()`**

`ManifestError` を他の例外と分けて catch し、復旧手順を案内します。

```python
# inject の場合
try:
    update_manifest(target, part_id=part_id)
except ManifestError as e:
    print(
        f"Warning: files were injected but manifest update failed: {e}\n"
        f"To recover, manually run: just inject {part_id}",
        file=sys.stderr,
    )
    return 2  # 部分成功を示す終了コード

# generate の場合
try:
    write_manifest(output, parts, project_name=name)
except ManifestError as e:
    print(
        f"Warning: files were generated but manifest creation failed: {e}\n"
        f"To recover: delete '{output}' and re-run generate.",
        file=sys.stderr,
    )
    return 2
```

終了コード 2 は「部分成功」を表します（0=成功、1=失敗、2=部分成功）。

### 4.4. --role 部分成功時の継続と案内

**`tooling/generator/cli.py` の `_generate_roles()`**

失敗 role を収集し、最後にまとめて報告します。

```python
def _generate_roles(name: str, output_root: Path, roles: list[RoleSpec]) -> int:
    readme_path = output_root / "README.md"
    if readme_path.exists():
        print(f"Error: output root README already exists: '{readme_path}'", file=sys.stderr)
        return 1

    print(f"→ Generating {len(roles)} role(s) at {output_root}...")
    failed: list[str] = []
    for role in roles:
        rc = _do_generate(name, role.profile, role.lang, output_root / role.name)
        if rc != 0:
            failed.append(role.name)

    if len(failed) == len(roles):
        return 1  # 全失敗はロールバック不要（各 role の apply が個別にロールバック済み）

    try:
        _write_role_readme(output_root, roles)
    except (ApplyError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if failed:
        print(
            f"Partial success: {len(roles) - len(failed)}/{len(roles)} role(s) generated.\n"
            f"Failed roles: {', '.join(failed)}\n"
            f"Re-run generate --role for each failed role to retry.",
            file=sys.stderr,
        )
        return 2
    print(f"Generated {len(roles)} role(s) in {output_root}")
    return 0
```

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| `inject()` rollback 中に 2 次 OSError | ロールバック不完全 | `unlink(missing_ok=True)` で無視し、元の ApplyError を伝播。ユーザーへの case はエラーメッセージに記載 |
| 全 skip を exit 0 に変えることで既存テストへの影響 | `test_inject_updates_manifest` が全 skip の場合にパスしなくなる可能性 | 全 skip シナリオは既存テストで発生しない（logging-python は新ファイルを追加する） |
| 終了コード 2 を既存スクリプトが 0/1 以外として扱う | 部分成功が失敗に見える可能性 | `just` のデフォルト挙動は非 0 を失敗として扱うため許容。ユーザードキュメントに記載 |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| 単体テスト(applier) | `inject()` I/O失敗時に追加済みファイルが削除されること |
| E2E テスト(inject) | 全skip時に exit 0 かつ manifest 未更新であること |
| E2E テスト(inject) | manifest 書き込み失敗時に exit 2 かつ復旧案内が出ること |
| E2E テスト(generate) | `--role` 部分成功時に失敗 role が報告され exit 2 になること |
| 回帰 | `just verify` 全パス |

## 7. 未解決事項

| ID | 論点 | 決定者 | ブロックする作業 |
| --- | --- | --- | --- |
| U-01 | inject 全skip exit 0 + 非記録: 「何もしなかった」として扱うのは正しいか | 本設計で採用 | G-2 実装 |
| U-02 | manifest アトミック書き込み(tmp ファイル → rename) で G-3 を根治するか | 次 Issue #130 | manifest v2 設計と合わせる |
| U-03 | `--role` 失敗 role を個別に再実行する `just retry-role` を追加するか | 次 Issue | CLI 拡張 |
