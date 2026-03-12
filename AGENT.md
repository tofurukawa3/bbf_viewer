# AGENT.md

## 1. 本プロジェクトの目標

本プロジェクトの目的は、Broadband Forumのデータモデル(TR-069)を解析し、Python(バックエンド)とReact(フロントエンド)を用いてローカル環境上で動作するViewerおよびEditorアプリケーションを開発することです。

## 2. 対象データモデル

本アプリケーションは、TR-069プロトコルに関連する以下の公式YANGモデルを対象とします。

- BroadbandForumの標準YANGモジュール（`bbf-*.yang` 群）
- GitHubから取得したレポジトリ(`https://github.com/BroadbandForum/yang`)に含まれる標準定義ファイル群

## 3. アプリケーション機能詳細 (Viewer / Editor)

本アプリケーションは、目的別に「Viewモード」と「Editモード」の2つのタブ構成を持ちます。

- **Viewモード**: データモデルの全パラメータを安全に閲覧・検索するためのモードです。
- **Editモード**: TR-069における設定変更を想定したモードです。書き込み権限（`readWrite`）を持つパラメータとその親オブジェクトのみがツリーに表示されます。

**主要機能一覧**:

- **リアルタイム検索・フィルタリング**: パラメータ名やパスの部分一致検索が可能です。
- **直感的なツリー表示**: 最上位の冗長な `Root` ノードをスキップし、`Device.` や `FAP.` から始まるスッキリとした階層表示を実現しています。
- **詳細情報のテーブル表示(Editモード)**: 右ペインにパラメータの型(Type)、アクセス権(Access)、説明(Description)、およびXMLモデル定義の **デフォルト値(Default Value)** を見やすい罫線付きの表形式で表示します。
- **CWMP SetParameterValues 生成機能**: Editモードにてパラメータの新しい値を入力すると、画面右側の広大な専用パネルにTR-069 CWMP標準の変更要求XML (W3C SOAP 1.1) がリアルタイム生成されます。
  - **標準準拠 (CWMP / SOAP)**: 生成されるXMLペイロードは、W3Cが策定したSOAP 1.1仕様およびBroadband Forum (BBF) が策定したTR-069 CWMP仕様に完全準拠する形で出力されます。
  - **標準準拠 (データモデル / TR-106)**: Broadband ForumのTR-106 (Data Model Template for CWMP and USP data models) に基づき、グローバルな `<dataType>` や `<default>` などの制約情報も正しくパースして画面に反映します。
  - **シンタックスハイライト**: 生成されたXMLのタグや値が自動で色付けされます。
  - **高度なエディタレイアウト**: エディタ画面は下端まで最大限に広がり、フォントは視認性に優れた **BIZ UD Gothic (9pt)** が適用されています。
  - **XML Lint (構文チェック)**: 生成されたXML、または手動編集したXMLをボタン一つで構文チェックできます。

## 4. アーキテクチャ構成

本アプリケーションは、モダンな技術スタックを採用しています。

- **Backend (Python / FastAPI)**:
  - Broadband Forumの定義ファイル (YANGなど) をパースし、フロントエンドが利用しやすいJSON形式へ変換。
  - フロントエンドからの要求に応じて、ツリー構造データやCWMP SetParameterValuesのSOAPペイロードを返却するWeb APIサーバー。
- **Frontend (JavaScript / React / Vite)**:
  - バックエンドから取得したデータモデルをツリー形式で可視化するSPA (Single Page Application)。
  - ペイン分割レイアウトやシンタックスハイライト機能を備えた高度なCWMPエディタ機能を提供。

## 5. 基本ディレクトリ構成方針

保守性を考慮し、機能ごとにディレクトリを分割しています。

- `backend/`: PythonによるAPIサーバーおよびYANGパース処理ロジック
- `frontend/`: ReactによるUIコンポーネントおよびスタイル定義
- `data/bbf_yang/`: Broadband Forumの公式YANG定義ファイル群リポジトリ
- `data/cwmp-data-models/`: TR-069に特化したCWMP XMLデータモデル（TR-181等）
- `e2e/`: **[サブプロジェクト]** Playwrightを用いたEnd-to-Endの自動テスト環境
- `docs/`: ユーザーマニュアルおよび開発用ドキュメント
- `translator/`: **[サブプロジェクト]** BBFデータモデル（CWMP XML）の `<description>` 項目の英語文書を日本語に一括翻訳・キャッシュ化するためのPythonスクリプトおよび関連ファイル群
