# sequence.md
WorldClassicsJP シーケンス設計

バージョン: 1.0.1
最終更新日: 2026-03-07
対応 SPEC: v1.5.1
対応 UseCase: v1.2.0

---

## 1. 目的

本書は、[SPEC.md](./SPEC.md) と [usecase.md](./usecase.md) をもとに、主要処理を Mermaid のシーケンス図として具体化したものである。

- 日次パイプライン正常系
- ロック復旧・初期化
- 翻訳と品質チェックの再試行
- 公開とロールバック
- 次作品移行と exhausted 遷移
- 画像取得の補助ジョブ

---

## 2. SQ-01 日次パイプライン正常系

```mermaid
sequenceDiagram
    autonumber
    actor CRON as cron
    participant OC as OpenClaw
    participant LOCK as state.lock
    participant STATE as state.json
    participant WM as works_master.json
    participant SRC as Source Site
    participant LLLM as ローカル LLM
    participant CODEX as Codex CLI
    participant BUILD as /tmp_build
    participant GIT as Git
    participant GH as GitHub Pages
    participant LOG as /logs/YYYY/MM/DD/run_id.json

    CRON->>OC: 03:00 に日次ジョブ起動
    OC->>LOCK: 排他的ロック取得
    LOCK-->>OC: run_id / pid / heartbeat_at
    OC->>STATE: state.json 読み込み
    STATE-->>OC: current_work_status=active, current_stage=idle
    OC->>WM: current_work_id の作品情報を参照
    WM-->>OC: source_url / length_class / slug 情報

    OC->>SRC: 原文 TXT / text_url を取得
    SRC-->>OC: raw source text
    OC->>LLLM: 前処理依頼（段落分割・クリーニング）
    LLLM-->>OC: cleaned text + segment list

    loop daily_max_chars 内の各セグメント
        OC->>CODEX: translate_prompt 展開済み本文を stdin 渡し
        CODEX-->>OC: JSON { translated_text, summary, keywords }
        OC->>LLLM: translated_text の品質チェック
        LLLM-->>OC: JSON { status, score, issues[] }
        OC->>STATE: translate_retry_count=0, consecutive_fail_days=0
    end

    OC->>BUILD: index / work / part / author page を生成
    BUILD-->>OC: 必須成果物生成完了
    OC->>BUILD: rss.xml / sitemap.xml を /tmp_build に生成
    OC->>GIT: pre_publish_head を state.json に記録
    OC->>GIT: /tmp_build を本番パスへ仮反映
    OC->>GIT: git add / commit / push
    GIT->>GH: 更新を反映
    GH-->>OC: push accepted

    OC->>STATE: current_part 更新, current_stage=idle, publish_retry_count=0
    OC->>LOG: 実行ログ保存
    OC->>LOCK: state.lock 削除
```

---

## 3. SQ-02 ロック復旧・初期化

```mermaid
sequenceDiagram
    autonumber
    actor CRON as cron
    participant OC as OpenClaw
    participant LOCK as state.lock
    participant STATE as state.json
    participant WM as works_master.json
    participant LOG as /logs/YYYY/MM/DD/run_id.json
    participant ADMIN as 管理者

    CRON->>OC: 日次起動
    OC->>LOCK: state.lock の有無確認

    alt lock が存在しない
        OC->>LOCK: 新規ロック作成
    else lock が存在する
        OC->>LOCK: pid / heartbeat_at を確認
        alt pid 生存中 かつ heartbeat が 6 時間以内
            OC->>LOG: 二重起動として記録
            OC-->>CRON: 今回の実行を中止
        else stale lock
            OC->>LOCK: state.lock.stale.<run_id> に退避
            OC->>LOCK: 新規ロック作成
        end
    end

    OC->>STATE: state.json の存在確認
    alt state.json が存在しない
        OC->>WM: 最小 work_id を取得
        WM-->>OC: min work_id
        OC->>STATE: 初期状態を自動生成
        Note over OC,STATE: next_work_id = current_work_id = min work_id<br/>current_stage = idle<br/>current_work_status = active
    else state.json が存在する
        OC->>STATE: 現在状態を読み込み
    end

    OC->>STATE: current_work_status を判定
    alt current_work_status = failed
        OC->>LOG: failed 状態を記録
        OC->>ADMIN: 手動復旧が必要
    else current_work_status = paused or exhausted
        OC->>LOG: 当日処理なしで終了
    else current_work_status = active or complete
        OC->>LOG: 通常フローへ継続
    end
```

---

## 4. SQ-03 翻訳・品質チェック・翌日再挑戦

```mermaid
sequenceDiagram
    autonumber
    participant OC as OpenClaw
    participant STATE as state.json
    participant CODEX as Codex CLI
    participant LLLM as ローカル LLM
    participant LOG as /logs/YYYY/MM/DD/run_id.json
    participant ADMIN as 管理者

    OC->>STATE: current_segment_id を読み込み
    OC->>STATE: current_stage = translate
    Note over OC,STATE: translate_retry_count は再翻訳回数のみ<br/>初回試行は含まない

    loop 総試行は最大 3 回（初回 1 回 + 再翻訳 2 回）
        OC->>CODEX: 翻訳要求
        alt Codex 実行失敗 または JSON 形式不正
            OC->>STATE: translate_retry_count++
            OC->>LOG: translate error を記録
        else 翻訳 JSON 正常
            CODEX-->>OC: translated_text / summary / keywords
            OC->>LLLM: 品質チェック要求
            LLLM-->>OC: status / score / issues[]
            alt status == pass
                OC->>STATE: translate_retry_count=0
                OC->>STATE: consecutive_fail_days=0
                Note over OC,STATE: Publisher へ進む
            else status == fail
                OC->>STATE: translate_retry_count++
                OC->>LOG: QA fail を記録
            end
        end
    end

    alt 同一実行内で解消しない
        OC->>STATE: consecutive_fail_days++
        OC->>STATE: current_stage = translate
        OC->>LOG: タイトルに【翻訳未完】を付記して終了
        alt consecutive_fail_days >= 2
            OC->>STATE: current_work_status = failed
            OC->>ADMIN: 手動復旧を通知
        else consecutive_fail_days == 1
            Note over OC,STATE: 翌日の cron で同一 segment を再試行
        end
    else 同一実行内で成功
        OC->>STATE: current_stage = quality_check
        OC->>STATE: current_stage = publish
    end
```

---

## 5. SQ-04 公開・Git 反映・ロールバック

```mermaid
sequenceDiagram
    autonumber
    participant OC as OpenClaw
    participant BUILD as /tmp_build
    participant STATE as state.json
    participant GIT as Git
    participant GH as GitHub Pages
    participant LOG as /logs/YYYY/MM/DD/run_id.json

    OC->>STATE: current_stage = publish
    OC->>BUILD: 必須成果物を生成

    alt build 失敗
        OC->>STATE: publish_retry_count++
        OC->>LOG: publish generation error
        Note over OC,STATE: 次回実行で同一 part を再試行
    else build 成功
        BUILD-->>OC: index / work / part / author page 完了
        OC->>BUILD: rss.xml / sitemap.xml を /tmp_build に生成
        OC->>GIT: pre_publish_head を state.json に記録
        OC->>GIT: /tmp_build を本番パスへ仮反映
        OC->>GIT: git add / commit / push

        alt commit/push 成功
            GIT->>GH: 更新反映
            GH-->>OC: 公開成功
            OC->>STATE: publish_retry_count=0
            OC->>STATE: current_part を進める
            OC->>STATE: current_stage = idle
            OC->>BUILD: /tmp_build を破棄
        else commit/push 失敗
            OC->>GIT: 作業ツリーとローカル履歴を pre_publish_head に復元
            OC->>BUILD: /tmp_build を破棄
            OC->>LOG: git failure を記録
            Note over OC,STATE: state.json は進めない
        end
    end
```

---

## 6. SQ-05 次作品移行・exhausted 遷移

```mermaid
sequenceDiagram
    autonumber
    participant OC as OpenClaw
    participant STATE as state.json
    participant WM as works_master.json
    participant LOG as /logs/YYYY/MM/DD/run_id.json

    OC->>STATE: current_work_status = complete を確認
    OC->>STATE: 次作品候補を判定（current_work_id より大きい work_id を走査）
    OC->>WM: 候補 work_id のメタデータを取得
    Note over OC,STATE: 条件: pd_verified = true / work_id 昇順<br/>実行可否判定は state.json（v1）または queue_state.json（複数キュー）

    alt 次作品が見つかる
        WM-->>OC: next work_id / slug / source_url
        OC->>STATE: next_work_id = 見つかった work_id
        OC->>STATE: current_work_id = 見つかった work_id
        OC->>STATE: current_part = 1
        OC->>STATE: current_segment_id = ""
        OC->>STATE: current_stage = idle
        OC->>STATE: current_work_status = active
        OC->>LOG: 次作品へ移行
    else 次作品が見つからない
        OC->>STATE: current_work_status = exhausted
        OC->>STATE: current_stage = idle
        OC->>LOG: キュー枯渇として終了
    end
```

---

## 7. SQ-06 画像取得補助ジョブ

> このシーケンスは日次翻訳パイプラインとは分離した補助ジョブを表す。

```mermaid
sequenceDiagram
    autonumber
    participant OC as OpenClaw
    participant WM as works_master.json
    participant WIKI as Wikimedia Commons
    participant FS as assets/images + YAML sidecar
    participant LOG as /logs/YYYY/MM/DD/run_id.json

    OC->>WM: 新規作品 / 著者追加を検出
    Note over OC,WM: works_master.hash との SHA-256 比較で変更を検出<br/>差異がある場合のみ補助ジョブを実行し、完了後にハッシュを更新
    WM-->>OC: author_name / title / slug
    OC->>WIKI: 著者名または作品名で検索

    alt 該当画像なし
        WIKI-->>OC: no result
        OC->>LOG: 画像未取得を記録
        Note over OC,FS: UI では画像枠を非表示
    else 候補あり
        WIKI-->>OC: file page / file url / rights label
        alt rights_label が Public domain / CC0 / Public Domain Mark
            OC->>WIKI: 画像ファイルを取得
            WIKI-->>OC: binary image
            OC->>FS: /assets/images/... に保存
            OC->>FS: YAML sidecar を保存
            OC->>LOG: 画像取得成功
        else 非許可ライセンス
            OC->>LOG: 画像を不採用として記録
            Note over OC,FS: UI では画像枠を非表示
        end
    end
```

---

## 8. メモ

- `state.lock`、`/tmp_build`、`pre_publish_head` は論理的な参与者として表現している。
- `pre_publish_head` は `state.json` の `pre_publish_head` フィールドに 40 桁 SHA として保存する。
- `rss.xml` と `sitemap.xml` は補助成果物であり、必須 HTML 成果物の `/tmp_build` への生成後・本番パスへの仮反映前に `/tmp_build` 内に生成する。仮反映で HTML 成果物と一緒にコピーされる。
- 本書作成時点では、シーケンス図化のために追加の Q&A は不要だった。
