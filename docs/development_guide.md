# 開発ガイドライン (Development Guide)

本プロジェクトにおける開発・運用・規約の標準ガイドラインです。

## 1. バックエンド (Python)

- **パッケージ管理**: `uv` または標準 `pip` を使用します。
- **Lint と Format**: コードフォーマットおよび静的解析には `ruff` を使用します。
  - ルートディレクトリで `python -m ruff check --fix .` および `python -m ruff format .` を適宜実行してください。
- **スタイル**: PEP-8 に準拠し、Type Hints (`typing`) を積極的に活用してください。

## 2. フロントエンド (React)

- **パッケージ管理**: `npm` を使用します。
- **Lint**: ESLint および Prettier を使用してコードの統一感を保ちます。
- **コンポーネント設計**: 機能の再利用性を高めるため、極力小さなHooksとComponentsに分割します。
- **スタイル**: CSS Modules または標準的なCSSアーキテクチャに従います（Tailwind等を利用する場合は既存の設定に従うこと）。

## 3. ドキュメント (Markdown)

- すべてのMarkdownファイルは `markdownlint-cli2` の対象です。
- 長すぎる行の折り返し制限は `.markdownlint.json` の設定に従い、日本語特有の記述におけるエラーを抑止しています。

## 4. Git運用・コミットメッセージ

- `main` ブランチへの直接コミットは避け、機能ごとにブランチを作成 (例: `feature/tree-view`, `fix/xml-parser`) してください。
- コミットメッセージは分かりやすく、「何を追加・修正したか」を簡潔に記載します。
