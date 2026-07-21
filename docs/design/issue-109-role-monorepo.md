---
status: implemented
proposed_at: 2026-07-21
approved_at: 2026-07-21
approved_by: PM
implemented_at: 2026-07-21
related: "#109"
---

# 設計提案: 複数役割(--role)によるモノレポ型フルスタック生成と意図ベースwizard

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

`docs/draft/project-direction.md`§7.3の目標設計(`--lang backend=python,frontend=typescript`)
を検討した結果、以下が判明しました。

1. 目標設計は「profileは1つのまま、langだけrole別」という前提だが、実際のフルスタック
   構成(例: Axum JSON API + React SPA)は用途(profile)自体もrole別になるのが自然
2. 「1つの`flake.nix`に複数言語のツールチェインを合成する」案(案A)は影響範囲とリスクが
   大きい(`/think:risks`でHigh 3件を検出)
3. **CLIの`--role`フラグだけを設計しても、`just new`(wizard)のUXが置き去りになる。**
   wizardは現状「単一言語を選ぶ」前提の3問(name/lang/profile)のみで、複数role対話も
   意図ベースの分岐も無い。CLIとwizardを別々に設計すると、後からwizard側の要求で
   CLI側の内部関数を作り直す手戻りが起きうるため、本Issueで両方を一体で設計する

さらに、wizardのUXについて「単一言語/複数言語」ではなく「**何を作りたいか(意図)**」を
起点に分岐すべきという指摘があり、この設計を採用します(Webアプリ/CLIツール/ライブラリ/
骨格のみ、という意図から必要なProfile・役割分割の要否を導く)。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `generate`サブコマンドへの`--role <name>:profile=<p>[,lang=<l>]`(繰り返し指定可)追加 | Database選択ステップ(`features/database-<lang>`が未実装のため。#98) |
| role毎に既存パイプラインを`{output}/{role名}/`へ実行する共有関数`_generate_roles` | ルート`justfile`の便利ラッパー(未解決事項) |
| `profile.toml`への`category`フィールド追加(`cli`/`web`/`library`) | ルート単位の`.template-manifest.toml`(未解決事項) |
| `create`ウィザードの意図ベース分岐(Webアプリ/CLIツール/ライブラリ/骨格のみ) |  |
| Webアプリ選択時のフロントエンド/バックエンド分離要否の質問、分離時のrole生成 |  |

## 3. 選択肢

| 案 | 内容 | 評価 |
| --- | --- | --- |
| B | モノレポ型サブ生成(role毎に既存パイプラインを独立実行)+意図ベースwizard | ← 採用 |
| A | 単一flake統合(当初案) | 見送り(1節参照) |
| C | CLIの`--role`のみ実装し、wizardは現状維持(将来別Issue) | 見送り。ユーザー指摘の通り、後からwizard要件でCLI内部関数の形が変わる手戻りリスクがある |

## 4. 設計案

### 4.1. `ProfileSchema`への`category`追加

```python
@dataclass(frozen=True)
class ProfileSchema:
    name: str
    summary: str
    category: str  # "cli" | "web" | "library"
    parts: tuple[str, ...]
    variables: Mapping[str, str]
```

既存4つの`profile.toml`へ`category`を追加します(必須フィールド、他フィールドと同じ厳密さ)。

| profile | category |
| --- | --- |
| `starter-cli` | `cli` |
| `starter-web-api` | `web` |
| `starter-web-htmx` | `web` |
| `starter-library` | `library` |

wizardは`category`でProfileを絞り込むため、新しいProfileを追加してもwizardの分岐コード
(if/else)を増やす必要がありません。

### 4.2. CLIの`--role`(再掲、変更なし)

```python
gen.add_argument("--profile", default=None, help="Profile ID（--role未使用時は必須）")
gen.add_argument(
    "--role",
    action="append",
    default=[],
    help="役割ごとのサブ生成（例: backend:profile=starter-web-api,lang=python）。複数指定可",
)
```

```python
@dataclass(frozen=True)
class RoleSpec:
    name: str
    profile: str
    lang: str | None


def _parse_role(role_str: str) -> tuple[str | None, str | None, str | None]:
    """Parse 'name:profile=<p>[,lang=<l>]' into (name, profile, lang)."""
    if ":" not in role_str:
        return None, None, None
    name, _, rest = role_str.partition(":")
    kv = dict(pair.split("=", 1) for pair in rest.split(",") if "=" in pair)
    return name, kv.get("profile"), kv.get("lang")
```

### 4.3. CLIとwizardが共有する生成コア関数

```python
def _generate_roles(name: str, output_root: Path, roles: list[RoleSpec]) -> int:
    """Generate one independent sub-project per role under output_root."""
    print(f"→ Generating {len(roles)} role(s) at {output_root}...")
    for role in roles:
        rc = _do_generate(name, role.profile, role.lang, output_root / role.name)
        if rc != 0:
            return rc
    _write_role_readme(output_root, roles)
    print(f"Generated {len(roles)} role(s) in {output_root}")
    return 0
```

**重要**: `_generate_roles`は`RoleSpec`のリストを直接受け取ります。CLI経由の場合は
`--role`文字列を`_parse_role`でパースしてから`RoleSpec`へ変換して渡し、wizard経由の
場合はwizardの質問結果から直接`RoleSpec`を組み立てて渡します。**wizardが`--role`文字列を
組み立てて再パースすることはありません**(ユーザー指摘を受けた設計上のポイント)。

`_cmd_generate`(CLI)は次のように分岐します。

```python
def _cmd_generate(args: argparse.Namespace) -> int:
    name_error = _validate_name(args.name)
    if name_error:
        print(name_error, file=sys.stderr)
        return 1

    if args.role and (args.profile or args.lang):
        print("error: --role cannot be combined with --profile/--lang", file=sys.stderr)
        return 1

    output = _resolve_output_path(args.name, args.output)

    if args.role:
        roles = []
        for role_str in args.role:
            role_name, profile, lang = _parse_role(role_str)
            if role_name is None or profile is None:
                print(
                    f"error: invalid --role format '{role_str}'. "
                    "Expected 'name:profile=<p>[,lang=<l>]'",
                    file=sys.stderr,
                )
                return 1
            if err := _validate_name(role_name):
                print(err, file=sys.stderr)
                return 1
            roles.append(RoleSpec(name=role_name, profile=profile, lang=lang))
        return _generate_roles(args.name, output, roles)

    if not args.profile:
        print("error: --profile is required unless --role is used", file=sys.stderr)
        return 1

    print(f"→ Generating at {output}...")
    return _do_generate(args.name, args.profile, args.lang, output)
```

### 4.4. wizardの意図ベース分岐

```python
@dataclass
class WizardAnswers:
    name: str
    profile: str | None = None
    lang: str | None = None
    roles: list[RoleSpec] = field(default_factory=list)
```

```text
1. プロジェクト名(既存のまま)
2. 「何を作りますか？」
   - CLIツール          → category="cli"
   - Webアプリ           → category="web"（4.5節で分岐）
   - ライブラリ          → category="library"
   - まず骨格だけ(後で決める) → --lang省略、Profileは全カテゴリから選択
3. (category="cli"/"library"の場合)
   - 該当categoryのProfileから選択(現状1つなら自動確定)
   - 言語選択(単一、既存と同じ質問)
```

CLIツール・ライブラリ・骨格のみの場合、質問数は**既存と同じ(実質3〜4問)**のままです。
複数言語を使うケースは稀だが後から`just inject`で追加できる、という案内をwizardの
完了メッセージに含めます(#91で確立済みの`inject`の仕組みをそのまま使う。新機能は不要)。

### 4.5. Webアプリ選択時の分岐

```text
3. 「フロントエンドとバックエンドを分けますか？」
   - いいえ(一体型。Next.js的な構成)
     → category="web"のProfileから選択(starter-web-api / starter-web-htmx)
     → 言語選択(単一)
     → 通常の単一lang生成（既存の_do_generateのみ、roleは使わない）
   - はい(分離)
     → 「backend」用のProfile選択(category="web") → 言語選択
     → 「frontend」用のProfile選択(category="web") → 言語選択
     → RoleSpec(name="backend", ...) / RoleSpec(name="frontend", ...) を組み立て
     → _generate_roles() を直接呼び出す
```

role名は`backend`/`frontend`に固定し、ユーザーには役割名自体を尋ねません(この分岐に
入った時点で意味が確定しているため)。3個以上の役割(例: `worker`)が必要なケースは
本Issueのwizardスコープ外とし、CLIの`--role`を直接使う上級者向け経路として残します。

### 4.6. Database選択ステップとの接続点(実装しない)

`features/database-<lang>`(#98)が実装された場合、wizard完了後に「データベースを
追加しますか？」という追加ステップを挿入できる設計にしておきます(具体的には、
`_generate_roles`/`_do_generate`実行後に`just inject features/database-<lang>`相当を
案内メッセージとして表示するだけで、wizardの構造自体を変更しません)。本Issueでは
`features/database-*`が存在しないため、この接続点の実装は行いません。

## 5. 失敗とロールバック

- 既存の`--profile`/`--lang`単体呼び出し(`--role`未使用)・既存wizardの単一lang経路は
  実質的に変更されません(`_do_generate`自体は無改修)
- `category`追加は既存4 profile全てに必須フィールドとして追加するため、
  `tests/fixtures/schema/valid_profile.toml`等の既存fixtureも更新が必要です(スキーマの
  破壊的変更、ただし本リポジトリ内で完結し外部ユーザーへの影響はありません)
- ロールバックは`git revert`で可能です

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/unit/test_schema.py` | `category`必須フィールドの検証(欠落時にSchemaError) |
| `tests/e2e/test_generate_profiles.py` | `--role`による2role生成、ルート`README.md`の内容 |
| `tests/unit/test_wizard.py` | 意図別分岐(CLI/ライブラリ/Web一体型/Web分離/骨格のみ)それぞれで正しい`WizardAnswers`が組み立てられること |
| 手動確認 | `just new`相当で実際に対話し、Web分離を選んだ場合に2つの独立した生成物ができ、それぞれ`just verify`がグリーンになること |
| `just verify`（このリポジトリ） | 全チェックpass |

## 7. 未解決事項

- **Database選択ステップ**: `features/database-<lang>`実装後に接続する(4.6節)
- **ルート`justfile`の便利ラッパー・ルート集約manifest**: 前回設計から継続する未解決事項
- **3役割以上のwizard対応(worker等)**: 本Issueのwizardスコープでは2役割(backend/frontend)
  固定。3役割以上が必要な場合はCLIの`--role`を直接使う運用とする
- **`docs/draft/project-direction.md`§7.3の更新**: 本Issue実装後、目標設計の記述を
  本設計(案B+意図ベースwizard)へ更新する必要があります
