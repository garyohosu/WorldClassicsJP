
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

---

## Open Questions（未回答）

| QA番号 | 状態 | 優先度 | 質問 | 該当箇所 | コメント |
|--------|------|--------|------|----------|----------|
| Q8-1 | Open | 高 | `work_slug` が `works_master.json` の必須フィールドに存在しないが、サイト構造で多用されている。`author_slug` と同様に追加すべきか。自動生成ルール（例: title から ASCII 変換）は何か | §11 / §19 | 実装ブロッカー |
| Q8-2 | Open | 高 | QualityChecker の `score` について、合格・不合格の閾値（数値）を定義してほしい。また `score` の最大値・最小値の定義は | §9.3 | 実装ブロッカー |
| Q8-3 | Open | 高 | 翻訳失敗が複数日にわたって続いた場合の終了条件が未定義。「最大N日連続失敗で完全中断し `failed` 扱いにする」などの上限を設けるべきか | §17.1 | 無限ループ防止 |
| Q8-4 | Open | 高 | Fetcher の詳細仕様がない。①source_url からのダウンロード方法、②文字コード処理（UTF-8 変換等）、③ローカルキャッシュの有無、④ダウンロード失敗時の挙動を明記してほしい | §4 / §11 | 専用セクション追加が必要 |
| Q8-5 | Open | 高 | `works_master.json` の `title` フィールドは原語タイトルか日本語タイトルか。`author_name` / `author_name_ja` のように `title` / `title_ja` の2フィールドに分けるべきではないか | §11 | スキーマ設計 |
| Q8-6 | Open | 高 | `works_master.json` はどのように追加・管理するか。AI エージェントが自動発見・登録するのか、それとも人手で編集するのか | §11 | 運用フロー |
| Q8-7 | Open | 中 | フェーズアップ条件「2週間以上安定稼働後」の「安定稼働」の定義は何か（例: エラー率0%、またはエラー率X%以下など） | §15 | フェーズ管理 |
| Q8-8 | Open | 中 | 段落ブロック上限は「最大 12,000 文字」固定だが、Phase 2（24,000文字/日）・Phase 3（48,000文字/日）に移行した場合、1ブロックあたりの上限も引き上げるか | §15 | ブロック分割ルール |
| Q8-9 | Open | 中 | 画像取得（著者ポートレート・イラスト）は日次パイプラインの一部として実行するのか、作品登録時などの別プロセスとして実行するのか | §22.1 / §23 | 実行タイミング |
| Q8-10 | Open | 中 | AdSense Publisher ID（`ca-pub-6743751614716161`）は仕様書にハードコードされているが、`config.yaml` に移して管理すべきではないか | §27 | 設定管理 |
| Q8-11 | Open | 中 | `config.yaml` の全体スキーマを定義してほしい。現状はローカル LLM 設定のみ記載。少なくとも Codex CLI モデル名・`daily_max_chars`・現在フェーズ・AdSense ID も含めるべきか | §10 / §15 / §27 | 設定管理 |
| Q8-12 | Open | 低 | RSS フィードの形式（RSS 2.0 / Atom）と掲載内容（全ページか最新公開分のみか）を定義してほしい | §28 | RSS仕様 |
| Q8-13 | Open | 低 | 「構造化メタデータ」の実装方式を指定してほしい（JSON-LD / Open Graph / Twitter Card など） | §29 | SEO実装 |
