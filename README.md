# BBF DataModel Viewer & Editor

Broadband ForumのDataModel (TR-069: FAP, Femto, Transport) を表示・編集するためのローカルWebアプリケーションです。

## プロジェクト構成

- `AGENT.md`: プロジェクトの目標および要件定義
- `backend/`: Pythonを利用したAPIサーバー(FastAPI等)。データモデルのパースと配信を担当。
- `frontend/`: JavaScript/React等を利用したUI。データをツリー形式等で表示および編集機能を提供。
- `data/`: 解析対象となる各種XMLファイルなどの入力ソース類を配置。
- `docs/`: プロジェクトの設計書等のドキュメント。

## 主な機能

- **Viewモード / Editモード**:
  - Viewモードでは全パラメータを安全に閲覧できます。
  - Editモードでは `<edit-config>` の対象となるWrite権限を持つパラメータのみを抽出し、NETCONFペイロードを生成します。
- **リアルタイム検索**: ツリー内のパラメータを部分一致で即座にフィルタリング可能です。
- **安全なXML生成**: 生成されたXMLはメモ帳風のRead-onlyビューに表示され、予期せぬ変更を防ぎます。

詳細な操作方法や起動手順については、[docs/getting_started.md](docs/getting_started.md) を参照してください。

## 開発環境のセットアップと起動

Windowsの場合は提供されている起動スクリプトを利用して、BackendとFrontendを同時に立ち上げることができます。

```powershell
# 初回起動時は依存関係(uv, npm)が自動でインストールされます
.\start.ps1 -Install

# 通常の起動
.\start.ps1
```
