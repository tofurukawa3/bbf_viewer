# BBF DataModel Viewer & Editor

Broadband Forumのデータモデル (TR-181, TR-196, TR-262) をブラウザ上で直感的に横断・検索し、CWMP (TR-069) ペイロードを生成するためのローカルWebアプリケーションです。

## プロジェクト構成

- [`backend/`](backend/README.md): Python (FastAPI) によるAPIサーバー。複雑なXMLデータモデルのパースとJSON構造への変換を担当。
- [`frontend/`](frontend/README.md): React (Vite) を用いたシングルページアプリケーション (SPA)。高度なツリー・テーブルビューやエディタを提供。
- [`translator/`](translator/README.md): 英語のXML定義から日本語へ翻訳するためのサブツール。
- [`e2e/`](e2e/README.md): Playwrightを使ったE2Eテスト環境。
- [`data/`](data/README.md): 解析対象となる各種XMLファイルなどの入力ソース類を配置。
- [`docs/`](docs/README.md): アプリケーションのアーキテクチャやドキュメント群。

## 主な機能と特徴

- **Viewモード / Editモードの分離**:
  - 【Viewモード】すべてのパラメータを安全に閲覧できます。
  - 【Editモード】TR-069における設定変更対象となる書き込み権限（`readWrite`）を持つパラメータのみを自動抽出してツリー表示します。
- **パラメータのリアルタイム検索**: ツリー内の膨大なパラメータ群から、部分一致で即座に目的の項目をフィルタリング可能です。
- **充実したパラメータ詳細表示**: 選択したパラメータの型、アクセス範囲、説明、XMLモデル상의デフォルト値などをテーブル形式で見やすく表示します。
- **高度なCWMPエディタ**:
  - 値を入力すると自動的にTR-069 CWMP標準の `SetParameterValues` 変更要求XML (W3C SOAP 1.1) が生成されます。
  - XML専用のシンタックスハイライト、構文エラーを検知できる「Lint (検証)」機能付き。
  - 視認性を極限まで高めるため、「BIZ UD Gothic (9pt)」フォントを採用し、画面ボトムまで拡張するモダンな2ペインレイアウトで構築しています。

詳細な操作方法や起動手順については、[docs/getting_started.md](docs/getting_started.md) をご参照ください。

## 開発環境のセットアップと起動

Windows環境では、提供されている起動スクリプトを利用して、BackendとFrontendをワンクリックで同時に立ち上げることができます。

```powershell
# 初回起動時は依存関係のインストール（uv, npm）が自動で実行されます
.\start.ps1 -Install

# 通常の起動
.\start.ps1
```

## E2Eテストの実行

アプリケーションが全体を通して正常に動作するか（フロントエンドの表示やバックエンドとの連携など）を確認するための、PlaywrightベースのE2Eテスト環境が用意されています。

```powershell
# E2Eテストの一括実行
# 自動的にサーバーを起動し、テスト完了後に終了します
.\test_e2e.ps1
```
