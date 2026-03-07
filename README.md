# WorldClassicsJP

WorldClassicsJP は、パブリックドメインの世界文学を日本語翻訳して静的サイトとして公開する自動出版プロジェクトです。

## ドキュメント

| ファイル | 内容 | バージョン |
|---------|------|-----------|
| [SPEC.md](./SPEC.md) | 全体仕様 | v1.5.1 |
| [usecase.md](./usecase.md) | ユースケースと運用フロー | v1.2.0 |
| [sequence.md](./sequence.md) | シーケンス設計 | v1.0.1 |
| [UI.md](./UI.md) | UI 設計メモ | — |
| [QandA.md](./QandA.md) | 実装 Q&A | — |

## v1 設計の重要原則

- `works_master.json` は作品メタデータ専用（実行状態は持たない）
- `state.json` は実行状態の唯一ソース（stage/status/retry/再開位置）
- publish は常に `/tmp_build` 経由で反映する
- `rss.xml` / `sitemap.xml` は補助成果物（単独失敗なら publish 継続可）
- 翻訳失敗時は進行を進めず、retry カウンタとログのみ更新する
- パス表記は Linux/WSL2 を前提に相対パス・小文字名で統一する

## 運用メモ

- 想定実行環境: OpenClaw on Windows 11 WSL2
- 日次実行: cron `0 3 * * *`
- 翻訳: Codex CLI（非対話）
- 前処理/品質チェック: ローカル LLM（Ollama 等）

