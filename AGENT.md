# AGENT.md

## 1. 本プロジェクトの目標

本プロジェクトは、Broadband ForumのDataModelについて、PythonとJavaScriptを用いた構成で、ローカル環境上にViewerとして表示させるアプリを開発することを目的とします。

## 2. 対象データモデル

対象となるデータモデルは、TR-069プロトコルに関連する以下の最新版DataModelとします。

- **FAP** (Femto Access Point Service Data Model)
- **Femto** (FAPService)
- **Transport** (Routing/Transport)

## 3. ViewerおよびEditor機能について

本アプリケーションは、**Viewモード**と**Editモード**の2つのタブ構成を持ちます。

- **Viewモード**: データモデルの全パラメータを安全に閲覧するためのモードです。
- **Editモード**: TR-069のEditメッセージに関して **NETCONF** を利用する場合を想定し、データの編集および生成を行うことができるモードです。対象ツリーには、Write権限（`readWrite`）を持つパラメータやその親オブジェクトのみがフィルタリング表示されます。

**共通機能**:

- パラメータの部分一致検索（リアルタイムフィルタリング）
- 最終的に出力されるXML (`<edit-config>`) は、画面右側のテキストエリアに表示され、**シンタックスハイライト（着色）** と **Lint（構文チェック）** をサポートします。また、エディタ部分のフォントは可読性を高めるため「BIZ UD Gothic (12pt)」に指定されています。
- ツリー表示時の冗長な `Root` ノードの表示をスキップし、より直感的な階層管理を実現します。

## 4. アーキテクチャ構成

本アプリケーションは、以下の技術スタック構成を基本とします。

- **Backend (Python)**:
  - Broadband Forumの定義ファイル (XML等) をパースし、JSONなどの扱いやすい形式に変換する役割。
  - フロントエンドに対してデータを提供するWeb APIサーバー (FastAPI等の利用を想定)。
- **Frontend (JavaScript)**:
  - バックエンドから取得したデータモデルをツリー形式等で可視化するViewer UIの提供。
  - NETCONF等を想定したデータ編集機能 (Editor) の提供。

## 5. 基本ディレクトリ構成方針

Githubリポジトリのベストプラクティスに従い、以下のような責務分割されたディレクトリ構成を使用します。

- `backend/`: Pythonを利用したAPIサーバーやデータ処理ロジック
- `frontend/`: JavaScript (HTML/CSS含む) を利用したUI実装
- `data/`: Broadband ForumのXMLなどの元データ、キャッシュなどを配置
- `docs/`: 開発関連のドキュメント
