---
status: implemented
proposed_at: 2026-07-20
approved_at: 2026-07-20
approved_by: PM
implemented_at: 2026-07-20
related: "#91"
---

# 設計提案: lang未定時にsrc骨格を生成しないstarter構造に分離する

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

`starter/cli`・`starter/web-api`・`starter/library`は`--lang`の値によらずPythonソース
(`src/main.py`等)を無条件で同梱しています。`--lang`は必須ではなく(`tooling/generator/cli.py`
の`default=None`)、`starter-*`Profileも`lang/*`に依存しないため、言語・技術スタックが未確定な
段階でプロジェクトを開始したい場合でも常にPythonコードが混入します。これは`base`の
`.gitignore`からPython専用エントリを完全に除去できない直接の原因でもあります(#89は
この歪みを前提に暫定対応)。

`_template`自身がPythonで実装されていることと、生成される成果物に何のsrcを含めるかは無関係
です。現状Pythonが混入するのは`starter/*`の実装がPython専用になっているためであり、これを
解消します。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `starter/cli`・`starter/web-api`・`starter/library`を「lang非依存の骨格」と「Python実装」に分割 | TypeScript/Rust/Go向けのstarter実装の追加(本Issueは分割の枠組みのみ。各言語の中身は別Issueで積む) |
| `tooling/generator/cli.py`への「starter×lang複合Part」注入ロジック追加 | `template/schema/part_schema.py`の`LAYERS`変更(既存`"starter"`のまま流用するため不要) |
| e2eテスト・`docs/architecture/core.md`の更新 | 複数lang同時指定時のstarter合成(U-06、フェーズ5) |

## 3. 選択肢

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | `starter/<name>`を骨格のみ(README等)にし、Python実装を`starter/<name>-python`という複合Partへ分離。CLIが選択された`lang`に応じて`<starter-id>-<lang>`が存在すれば追加注入する(`lang/<x>`注入と同じパターンの拡張) | ← 推奨。既存の注入パターンを再利用し、`part_schema.py`・`LAYERS`・`resolver.py`の変更が不要。命名規約(`<starter>-<lang>`)だけで表現できる |
| B | `part.toml`に`lang`フィールドを新設し、ジェネレータが「同じPurposeでlangが一致するPartを選ぶ」解決ロジックを実装する | 見送り。新しい選択ロジック(現状の単純なID指定+requires/conflictsから逸脱)をジェネレータに追加することになり、既存の3段階(Load→Resolve→Plan)の設計より複雑化する。単一lang専用の`role=None`運用のM5範囲を超える投資 |
| C | 何もしない(現状維持) | 見送り。#89で暫定対応した歪みの根本原因が残り続ける |

案Aを採用します。

## 4. 設計案

### 4.1. Part構成の変更

```text
template/parts/starter/cli/                 # 骨格のみ(lang非依存)
├── part.toml                                # 変更なし(id="starter/cli", requires=["base"])
└── payload/
    └── src/README.md                        # 維持

template/parts/starter/cli-python/           # 新規: Python実装
├── part.toml                                # id="starter/cli-python", requires=["base", "starter/cli", "lang/python"]
└── payload/
    └── src/main.py                          # starter/cli から移動

template/parts/starter/web-api/              # 骨格のみ
└── payload/
    ├── src/README.md
    └── src/routes/README.md

template/parts/starter/web-api-python/       # 新規: Python実装
└── payload/
    └── src/app.py                           # starter/web-api から移動

template/parts/starter/library/              # 骨格のみ
└── payload/
    ├── src/README.md
    ├── src/{{project_name}}/README.md
    └── CHANGELOG.md

template/parts/starter/library-python/       # 新規: Python実装
└── payload/
    └── src/{{project_name}}/__init__.py     # starter/library から移動
```

複合Partの`part.toml`例(`starter/cli-python`):

```toml
[part]
id = "starter/cli-python"
layer = "starter"
summary = "starter/cli の Python 実装（src/main.py）"
requires = ["base", "starter/cli", "lang/python"]
conflicts = []

[placeholders]
required = ["project_name"]
```

`layer`は既存の`"starter"`をそのまま使います。`part_schema.py`の`LAYERS`変更は不要です。

### 4.2. `cli.py`への複合Part注入ロジック追加

`_do_generate`内、既存の`lang/<x>`注入直後に追加します。

```python
def _starter_lang_parts(profile_parts: tuple[str, ...], lang: str, template_root: Path) -> tuple[str, ...]:
    """Return companion '<starter-id>-<lang>' part ids that exist on disk."""
    candidates = []
    for part_id in profile_parts:
        if part_id.startswith("starter/"):
            candidate = f"{part_id}-{lang}"
            if (template_root / "parts" / candidate / "part.toml").exists():
                candidates.append(candidate)
    return tuple(candidates)
```

```python
extra_parts = (f"lang/{lang_spec.lang}",) if lang_spec else ()
if lang_spec:
    extra_parts += _starter_lang_parts(loaded_profile.parts, lang_spec.lang, _TEMPLATE_ROOT)
```

`part_id.startswith("starter/")`という文字列規約での判定は、`_available_langs`が
`template/parts/lang/`のディレクトリ一覧を規約で走査しているのと同じ軽量な手法です。
`.layer`フィールドを見るにはPartを個別ロードする必要があり、二重ロードのコストに対して
恩恵が小さいため見送ります。

### 4.3. 生成結果の変化

| `--lang` | `--profile starter-cli`のsrc/ | 備考 |
| --- | --- | --- |
| 省略 | `src/README.md`のみ | 本Issueの主目的。lang未定でも骨格だけ生成できる |
| `python` | `src/README.md` + `src/main.py` | 現状と同じ(回帰なし) |
| `typescript` / `rust` (#86マージ後) | `src/README.md`のみ | **挙動変更**: 現状はPythonの`main.py`が混入するが、対応する`starter/cli-typescript`等が存在しないため何も注入されなくなる。TypeScriptプロジェクトにPythonコードが紛れ込む既存の不整合(M5以来の既知のギャップ)が解消される |

### 4.4. `docs/architecture/core.md`の更新

§2「現行実装」の表を、骨格Partと複合Partの分離を反映する形に更新します。

### 4.5. 後からのlang確定(`inject`との組み合わせ)

`--lang`省略で骨格のみ生成したプロジェクトでも、既存の`inject`サブコマンド(#59)を使えば
技術選定確定後に後追いでlangを確定できます。`inject`は`part.requires`を
`manifest.applied_part_ids`と照合してから適用するため、新しい仕組みを追加しなくても
次の2段階適用がそのまま成立します。

```sh
just inject lang/python          # devShell を追加(requires=["base"]を満たす)
just inject starter/cli-python   # src/main.py を追加(requires=["base","starter/cli","lang/python"]を満たす)
```

1コマンド目を先に実行しないと2コマンド目は`missing`エラーで拒否されるため、順序はrequiresが
自然に強制します。

## 5. 失敗とロールバック

- `starter/cli`等のIDはProfile側で変更不要(骨格Partが同じIDを維持するため、
  `template/profiles/*.toml`は無改修)
- `--lang python`指定時の生成結果は現状と同一(既存e2eテストで回帰検出)
- `--lang typescript`/`rust`指定時はsrc内容が変化する(4.3節)が、既存テストはこれらの
  langで`src/`の内容を検証していないため、既存テストの失敗は発生しない
- ロールバックは`git revert`で可能

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/e2e/test_generate_profiles.py` | `--lang`省略時に3プロファイルいずれも`src/`配下にPythonコードが無いこと／`--lang python`指定時は現状と同じPython骨格が生成されること(既存テストの回帰確認) |
| `tests/unit/test_schema.py` | 複合Partの`part.toml`がスキーマ検証を通ること(変更不要、既存の動的globで対象に入る) |
| `just verify`（このリポジトリ） | 全チェックpass |

## 7. 未解決事項

- **TypeScript/Rust/Go向けstarter実装**: 本Issueは分割の枠組みのみ提供します。
  `starter/cli-typescript`等の中身は、それぞれの言語のpurpose Part追加時(#87・#88関連、
  および将来のTypeScript対応)に個別Issueとして積みます
- **`--lang typescript`/`rust`のsrc内容変更**: 4.3節の通り、既存の「Pythonが紛れ込む」
  状態から「何も無い」状態に変わります。これは意図した改善ですが、利用者から見ると
  `--lang typescript`で生成したプロジェクトに`src/`の中身が無くなる体験の変化があるため、
  ルートREADME等で明示するかは`/build:docs`フェーズで判断します
- **U-06との関係**: 複数lang同時指定時の複合Part解決は、flake.nixの`append`戦略と同じ
  タイミング（フェーズ5）でまとめて設計します
