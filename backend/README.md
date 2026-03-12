# Backend

Python (FastAPI) によるAPIサーバーです。BBF (Broadband Forum) が策定するYANGモデルおよびCWMP XMLデータモデルを受け取り、フロントエンドが利用しやすいJSONツリー構造に変換して提供します。

## 主な機能

- **Tree API**: 木構造化されたパラメータ階層の返却
- **Search API**: パラメータ名やパス名によるフィルタリングと検索
- **XML Generation**: フロントエンドからのリクエストに基づく、CWMP標準準拠の `SetParameterValues` のSOAPペイロードの生成

## 開発環境

- Python 3.12+
- FastAPI
- ruff (Linter & Formatter)

## 起動

プロジェクトルートの `start.ps1` を実行するか、`uv` 等のパッケージマネージャを利用して直接起動します。
