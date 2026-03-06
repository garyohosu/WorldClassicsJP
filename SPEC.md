# SPEC.md
WorldClassicsJP 仕様書

バージョン: 1.5.0
最終更新日: 2026-03-06

---

# 1. 概要

WorldClassicsJP は、パブリックドメインの世界文学を日本語に翻訳し、静的ウェブサイトとして公開する自動出版システムである。

Project Gutenberg などの公共ドメインソースからテキストを取得し、AIを用いて日本語に翻訳し、GitHub Pages 上で公開する。

目標は、AIを活用した文学出版プラットフォームを構築し、世界の名作を日本語読者が読めるようにすることである。

---

# 2. 目標

主な目標：

- パブリックドメインの世界文学を日本語に翻訳する
- 翻訳作品を自動的に公開する
- 短編・長編連載の両方に対応する
- 著者別ナビゲーションを提供する
- パブリックドメイン画像でコンテンツを充実させる
- Google AdSense による広告収入を得る

---

# 3. 設計原則

1. 完全自動化
2. 静的サイト公開
3. 再利用可能なアーキテクチャ
4. AI エージェント駆動のワークフロー
5. 低運用コスト
6. モバイルファーストのユーザー体験

---

# 4. システムアーキテクチャ

パイプライン：

```
原文テキスト
↓
Fetcher（取得）
↓
Preprocessor（ローカル LLM）
↓
Translator（Codex CLI / GPT-5 系モデル）
↓
QualityChecker（品質チェック AI エージェント）
↓
Publisher（公開）
↓
GitHub Pages
```

自動化は OpenClaw の cron 実行によってトリガーされる。

---

# 5. 実行環境

自動化は OpenClaw によって実行される。

## OpenClaw とは

OpenClaw（旧称: Clawdbot / Moltbot）は、ユーザー専有のミニPC上で動作するオープンソースの自律型 AI エージェントである。Codex CLI を活用し、スケジュール実行・ファイル操作・Web ブラウジング・シェルコマンド実行を自律的に行う。

実行環境：**Windows 11 の WSL2**（Windows Subsystem for Linux 2）上で動作する。cron・シェルスクリプト・Python 等の Linux ツールチェーンをそのまま利用できる。

OpenClaw の責務：

- cron によるスケジュールジョブの実行
- AI エージェントのオーケストレーション
- 翻訳コマンドの実行
- 翻訳結果の GitHub へのコミット・プッシュ

参考: https://openclaw.ai/

---

# 6. スケジューリング

実行頻度：1日1回

cron 実行は OpenClaw が管理する。

例：

```
0 3 * * *
```

これにより翻訳パイプライン全体がトリガーされる。

---

# 7. 翻訳エンジン

翻訳は Codex CLI を使用して非インタラクティブに実行する。

使用モデルは設定可能とし、2026-03-06 時点の既定運用モデルは `gpt-5.4` とする。

重要要件：

- Codex CLI は `exec` モードで動作させること
- モデル名は設定ファイルまたは環境変数で切り替え可能にすること
- 翻訳対象テキストは、テンプレートを展開した**最終プロンプト文字列**として Codex CLI に渡すこと
- 出力形式は JSON とし、最低でも `translated_text` / `summary` / `keywords` を返すこと

例（PowerShell）：

```powershell
@"
[展開済み翻訳プロンプト本文]
"@ | codex exec -m gpt-5.4 -
```

運用上は Codex CLI の定額プラン（ChatGPT Plus）を使用するが、将来のモデル変更に備えてコード中に固定値を埋め込まない。

---

# 8. 翻訳プロンプト設計

翻訳品質はプロンプト設計に大きく依存する。以下の方針に従うこと。

## 8.1 文体・表記方針

- 文体：常体（だ・である調）を基本とする
- 固有名詞：原語のカタカナ表記を優先する
- 文化的背景：直訳を避け、日本語読者に自然な表現を使う
- 段落構造：原文の段落分けを尊重する

## 8.2 プロンプトファイル

翻訳プロンプトは `translate_prompt.md` のテンプレートとして管理する。

実行時はテンプレート中のプレースホルダを展開して最終プロンプト文字列を生成し、その文字列を Codex CLI に stdin または引数で渡す。`translate_prompt.md` の**ファイルパス自体**をプロンプトとして渡してはならない。

プロンプトには以下を含めること：

- `title`
- `author`
- `segment_text`
- `part_number`
- `translation_rules`
- 文体・表記ルール
- 翻訳品質の注意事項

## 8.3 プロンプト更新方針

翻訳品質の問題が検出された場合はプロンプトを改善し、バージョン管理する。

---

# 9. 品質チェック AI エージェント

翻訳後に品質チェック専用の AI エージェントを実行する。

## 9.1 チェック項目

- 日本語として自然な文章になっているか
- 誤訳・意味の欠落がないか
- 固有名詞の表記ゆれがないか
- 段落構造が原文と対応しているか
- 文字化け・記号の異常がないか

## 9.2 使用モデル

品質チェックはローカル LLM（Ollama 等）を使用し、API コストを抑える。

## 9.3 チェック結果

QualityChecker の出力形式は JSON とし、最低でも以下を返すこと：

- `status`
- `score`
- `issues`

判定ルール：

- 合格：Publisher へ進む
- 不合格：エラーログに記録し、同一実行内で再翻訳を最大2回行う
- 同一実行内で解消しない場合：そのセグメントは翌日の実行で再挑戦する（§17 参照）

---

# 10. ローカル LLM の使用

ローカル LLM（Ollama 等）は以下の用途で使用する：

- 段落分割
- テキストクリーニング
- メタデータ生成
- 要約
- タイトル正規化
- 品質チェック（§9 参照）

ローカル LLM は2台の専用マシンで動作し、無制限かつ無料で使用できる。

設定はリポジトリルートの `config.yaml` で管理し、最低でも以下を定義する：

- `host`
- `port`
- `model`

利点：

- API トークン使用量を削減する
- オフライン処理が可能
- 前処理が高速化される

---

# 11. ソースデータ

主なソース：

- Project Gutenberg
- Internet Archive
- その他パブリックドメイン文学リポジトリ

v1 で受け入れる原文ソース形式は以下に限定する：

- TXT ファイル
- Plain Text URL

作品マスタは `/data/works_master.json` に保持し、自動生成する。

`works_master.json` の必須フィールド：

| フィールド | 説明 |
|-----------|------|
| work_id | 整数連番の作品 ID |
| work_slug | 作品の URL スラッグ（ASCII 小文字 + ハイフン。重複時は末尾に `-2` `-3` を付加） |
| title | 作品タイトル（原語） |
| title_ja | 作品タイトル（日本語訳） |
| author_name | 著者名（原語） |
| author_name_ja | 著者名（日本語） |
| author_slug | 著者 URL スラッグ |
| source_url | 原文取得元 URL |
| source_type | `txt` または `text_url` |
| death_year | 著者没年 |
| pd_verified | パブリックドメイン確認済みフラグ |
| length_class | `short` / `medium` / `long` |

---

# 12. 著作権ポリシー

## 12.1 基本方針

本システムはパブリックドメイン作品のみを対象とする。

## 12.2 国別著作権の注意事項

Project Gutenberg は米国著作権法に基づきパブリックドメインと判断した作品を公開している。しかし、国によって保護期間が異なるため、日本国内での公開には個別確認が必要な場合がある。

日本の著作権保護期間：著作者の死後 **70年**（2018年法改正により50年から延長）

米国では合法でも日本では保護対象となり得る例：

- 1955〜1967年に亡くなった著者の作品は、日本では 2025〜2037年まで保護対象
- 1928年以前に出版された米国パブリックドメイン作品でも、著者の没年次第では日本での公開に注意が必要

## 12.3 確認手順

作品登録時に著者の没年を確認し、`没年 + 70年 < 現在年` であることを検証する。確認結果は作品メタデータに記録する。

---

# 13. 作業分類

作品は文字数で分類する。

| 分類 | 文字数 |
|------|--------|
| short（短編） | 30,000文字未満 |
| medium（中編） | 30,000〜150,000文字 |
| long（長編） | 150,000文字超 |

---

# 14. 公開単位

## 短編

1回の実行で完結させて公開する。

## 中編

原則として1回の実行で完結させて公開する。ただし `daily_max_chars` を超える場合は長編と同様の分割ルールを適用する。

## 長編

分割して連載形式で公開する。

分割の優先順位：

1. `CHAPTER` / `Chapter` / `CHAP` / `BOOK` 等の見出し検出による章の区切り
2. 見出しが検出できない場合は段落単位で分割する
3. 章（または段落ブロック）が1日の上限を超える場合は段落ブロック単位でさらに分割する

---

# 15. 1日の翻訳量上限

コストと実行時間を管理するため、1日あたりの翻訳量を以下のように段階的に設定する。

上限は**原文基準の文字数**で管理する。運用開始時は少量から始め、問題がなければ徐々に増やす。本仕様ではこの日次上限値を `daily_max_chars` と呼ぶ。

| フェーズ | 上限原文文字数 | 条件 |
|---------|---------------|------|
| 初期（Phase 1） | 12,000文字/日 | 運用開始時 |
| 拡張（Phase 2） | 24,000文字/日 | Phase 1 で2週間以上安定稼働後 |
| 最大（Phase 3） | 48,000文字/日 | Phase 2 で2週間以上安定稼働後 |

章が上限を超える場合は、原文文字数を基準に段落単位で分割する。

段落ブロック分割ルール：

- 1ブロックあたり最大 12,000 文字
- 改行・段落境界をまたいで切らない
- `current_segment_id` は章番号とブロック番号の組み合わせで一意にする

---

# 16. 連載ポリシー

長編作品の連載が開始した場合：

- 作品が完結するまで後続パートを継続して公開する
- 明示的に設定しない限り、連載中に別作品に切り替えない

## 16.1 次作品への移行ルール

1つの作品が `complete` になった場合、`works_master.json` から次の未完了作品を探して処理を継続する。

次作品の選択条件：

- `current_work_status` が `complete` / `failed` / `paused` **以外**の作品を対象とする
- `work_id` の昇順で最初に見つかった作品を次作品とする
- `pd_verified = true` であること

次作品が見つからない場合は `current_work_status` を `exhausted` に設定し、その日の処理を終了する。

## 16.2 exhausted 遷移条件

v1 では以下の **2条件** で `exhausted` に遷移する：

1. **キュー枯渇**: `works_master.json` に `complete` / `failed` / `paused` 以外の次作品が存在しない（全作品が完了または処理停止）
2. **恒久的取得不能**: `source_url` が有効でも原文取得対象が実質空であり、継続不能と判定された場合

以下は `exhausted` に**含めない**：

- 一時的なネットワーク障害による fetch 失敗 → 翌日再試行
- QualityChecker 不合格 → translate リトライ
- `state.json` の `consecutive_fail_days < 2` の翻訳失敗 → 翌日再挑戦

`exhausted` は「材料が尽きた」状態を表し、一時的な障害では遷移しない。

---

# 17. エラーハンドリングとリトライ

## 17.1 翻訳失敗時

- 状態を更新しない
- エラーをログに記録する
- `state.json.current_stage` を `translate` に設定する
- 総試行数は「初回1回 + 同一実行内の再翻訳最大2回」とする
- Codex CLI 実行失敗、JSON 形式不正、または QualityChecker の不合格時は同一実行内で再翻訳を最大2回行う
- 同一実行内で解消しない場合は `current_segment_id` を維持したままその日の処理を終了し、タイトルに【翻訳未完】を付記する
- 翌日の cron 実行で同一セグメントに再挑戦する
- **2日連続で同一セグメントの翻訳に失敗した場合は `current_work_status` を `failed` に設定し、手動対応が必要な状態として処理を停止する**
- `state.json.translate_retry_count` は同一実行内の再翻訳回数として扱う
- `state.json.consecutive_fail_days` は連続失敗日数を記録し、翻訳成功時に 0 にリセットする
- 翻訳に成功した時点で `translate_retry_count` と `consecutive_fail_days` を 0 に戻す

## 17.2 翻訳ステータス表示

作品の翻訳状態をタイトルに付記する：

| 状態 | 表示例 |
|------|--------|
| 翻訳処理中 | `ロビンソン・クルーソー【翻訳中】` |
| 翻訳完了 | `ロビンソン・クルーソー` |
| 翻訳未完（翌日再挑戦） | `ロビンソン・クルーソー【翻訳未完】` |

## 17.3 公開失敗時

- コミットを中断する
- 前の状態を保持する
- Publisher は必ず `/tmp_build` 配下に成果物を生成し、成功時のみ本番パスへ反映する
- 公開成功の必須成果物は `index.html` / work page / part page / author page とする
- 本番パスへ反映する直前に、公開処理開始前の git revision を `pre_publish_head` として記録する
- `state.json.current_stage` を `publish` に設定する
- `state.json.publish_retry_count` を 1 ずつ増やし、次の実行サイクルで同一パートを最大3回リトライする
- 公開成功時に `publish_retry_count` を 0 に戻し、その後にのみ `current_part` / `next_work_id` を進める
- 公開失敗時は `/tmp_build` を破棄し、本番ファイルを変更しない
- `git commit` または `git push` が失敗した場合は、本番パスに反映した差分とローカル履歴を `pre_publish_head` に復元し、`/tmp_build` を破棄し、`state.json` を進めない

---

# 18. 状態管理

システムの状態は `state.json` で管理する。

必須フィールド：

- `next_work_id`: 次に着手する作品 ID
- `current_work_id`: 現在処理中の作品 ID
- `current_part`: 現在処理中のパート番号
- `current_segment_id`: 現在処理中のセグメント識別子
- `current_stage`: 現在の処理段階（`idle` / `preprocess` / `translate` / `quality_check` / `publish`）
- `current_work_status`: 作品の状態
- `last_processed_date`: 最終処理日
- `last_run_id`: 実行ごとの一意 ID
- `translate_retry_count`: 同一実行内の翻訳リトライ回数（最大2）
- `consecutive_fail_days`: 同一セグメントの連続失敗日数（2日で `failed` 確定）
- `publish_retry_count`: 公開リトライ回数

`next_work_id` および `current_work_id` は `/data/works_master.json` の `work_id` を参照し、整数連番で管理する。

初期化ルール：

- `state.json` が存在しない場合は、`/data/works_master.json` の最小 `work_id` を使って初期状態を自動生成する
- 初期生成時の値は `next_work_id = current_work_id = 最小 work_id`、`current_part = 1`、`current_segment_id = ""`、`current_stage = "idle"`、`current_work_status = "active"`、`translate_retry_count = 0`、`consecutive_fail_days = 0`、`publish_retry_count = 0` とする
- 初期化後、同一実行内で通常のパイプライン処理を継続する

例：

```json
{
  "next_work_id": 5,
  "current_work_id": 3,
  "current_part": 4,
  "current_segment_id": "chapter-04-part-01",
  "current_stage": "translate",
  "current_work_status": "active",
  "last_processed_date": "2026-03-06",
  "last_run_id": "20260306T030000Z-18432",
  "translate_retry_count": 1,
  "consecutive_fail_days": 0,
  "publish_retry_count": 0
}
```

ステータス一覧：

| ステータス | 説明 | 移行トリガー |
|-----------|------|------------|
| active | 現在処理中（連載中含む） | 初期化時・次作品移行時・手動復旧時 |
| paused | 管理者が `state.json` を手動変更して設定する一時停止状態 | **管理者による手動操作のみ** |
| complete | 個別作品の全パート公開完了 | Publisher が全パート完了を検出した時点 |
| exhausted | キューに処理可能な次作品が存在しない、または恒久的に取得不能な状態（§16.2 参照） | LOAD_NEXT で次作品が見つからない時・恒久的取得不能判定時 |
| failed | 2日連続翻訳失敗による中断。手動対応が必要 | `consecutive_fail_days >= 2` |

復旧ルール：

- 次回実行時は `current_segment_id` と `current_stage` を見て同一セグメントから再開する
- `preprocess` / `translate` / `quality_check` で中断した場合は、**前処理キャッシュに依存せず** raw source から当該セグメントを再切り出しして翻訳処理を先頭からやり直す
- 翻訳または品質チェックがその日の再試行上限に達した場合は、そのセグメントを翌日の最優先対象として再実行する
- 翌日の再実行を開始する際は `translate_retry_count` を 0 に戻す
- `publish` で中断した場合は、同一パートの Publisher を再実行し、成功するまで `current_part` を進めない
- `current_stage` を `idle` に戻すのは、そのセグメントの publish 成功後のみとする

## 18.1 ファイルの整合性保護

`state.json` の書き込みは必ずアトミック操作で行う：

1. 一時ファイル（`state.json.tmp`）に書き込む
2. 検証後、アトミックリネーム（`mv` 等）で本番ファイルに置き換える
3. 並列実行を防ぐため、処理開始時に `state.lock` を**排他的に作成**し、JSON で `run_id` / `pid` / `started_at` / `heartbeat_at` を記録する
4. 処理中はステージ切り替えごとに `heartbeat_at` を更新する
5. `state.lock` が存在する場合は内容を読み取り、対応する `pid` が生存中かつ `heartbeat_at` が 6 時間以内であれば、その回の実行を中止する
6. `pid` が存在しない、または `heartbeat_at` が 6 時間を超えて古い場合のみ、`state.lock.stale.<run_id>` にリネームしてから新しいロックを取得する
7. 正常終了時は `state.lock` を削除する

## 18.2 実行ログ

実行ログは `/logs/YYYY/MM/DD/run_id.json` に保存する。

- `run_id` は `state.json.last_run_id` と同じ値を使用する
- 失敗時もログは保存する

---

# 19. サイト構造

公開サイト構造：

```
/
├── index.html
├── authors/
│   ├── index.html
│   └── <author-slug>/
│       └── index.html
├── works/
│   └── <work-slug>/
│       ├── index.html
│       ├── part-001/
│       │   └── index.html
│       └── part-002/
│           └── index.html
├── assets/
│   └── images/
│       ├── authors/
│       ├── illustrations/
│       └── decorative/
├── rss.xml
├── sitemap.xml
└── robots.txt
```

内部運用ファイル：

```
/config.yaml
/data/works_master.json
/logs/YYYY/MM/DD/<run_id>.json
/tmp_build/
```

スラッグルール：

- `author_slug` / `work_slug` は ASCII 小文字とハイフンのみを使用する
- 重複が発生した場合は末尾に `-2` `-3` のように連番サフィックスを付加する

---

# 20. 著者ページ

著者ナビゲーションは必須とする。

構造：

```
/authors/index.html
/authors/<author-slug>/index.html
```

著者ページに含める情報：

- 著者ポートレート
- 略歴サマリー
- 翻訳済み作品の一覧
- 連載作品の進捗

例：

```
マーク・トウェイン
トム・ソーヤーの冒険（連載中）
跳び蛙（完結）
```

---

# 21. 著者メタデータ

必須フィールド：

| フィールド | 説明 |
|-----------|------|
| author_name | 著者名（原語） |
| author_name_ja | 著者名（日本語） |
| author_slug | URL用スラッグ |
| birth_year | 生年 |
| death_year | 没年 |
| description | 略歴（日本語） |

---

# 22. パブリックドメイン画像ポリシー

画像は、権利条件が単純なものだけを採用する。

v1 で許可する権利表示は以下のいずれかに限定する：

- `Public domain`
- `CC0`
- `Public Domain Mark`

上記以外（`CC BY` / `CC BY-SA` / `fair use` / 権利不明）は採用しない。

ソース：

- Wikimedia Commons の個別ファイルページ
- Wikipedia から辿れる個別ファイルページ
- Project Gutenberg のイラスト
- 歴史的アーカイブ

## 22.1 取得方法

画像取得は日次翻訳パイプラインとは**分離した補助ジョブ**として実行する。

実行タイミング：`works_master.json` に新しい作品または著者が追加された時（作品登録時・手動トリガー）

理由：Wikimedia Commons 側の都合による失敗が日次翻訳パイプラインの安定性に影響しないようにする。画像が未取得の場合は画像枠を非表示にするため、翻訳公開の妨げにならない。

取得方法：API を使わず、AI エージェントがブラウザ操作または直接 URL 取得で保存する。人手の手動操作は前提としない。

各画像はダウンロード前に個別ファイルページで権利表示を確認し、許可された権利表示に一致する場合のみ保存する。

## 22.2 ライセンス記録

各画像にはメタデータを付与する：

| フィールド | 説明 |
|-----------|------|
| source_page_url | 個別ファイルページURL |
| file_url | 実ファイルURL |
| author | 著作者 |
| rights_label | `Public domain` / `CC0` / `Public Domain Mark` |
| year | 制作年 |
| rights_verified_at | 権利確認日 |

メタデータは画像ファイルと同名の YAML sidecar ファイルとして保存する。

---

# 23. 著者ポートレート

著者ページには、利用可能な場合はポートレートを掲載する。

Wikimedia Commons の個別ファイルページを AI エージェントが確認し、§22 の条件を満たす画像のみ取得する。

利用可能な画像がない場合は、著者ページの画像枠を表示しない。

保存場所：

```
/assets/images/authors/<author-slug>.jpg
```

---

# 24. イラスト対応

オリジナルのイラストが利用可能で、§22 の条件を満たす場合は保存する。

配置場所：段落間またはセクション境界

利用可能な画像がない場合は、画像ブロックを挿入しない。

保存場所：

```
/assets/images/illustrations/
```

---

# 25. モバイル対応

モバイルファーストのレスポンシブデザインを必須とする。

要件：

- 読みやすいタイポグラフィ
- レスポンシブ画像
- シンプルなナビゲーション
- 高速なページ読み込み

画像設定：

```html
<img src="/assets/images/..." alt="..." loading="lazy" decoding="async">
```

---

# 26. ナビゲーション要件

作品ページには以下のナビゲーションを含めること：

- 前へ
- 次へ
- 目次
- 著者ページ

---

# 27. 広告統合

Google AdSense をすべてのページに表示する。

共通レイアウトには以下の AdSense スクリプトを挿入する：

```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6743751614716161" crossorigin="anonymous"></script>
```

対象ページ：

- トップページ
- 著者ページ
- 作品ページ
- 連載ページ

推奨配置：

- ヘッダー
- 記事中央
- フッター

広告は読書体験を妨げないこと。

---

# 28. RSS・サイトマップの自動更新

RSS フィード（`rss.xml`）およびサイトマップ（`sitemap.xml`）は、パイプライン実行時に**自動更新**する。

更新タイミング：Publisher ステップの完了後、GitHub へのコミット前に生成・更新する。

canonical URL および RSS / サイトマップのルートURLは以下を使用する：

`https://garyohosu.github.io/WorldClassicsJP/`

`rss.xml` と `sitemap.xml` は補助成果物とし、主要公開物の生成成功後に更新する。

---

# 29. SEO 戦略

SEO 改善項目：

- 著者ページ
- 画像 alt テキスト（日本語）
- 構造化メタデータ
- canonical URL
- RSS フィード
- サイトマップ

---

# 30. リポジトリ

リポジトリ：

https://github.com/garyohosu/WorldClassicsJP

デプロイ先：

GitHub Pages

---

# 31. 言語方針

本システムおよび本仕様書は**日本語を主要言語**とする。

- 仕様書：日本語
- サイトコンテンツ：日本語
- コミットメッセージ・コードコメント：日本語を推奨（英語も可）
- ユーザー向け UI：日本語

---

# 32. 長期ビジョン

WorldClassicsJP は AI 駆動の世界文学アーカイブを目指す。

将来の可能性：

- 多言語翻訳対応
- 著者タイムラインページ
- 文学ディスカバリーツール
- 言語横断的な文学データセット

本プラットフォームはグローバルなパブリックドメイン文学ハブを目標とする。
