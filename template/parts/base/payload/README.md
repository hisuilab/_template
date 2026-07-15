# {{project_name}}

## 1. 概要

プロジェクトの説明をここに書きます。

## 2. セットアップ

### Nix 環境（macOS / Linux）

```sh
# 初回のみ: git 初期化
nix develop --command just init

# 開発シェルに入る
nix develop
```

### devcontainer（Windows / Nix 未経験者）

Docker と VS Code がインストールされていれば Nix 不要で開発できます。

1. VS Code でリポジトリを開く
2. コマンドパレット →「Reopen in Container」
3. コンテナ起動後、ターミナルで `nix develop` に入ると git フックが自動インストールされます

```sh
nix develop          # devShell に入る（初回は nix store のダウンロードに数分かかります）
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
