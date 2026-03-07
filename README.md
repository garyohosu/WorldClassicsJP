# WorldClassicsJP

WorldClassicsJP は、パブリックドメインの世界文学を日本語翻訳して静的サイトとして公開する自動出版プロジェクトです。

## ドキュメント

| ファイル | 内容 | バージョン |
|---------|------|-----------|
| [SPEC.md](./SPEC.md) | 全体仕様 | v1.5.1 |
| [usecase.md](./usecase.md) | ユースケースと運用フロー | v1.2.0 |
| [sequence.md](./sequence.md) | シーケンス設計 | v1.0.1 |
| [class.md](./class.md) | クラス図 | v1.0.0 |
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

## セットアップ

Win11 ホスト上の WSL2 Ubuntu で実行する前提です。

```bash
cd /home/garyo/WorldClassicsJP
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

Codex CLI と、前処理・品質チェック用のローカル LLM を別途利用可能な状態にしておきます。

## 起動方法

現時点のリポジトリはライブラリ実装とテストが中心で、日次パイプラインを起動する単一の CLI エントリーポイントはまだ入っていません。

開発・検証時の実行:

```bash
cd /home/garyo/WorldClassicsJP
. .venv/bin/activate
pytest -q
```

OpenClaw cron から WSL2 内で Codex CLI を呼ぶ想定例:

```bash
cd /home/garyo/WorldClassicsJP
. .venv/bin/activate
codex exec -m gpt-5.4 "Read README.md and worldclassicsjp_codex_instructions/CODEX_CLI_INSTRUCTIONS.md, then implement the system."
```

cron 例:

```cron
0 3 * * * cd /home/garyo/WorldClassicsJP && . .venv/bin/activate && codex exec -m gpt-5.4 "Read README.md and worldclassicsjp_codex_instructions/CODEX_CLI_INSTRUCTIONS.md, then implement the system."
```

OpenClaw 側ではこの cron を WSL2 の Ubuntu 環境で実行し、作業ディレクトリを `/home/garyo/WorldClassicsJP` に固定します。
