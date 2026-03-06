
# QandA.md

WorldClassicsJP 実装Q&Aシート

最終更新日: 2026-03-06

---

## Open Questions（回答済み）

| QA番号 | 状態 | 優先度 | 質問 | コメント | 回答 |
|--------|------|--------|------|----------|------|
| Q1-1 | Closed | 高 | 作品一覧データはどのファイルに保持し、1作品あたりの必須フィールドは何か | 作品マスタ | `/data/works_master.json` を使用。自動生成。必須: work_id, title, author_name, author_name_ja, author_slug, source_url, source_type, death_year, pd_verified, length_class |
| Q1-2 | Closed | 高 | work_id は整数連番・slug・UUID のどれを正とするか | ID方式 | 整数連番 |
| Q1-3 | Closed | 高 | medium作品の公開方式 | 公開単位 | 原則1回公開。ただし daily_max_chars を超える場合は分割 |
| Q2-1 | Closed | 高 | Fetcher が受け入れる原文ソース形式 | v1範囲 | TXT / Plain Text URL |
| Q2-2 | Closed | 高 | 原文の章区切り判定 | 長編分割 | CHAPTER / Chapter / CHAP / BOOK 等の見出し検出 |
| Q2-3 | Closed | 高 | 段落ブロック分割ルール | 長編処理 | 最大12000文字、段落単位 |
| Q3-1 | Closed | 高 | translate_prompt.md の必須変数 | 翻訳仕様 | title, author, segment_text, part_number, translation_rules |
| Q3-2 | Closed | 高 | Codex CLI 出力形式 | Publisher連携 | JSON (translated_text, summary, keywords) |
| Q3-3 | Closed | 中 | ローカルLLM設定 | Ollama | config.yaml に host, port, model |
| Q4-1 | Closed | 高 | QualityChecker 出力 | QA判定 | JSON: status, score, issues |
| Q4-2 | Closed | 高 | 不合格時の再翻訳 | 再試行 | 同一実行内最大2回 |
| Q4-3 | Closed | 高 | 翻訳失敗時 | 停止条件 | 翌日再挑戦 |
| Q5-1 | Closed | 高 | Publisher成果物 | 成功条件 | index.html / work page / part page / author page |
| Q5-2 | Closed | 高 | 公開失敗時ファイル | 再実行 | tmp_build 生成→成功時反映 |
| Q5-3 | Closed | 中 | canonical URL | GitHub Pages | https://garyohosu.github.io/WorldClassicsJP/ |
| Q5-4 | Closed | 高 | slug生成ルール | URL生成 | ASCII小文字 + ハイフン |
| Q6-1 | Closed | 中 | 画像メタデータ | sidecar | YAML |
| Q6-2 | Closed | 低 | 画像未取得 | UI | 画像枠非表示 |
| Q7-1 | Closed | 中 | AdSense | 広告 | `<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6743751614716161" crossorigin="anonymous"></script>` をlayoutに挿入 |
| Q7-2 | Closed | 高 | 実行ログ保存 | 運用 | `/logs/YYYY/MM/DD/run_id.json` |
