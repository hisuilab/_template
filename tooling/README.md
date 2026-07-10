# tooling

## 1. 概要

新規プロジェクトを生成するジェネレータ本体を置くディレクトリです。CI(`.github/workflows/ci.yml`)は`python3 -m tooling.generator generate --name ... --profile ... --output ...`の形で呼び出す想定です。現時点ではディレクトリ雛形のみで、実装は未着手です。

## 2. 責任

- 保持するもの: `template/`のProfileを読み込み、指定した名前・言語でプロジェクト一式を出力するジェネレータ実装(今後追加)

## 3. 責任外

- Profileそのものの内容(`template/`が持ちます)
