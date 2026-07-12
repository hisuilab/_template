# {{project_name}}

## 1. 概要

プロジェクトの説明をここに書きます。

## 2. セットアップ

```sh
# 初回のみ: git 初期化と pre-commit フックのインストール
nix develop --command just init

# 開発シェルに入る
nix develop
```

## 3. 開発

```sh
# フォーマット・lint・テスト・ドキュメント検証を一括実行
just verify

# フォーマットのみ
just format

# ツールバージョン確認
just versions
```
