
# QandA.md

WorldClassicsJP 実装Q&Aシート

最終更新日: 2026-03-06

---

## Open Questions（回答済み）

| QA番号 | 状態 | 優先度 | 質問 | コメント | 回答 |
|--------|------|--------|------|----------|------|
| Q1-1 | Closed | 高 | 作品一覧データはどのファイルに保持し、1作品あたりの必須フィールドは何か | 作品マスタ設計 | `/data/works_master.json` を使用。自動生成。必須: work_id, title, title_ja, author_name, author_name_ja, author_slug, source_url, source_type, death_year, pd_verified, length_class |
| Q1-2 | Closed | 高 | `work_id` は整数連番・slug・UUID のどれを正とするか | ID設計 | 整数連番を採用。URL生成は `work_slug` を使用 |
| Q1-3 | Closed | 高 | `medium` 作品は短編と同じく1回で完結公開するのか、それとも長編と同様に連載対象にするのか | 公開単位 | 原則1回公開。ただし `daily_max_chars` を超える場合は長編と同様に分割公開 |
| Q2-1 | Closed | 高 | Fetcher が受け入れる原文ソース形式は TXT・HTML・EPUB・Plain Text URL のどこまでとするか | v1対応範囲 | v1では TXT / Plain Text URL のみ対応 |
| Q2-2 | Closed | 高 | 原文の章区切り判定ルールは何を正とするか | 長編分割 | CHAPTER / Chapter / CHAP / BOOK などの見出し検出。見出しが無い場合は段落分割 |
| Q2-3 | Closed | 高 | 章が1日の上限を超えた場合の段落ブロック分割ルールは何か | 分割ロジック | 最大12000文字を上限として段落単位で分割 |
| Q3-1 | Closed | 高 | `translate_prompt.md` のテンプレート変数は何を必須とするか | プロンプト仕様 | title, author, segment_text, part_number, translation_rules |
| Q3-2 | Closed | 高 | Codex CLI の出力形式は自由文か JSON か | Publisher連携 | JSON形式 (translated_text, summary, keywords) |
| Q3-3 | Closed | 中 | ローカル LLM の接続先とモデル名の設定方法は何か | Ollama想定 | `config.yaml` に host / port / model を定義 |
| Q4-1 | Closed | 高 | QualityChecker の入出力フォーマットは何か | QA判定 | JSON: status(pass/fail), score, issues[] |
| Q4-2 | Closed | 高 | QualityChecker の不合格時は同一実行内で即時再翻訳するのか、それとも次回日次実行に持ち越すのか | 再試行 | 同一実行内で最大2回再翻訳 |
| Q4-3 | Closed | 高 | 翻訳失敗が3回に達したセグメントの扱いは | 停止条件 | 当日は「翻訳未完」として処理停止。次回cronで再試行。2日連続失敗した場合 `failed` |
| Q5-1 | Closed | 高 | Publisher が生成する成果物の最小セットは何か | 成功判定 | index.html / work page / part page / author page |
| Q5-2 | Closed | 高 | 公開失敗時に作業ツリーへ生成済みファイルが残った場合の扱いはどうするか | 再実行対策 | `/tmp_build` で生成し成功時のみ公開ディレクトリへ移動 |
| Q5-3 | Closed | 中 | RSS と sitemap.xml に入れる canonical URL のルートは何か | GitHub Pages | https://garyohosu.github.io/WorldClassicsJP/ |
| Q5-4 | Closed | 高 | slug生成ルール | URL設計 | ASCII小文字 + ハイフン。重複時は -2 -3 |
| Q6-1 | Closed | 中 | 画像メタデータはどのファイル形式・保存場所で管理するか | sidecar管理 | YAML sidecar |
| Q6-2 | Closed | 低 | 画像が見つからない場合にページへプレースホルダー画像を出すのか | UI | 画像枠を非表示 |
| Q7-1 | Closed | 中 | AdSense は v1 で実IDを埋め込むのか | 広告 | layout に `<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6743751614716161" crossorigin="anonymous"></script>` を挿入 |
| Q7-2 | Closed | 高 | 実行ログの保存場所とJSONスキーマは何か | 運用 | `/logs/YYYY/MM/DD/run_id.json` |
