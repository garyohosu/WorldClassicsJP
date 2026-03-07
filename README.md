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

### 1. Python 環境のセットアップ

```bash
cd /home/garyo/WorldClassicsJP
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

### 2. 設定ファイルの作成

```bash
# config.yaml を作成
cp config.yaml.template config.yaml

# 必要に応じて config.yaml を編集
nano config.yaml
```

設定項目:
- `host`: ローカル LLM のホスト名（通常は "localhost"）
- `port`: ローカル LLM のポート（Ollama のデフォルトは 11434）
- `model`: 使用する LLM モデル名（例: "llama3:8b"）
- `daily_max_chars`: 1日の翻訳量上限（初期値: 12000）
- `current_phase`: 運用フェーズ（1/2/3）

### 3. ローカル LLM のセットアップ

前処理と品質チェックに Ollama を使用します。

```bash
# Ollama のインストール（WSL2 Ubuntu）
curl -fsSL https://ollama.ai/install.sh | sh

# モデルのダウンロード
ollama pull llama3:8b

# サーバーの起動
ollama serve
```

### 4. Codex CLI のセットアップ

Codex CLI と、前処理・品質チェック用のローカル LLM を別途利用可能な状態にしておきます。

Codex CLI の詳細は https://codex.storage を参照してください。

### 5. 翻訳プロンプトのカスタマイズ（オプション）

デフォルトの翻訳プロンプトは `templates/translate_prompt.md` にあります。
必要に応じて編集してください。

プレースホルダー:
- `{{title}}`: 作品タイトル
- `{{author}}`: 著者名
- `{{part_number}}`: パート番号
- `{{segment_text}}`: 翻訳対象テキスト

## 起動方法

### 日次パイプライン実行（実装済み）

```bash
cd /home/garyo/.openclaw/workspace/WorldClassicsJP
PYTHONPATH=src python3 -m worldclassicsjp.run
```

オプション:

```bash
# Git commit/push なしで生成確認のみ
PYTHONPATH=src python3 -m worldclassicsjp.run --no-git

# 日付指定
PYTHONPATH=src python3 -m worldclassicsjp.run --date 2026-03-08
```

### OpenClaw cron 例（WSL2/Linux）

```bash
openclaw cron add \
  --name "WorldClassicsJP daily" \
  --cron "0 3 * * *" \
  --tz "Asia/Tokyo" \
  --session isolated \
  --message "作業ディレクトリ /home/garyo/.openclaw/workspace/WorldClassicsJP で PYTHONPATH=src python3 -m worldclassicsjp.run を実行。成功時は公開URLとcommitを報告、失敗時は要点3行で報告。"
```

