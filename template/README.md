# template

## 1. 概要

`tooling/`のジェネレータが読み込むProfile(生成元となるテンプレート一式)を置くディレクトリです。CI(`.github/workflows/ci.yml`)は`small` `small-ddd` `small-python`の3 Profileを生成してスモークテストする想定です。現時点ではディレクトリ雛形のみで、内容は未着手です。

## 2. 責任

- 保持するもの: Profileごとのテンプレートファイル一式(今後追加)

## 3. 責任外

- 生成ロジック本体(`tooling/`が持ちます)
