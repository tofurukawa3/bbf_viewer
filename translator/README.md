# Data Model Translator サブプロジェクト

## 概要

BBF (Broadband Forum) が策定したTR-069特化の CWMP XML データモデル群（例: `tr-181`, `tr-196`, `tr-262`）に含まれる `<description>` 要素を、英語から日本語へ一括翻訳するツール群です。

データモデル内の `Description` ノードは数千行〜数万行に及ぶため、外部API呼び出しを節約するための **ローカル翻訳キャッシュ (Translation Memory)** 機構を内蔵しており、安全に中断・再開が可能です。

## 技術スタック

- `Python 3.x`
- `lxml` (高速なXMLパース処理・ネームスペースの保持)
- `deep-translator` (Google Translateの無償APIラッパー機構)
- `tqdm` (CUI上でのプログレスバー表示)

## 環境構築 (Setup)

このサブプロジェクトを実行するには専用のPython仮想環境（venv）の作成を推奨します。

```powershell
# 1. ターミナルで translator フォルダに移動
cd translator

# 2. Python仮想環境を作成 (初回のみ)
python -m venv venv

# 3. 仮想環境をアクティベート
.\venv\Scripts\Activate.ps1

# 4. 依存ライブラリのインストール
pip install -r requirements.txt
```

## 利用方法 (Usage)

翻訳対象のXMLファイルは、リポジトリ内の `data/cwmp-data-models/` ディレクトリに存在している必要があります。

準備ができたら、以下のコマンドを実行します。
デフォルトでは `tr-181-2-16-0-cwmp-full.xml` が対象となります。

```powershell
# 仮想環境がアクティベートされている状態で実行してください
python .\translate_models.py
```

### 特定のファイルを指定して実行する場合

対象ファイル名を `--file` 引数で指定します。

```powershell
python .\translate_models.py --file "tr-196-2-1-0-cwmp-full.xml"
```

## 処理の仕組みとファイル出力

1. スクリプトは指定されたXMLファイル（例: `tr-181-*.xml`）を読み込みます。
2. XPathを用いてすべての `<description>` タグをトラバース（走査）し、英語の文字列を取得します。
3. `translation_cache.json` にその英文が存在すればキャッシュから日本語を即座に入力し、存在しなければ `deep-translator` を経由して翻訳APIを叩きます。
4. 進捗度100%に達すると、ファイル名の末尾に `-ja` を付与した新しいファイル（例: `tr-181-2-16-0-cwmp-full-ja.xml`）が `data/cwmp-data-models/` ディレクトリ内に保存されます。

## 注意事項 (Notes)

- **処理時間について**: BBFの巨大なXMLモデル（数万行クラス）の場合、API通信の制限を回避するため、初回翻訳には非常に長い時間（数十分～数時間）がかかる可能性があります。
- **中断と再開**: プロセスの実行中に `Ctrl + C` を押して中断した場合でも、直前までのキャッシュは `translation_cache.json` に保存されます。再度同一コマンドを実行するだけで途中から即座に再開（レジューム）できます。
- **Rate Limit（API制限）対策**: 万が一Google Translateによる一時ブロック (`Rate Limit`) が発生してエラーが出た場合、数時間待機したのちスクリプトを再実行してください。
