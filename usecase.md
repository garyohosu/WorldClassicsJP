# usecase.md
WorldClassicsJP ユースケース設計

バージョン: 1.2.0
最終更新日: 2026-03-06
対応 SPEC: v1.5.0

---

## 1. アクター定義

| アクター | 種別 | 説明 |
|---------|------|------|
| **cron** | システム | OpenClaw 内蔵スケジューラ。毎日 03:00 にパイプラインをトリガーする |
| **OpenClaw** | 自律 AI エージェント | Win11 WSL2 上で動作するオーケストレーター。全 UC の主アクター |
| **ローカル LLM** | AI システム | Ollama 等。前処理・品質チェックに使用。無制限・無料 |
| **Codex CLI** | AI システム | GPT-5.4 モデル。翻訳専用。定額プランのトークン上限あり |
| **GitHub** | 外部サービス | リポジトリホスティング・GitHub Pages でのサイト公開 |
| **Wikimedia Commons** | 外部サービス | 著者ポートレート・イラストの取得元 |
| **管理者** | 人間 | `failed` 発生時にのみ手動介入する |
| **読者** | 人間 | 公開されたサイトを閲覧する |

---

## 2. ユースケース一覧

| UC番号 | ユースケース名 | 主アクター | 概要 |
|--------|--------------|-----------|------|
| UC-01 | 日次パイプライン起動 | cron | 毎日 03:00 に OpenClaw を起動し、パイプラインを開始する |
| UC-02 | ロック取得・状態復旧・初期化 | OpenClaw | 二重起動を防ぎ、`state.json` が無ければ初期生成し、前回中断状態から再開する |
| UC-03 | 原文テキスト取得 | OpenClaw | works_master.json に基づき source_url から原文を取得する |
| UC-04 | テキスト前処理 | ローカル LLM | 段落分割・クリーニング・メタデータ生成を行い、セグメントを生成する |
| UC-05 | テキスト翻訳 | Codex CLI | セグメントを日本語に翻訳し、JSON で結果を返す |
| UC-06 | 翻訳品質チェック | ローカル LLM | 翻訳結果の自然さ・正確さ・表記ゆれを検証する |
| UC-07 | 同一実行内リトライ | OpenClaw | 翻訳失敗・品質不合格時に最大2回再翻訳する |
| UC-08 | 翻訳失敗確定処理 | OpenClaw | 2日連続失敗で `failed` に設定し処理を停止する |
| UC-09 | サイト生成・公開 | OpenClaw | 翻訳結果から HTML を生成し、tmp_build 経由で公開する |
| UC-10 | RSS・サイトマップ更新 | OpenClaw | 公開完了後に rss.xml・sitemap.xml を自動生成・更新する |
| UC-11 | GitHub コミット・プッシュ | OpenClaw | 生成した成果物を GitHub にコミット・プッシュし、GitHub Pages に反映する |
| UC-12 | 状態保存（state.json） | OpenClaw | 各ステージ完了時に state.json をアトミック書き込みで更新する |
| UC-13 | 画像自動取得 | OpenClaw | Wikimedia Commons から著者ポートレート・イラストを取得・検証・保存する |
| UC-14 | 手動復旧 | 管理者 | `failed` 状態の作品を確認し、state.json を修正して再開する |
| UC-15 | サイト閲覧 | 読者 | 公開された作品・著者ページを閲覧する |

---

## 3. ユースケース全体関係図

```mermaid
graph TB
    subgraph ACTORS["アクター"]
        CRON([cron])
        OC([OpenClaw])
        LLLM([ローカル LLM])
        CODEX([Codex CLI])
        GH([GitHub Pages])
        WIKI([Wikimedia Commons])
        ADMIN([管理者])
        READER([読者])
    end

    subgraph PIPELINE["日次パイプライン"]
        UC01["UC-01\n日次パイプライン起動"]
        UC02["UC-02\nロック取得・状態復旧・初期化"]
        UC03["UC-03\n原文テキスト取得"]
        UC04["UC-04\nテキスト前処理"]
        UC05["UC-05\nテキスト翻訳"]
        UC06["UC-06\n翻訳品質チェック"]
        UC07["UC-07\n同一実行内リトライ"]
        UC08["UC-08\n翻訳失敗確定処理"]
        UC09["UC-09\nサイト生成・公開"]
        UC10["UC-10\nRSS・サイトマップ更新"]
        UC11["UC-11\nGitHub コミット・プッシュ"]
        UC12["UC-12\n状態保存"]
    end

    subgraph SUPPORT["補助処理"]
        UC13["UC-13\n画像自動取得"]
        UC14["UC-14\n手動復旧"]
        UC15["UC-15\nサイト閲覧"]
    end

    CRON -->|起動| UC01
    UC01 --> OC
    OC --> UC02
    OC --> UC03
    OC --> UC04
    OC --> UC09
    OC --> UC10
    OC --> UC11
    OC --> UC12
    OC --> UC13

    LLLM --> UC04
    LLLM --> UC06
    OC --> UC05
    CODEX --> UC05
    UC04 --> UC05
    UC05 --> UC06
    UC06 -->|不合格| UC07
    UC07 -->|上限超過| UC08
    UC09 --> UC10
    UC10 --> UC11

    GH --> UC11
    WIKI --> UC13
    ADMIN --> UC14
    READER --> UC15
    GH --> UC15
```

---

## 4. 日次パイプライン 詳細フロー

```mermaid
flowchart TD
    START([cron 03:00 起動]) --> LOCK{state.lock\n存在？}

    LOCK -->|あり| LOCK_CHECK{pid 生存中\nかつ heartbeat\n6時間以内？}
    LOCK_CHECK -->|YES| ABORT([今回の実行を中止])
    LOCK_CHECK -->|NO| STALE[lock を .stale に退避]
    STALE --> LOCK_ACQ

    LOCK -->|なし| LOCK_ACQ[state.lock 取得\nrun_id / pid 記録]

    LOCK_ACQ --> STATE_EXISTS{state.json\n存在？}
    STATE_EXISTS -->|NO| INIT_STATE[state.json 初期生成\n最小 work_id /\ncurrent_stage=idle]
    INIT_STATE --> STATE_READ
    STATE_EXISTS -->|YES| STATE_READ[state.json 読み込み]

    STATE_READ --> STATUS_CHECK{current_work_status}

    STATUS_CHECK -->|failed| NOTIFY_FAILED([管理者通知\n処理停止])
    STATUS_CHECK -->|paused / exhausted| END_DAY
    STATUS_CHECK -->|complete| LOAD_NEXT{works_master に\n次の未完了作品あり？}
    STATUS_CHECK -->|active| STAGE_CHECK{current_stage}

    LOAD_NEXT -->|YES\n次作品を設定\ncurrent_stage=idle| STAGE_CHECK
    LOAD_NEXT -->|NO\n全作品完了または\n恒久的取得不能| SET_EXHAUSTED[current_work_status = exhausted\nstate.json 保存]
    SET_EXHAUSTED --> END_DAY

    STAGE_CHECK -->|idle / preprocess| FETCH
    STAGE_CHECK -->|translate\nraw source から\nセグメント再切り出し| TRANSLATE
    STAGE_CHECK -->|quality_check\nraw source から\nセグメント再切り出し| TRANSLATE
    STAGE_CHECK -->|publish| PUBLISH

    FETCH["🔵 UC-03 Fetcher\nsource_url から原文取得"]
    FETCH --> FETCH_OK{取得成功？}
    FETCH_OK -->|NO| LOG_FETCH[エラーログ記録\nstage=preprocess]
    LOG_FETCH --> END_DAY

    FETCH_OK -->|YES| PREPROCESS

    PREPROCESS["🟣 UC-04 Preprocessor\n段落分割・クリーニング\nセグメント生成\n（ローカル LLM）"]
    PREPROCESS --> SEG_LOOP

    SEG_LOOP{daily_max_chars\n以内のセグメントあり？}
    SEG_LOOP -->|YES| TRANSLATE

    TRANSLATE["🟡 UC-05 Translator\nプロンプト展開\nCodex CLI 実行\n→ JSON 出力"]
    TRANSLATE --> TRANS_OK{成功 かつ\nJSON 正常？}

    TRANS_OK -->|NO| RETRY_COUNT{translate_retry_count\n< 2 ？}
    RETRY_COUNT -->|YES| INC_RETRY[translate_retry_count++\nheartbeat 更新]
    INC_RETRY --> TRANSLATE
    RETRY_COUNT -->|NO| FAIL_DAY[consecutive_fail_days++\n【翻訳未完】を付記]

    FAIL_DAY --> FAIL_CHECK{consecutive_fail_days\n≥ 2 ？}
    FAIL_CHECK -->|YES| SET_FAILED[current_work_status = failed\nstate.json 保存]
    SET_FAILED --> END_DAY
    FAIL_CHECK -->|NO| SAVE_RETRY[state.json 保存\nstage = translate]
    SAVE_RETRY --> END_DAY

    TRANS_OK -->|YES| QA

    QA["🟠 UC-06 QualityChecker\n品質チェック\n（ローカル LLM）\n→ JSON: status/score/issues"]
    QA --> QA_PASS{status == pass？}

    QA_PASS -->|NO| RETRY_COUNT
    QA_PASS -->|YES| RESET_RETRY[translate_retry_count=0\nconsecutive_fail_days=0]

    RESET_RETRY --> PUBLISH

    PUBLISH["🟢 UC-09 Publisher\n/tmp_build に HTML 生成\nindex / work / part / author"]
    PUBLISH --> PUB_OK{生成成功？}

    PUB_OK -->|NO| PUB_RETRY{publish_retry_count\n< 3 ？}
    PUB_RETRY -->|YES| INC_PUB[publish_retry_count++\nstage=publish]
    INC_PUB --> END_DAY
    PUB_RETRY -->|NO| PUB_FAILED[pub 失敗確定\nログ記録]
    PUB_FAILED --> END_DAY

    PUB_OK -->|YES| SAVE_HEAD[pre_publish_head を記録]
    SAVE_HEAD --> COPY[tmp_build → 本番パスへ仮反映]
    COPY --> RSS_SITEMAP

    RSS_SITEMAP["🔵 UC-10 RSS・サイトマップ更新\nrss.xml / sitemap.xml 再生成"]
    RSS_SITEMAP --> RSS_OK{更新結果}
    RSS_OK -->|成功| COMMIT
    RSS_OK -->|補助成果物のみ失敗| LOG_RSS[警告ログ記録\ncommit 継続]
    LOG_RSS --> COMMIT
    RSS_OK -->|致命的エラー| RSS_FATAL[publish failure として扱う\nstage=publish / リトライ]
    RSS_FATAL --> END_DAY

    COMMIT["⚫ UC-11 GitHub コミット・プッシュ\ngit add / commit / push"]
    COMMIT --> COMMIT_OK{成功？}
    COMMIT_OK -->|NO| ROLLBACK[作業ツリーとローカル履歴を\npre_publish_head に復元\ntmp_build 破棄\nstate は進めない]
    ROLLBACK --> LOG_COMMIT[エラーログ\n次回リトライ]
    LOG_COMMIT --> END_DAY

    COMMIT_OK -->|YES| CLEAN_TMP[tmp_build 破棄]
    CLEAN_TMP --> ADV_STATE[current_part 進める\nstage = idle]
    ADV_STATE --> SEG_LOOP

    SEG_LOOP -->|NO\n今日の上限到達| END_DAY

    END_DAY[state.json 保存\nstate.lock 削除\nログ保存]
    END_DAY --> DONE([実行完了])
```

---

## 5. 翻訳・リトライ シーケンス図

```mermaid
sequenceDiagram
    autonumber
    participant OC as OpenClaw
    participant LLLM as ローカル LLM
    participant CODEX as Codex CLI
    participant STATE as state.json

    OC->>STATE: current_segment_id・stage 読み込み
    OC->>LLLM: セグメントテキスト送信（前処理）
    LLLM-->>OC: 段落分割・クリーニング済みテキスト

    Note over OC,STATE: translate_retry_count は再翻訳回数のみを表す<br/>初回試行は含まない

    loop 総試行は最大3回（初回1回 + 再翻訳2回）
        OC->>OC: translate_prompt.md テンプレート展開
        OC->>CODEX: 展開済みプロンプト（stdin）
        CODEX-->>OC: JSON { translated_text, summary, keywords }

        alt JSON 形式不正 or 実行失敗
            OC->>STATE: translate_retry_count++, stage=translate
            OC->>OC: リトライ待機
        else JSON 正常
            OC->>LLLM: 原文 + 翻訳文 送信（品質チェック）
            LLLM-->>OC: JSON { status, score, issues[] }

            alt status == fail
                OC->>STATE: translate_retry_count++
                OC->>OC: リトライ
            else status == pass
                OC->>STATE: translate_retry_count=0, consecutive_fail_days=0
                OC->>OC: Publisher へ進む
                break
            end
        end
    end

    alt 同一実行内で解消しない（translate_retry_count == 2）
        OC->>STATE: consecutive_fail_days++, stage=translate
        OC->>OC: 【翻訳未完】をタイトルに付記

        alt consecutive_fail_days >= 2
            OC->>STATE: current_work_status = failed
            OC->>OC: 処理停止・管理者通知
        else consecutive_fail_days == 1
            OC->>OC: 翌日の cron 実行で再挑戦
        end
    end
```

---

## 6. 作品ステータス 状態遷移図

```mermaid
stateDiagram-v2
    [*] --> active : 作品登録・翻訳開始\n（初期化 or 次作品移行）

    active --> active : パート公開成功\ncurrent_part を進める

    active --> failed : consecutive_fail_days ≥ 2\n同一セグメント2日連続翻訳失敗

    active --> paused : 管理者が state.json を\n手動変更して一時停止

    active --> complete : 全パート公開完了\nタイトルから【翻訳中】を除去

    complete --> active : 次の未完了作品あり\n（LOAD_NEXT 成功）

    complete --> exhausted : 次の未完了作品なし\n（LOAD_NEXT 失敗 / キュー枯渇）

    active --> exhausted : 恒久的取得不能\n（source が実質空と判定）

    paused --> active : 管理者が state.json を\n手動変更して再開

    failed --> active : 管理者が state.json を\n修正して再開

    exhausted --> active : works_master に新規作品追加後\n管理者が手動で再開

    exhausted --> [*] : 運用終了
```

---

## 7. 実行ステージ 状態遷移図（current_stage）

```mermaid
stateDiagram-v2
    [*] --> idle : 初期状態 / 前回パート完了

    idle --> preprocess : Fetcher・Preprocessor 開始

    preprocess --> translate : 前処理完了\nセグメント生成

    preprocess --> idle : 前処理失敗\nログ記録・翌日再試行

    translate --> quality_check : 翻訳成功\nJSON 取得

    translate --> translate : 同一実行内リトライ\n(translate_retry_count < 2)

    translate --> idle : リトライ上限超過\n翌日再挑戦へ

    quality_check --> publish : 品質チェック 合格

    quality_check --> translate : 品質チェック 不合格\nリトライ

    publish --> idle : 公開成功\ncurrent_part 進める

    publish --> publish : publish_retry_count++\n次回実行でリトライ\n(最大3回)

    publish --> idle : publish 失敗確定\nログ記録

    note right of translate
        translate_retry_count で管理
        上限: 同一実行内2回
    end note

    note right of publish
        publish_retry_count で管理
        上限: 3回
    end note
```

---

## 8. 画像自動取得フロー（UC-13）

> **注意**: UC-13 は日次翻訳パイプライン（UC-01〜UC-12）とは**分離した補助ジョブ**として実行する。
> 実行タイミング：`works_master.json` への新規作品・著者追加時、または手動トリガー時。
> 画像が未取得でも翻訳公開は妨げられない（未取得の場合は画像枠を非表示）。

```mermaid
flowchart TD
    START([補助ジョブ起動\nworks_master 更新検出\nまたは手動トリガー]) --> SEARCH

    SEARCH["AI エージェント\nWikimedia Commons 検索\n著者名 or 作品名でクエリ"]
    SEARCH --> FOUND{ファイルページ\n発見？}

    FOUND -->|NO| SKIP([画像枠を非表示\n処理終了])

    FOUND -->|YES| CHECK_LICENSE{権利表示確認\nPublic domain ?\nCC0 ?\nPublic Domain Mark ?}

    CHECK_LICENSE -->|該当なし\nCC BY / fair use 等| SKIP

    CHECK_LICENSE -->|合格| DOWNLOAD[ファイル URL から\nダウンロード]

    DOWNLOAD --> SAVE_IMG[/assets/images/authors/ または\n/assets/images/illustrations/ に保存]
    SAVE_IMG --> SAVE_META[YAML sidecar 生成\nsource_page_url / file_url\nauthor / rights_label / year\nrights_verified_at]

    SAVE_META --> DONE([画像取得完了])
```

---

## 9. ユースケース別 前提条件・成功条件一覧

| UC番号 | 前提条件 | 成功条件 | 例外・代替フロー |
|--------|---------|---------|----------------|
| UC-01 | cron が設定済み | OpenClaw プロセスが起動する | cron 自体の障害は運用者が対処 |
| UC-02 | `/data/works_master.json` が存在する | ロック取得成功・state.json 読み込みまたは初期生成完了 | stale lock の場合は退避後取得。`state.json` 欠如時は最小 `work_id` で初期化 |
| UC-03 | state.json で current_work_status=active かつ works_master.json に current_work_id が存在し pd_verified=true | テキストデータを取得しローカルに保存 | 取得失敗時はログ記録し翌日再試行 |
| UC-04 | 原文テキスト取得済み | daily_max_chars 以内のセグメント列を生成 | 前処理失敗時はログ記録し翌日再試行 |
| UC-05 | セグメント生成済み | JSON `{ translated_text, summary, keywords }` を正常取得 | 失敗時は同一実行内最大2回リトライ |
| UC-06 | 翻訳 JSON 取得済み | `status == pass` を返す | 不合格時は UC-07 へ |
| UC-07 | translate_retry_count < 2 | 再翻訳で品質合格 | 上限到達時は consecutive_fail_days++ |
| UC-08 | consecutive_fail_days >= 2 | `current_work_status` を `failed` に設定し停止 | 管理者が UC-14 で手動復旧 |
| UC-09 | **新規実行時**: 品質チェック合格済み / **publish 再開時**: 前回翻訳済みセグメントが存在し `current_stage = publish` | /tmp_build に必須成果物を全生成 | 失敗時は tmp_build 破棄・最大3回リトライ |
| UC-10 | Publisher 成功 | rss.xml / sitemap.xml 更新完了 | 補助成果物のみ失敗ならログ記録して継続。致命的エラー時は publish failure としてリトライ |
| UC-11 | `pre_publish_head` 記録済み・本番パスへの仮反映完了 | git push 成功・GitHub Pages 更新 | 失敗時は `pre_publish_head` に復元し翌日リトライ |
| UC-12 | 各ステージ完了 | state.json アトミック書き込み成功 | 書き込み失敗時はパイプライン停止 |
| UC-13 | `works_master.json` に新規作品・著者が追加済み（日次翻訳パイプラインとは独立した補助ジョブ） | PD/CC0/PDM の画像を保存し YAML sidecar 生成 | 該当画像なしの場合は画像枠を非表示。ジョブ失敗は翻訳公開に影響しない |
| UC-14 | current_work_status == failed | state.json を修正し active に戻す | 管理者による手動操作 |
| UC-15 | GitHub Pages にページが公開済み | 読者がブラウザでページを閲覧できる | - |
