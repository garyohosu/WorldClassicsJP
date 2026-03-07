# 状態遷移ルール

## 1. current_stage

### idle
待機状態。新規開始またはパート公開成功直後。

### preprocess
原文取得・整形中。中断したら raw source から再開準備。

### translate
翻訳中。失敗時は retry を増やし、同一セグメント再挑戦。

### quality_check
品質確認中。不合格なら translate に戻る。

### publish
HTML 生成・反映・git push。成功するまで current_part を進めない。

---

## 2. 翻訳失敗時

### 同一実行内
- translate_retry_count を増加
- current_stage = translate 維持
- current_part は進めない

### 当日解消しない
- consecutive_fail_days++
- current_segment_id を維持
- タイトルに【翻訳未完】を付記可能
- 翌日同一セグメント再試行

### 2日連続失敗
- current_work_status = failed
- 管理者対応待ち

---

## 3. 公開失敗時

### build failure
- publish_retry_count++
- current_stage = publish
- current_part は進めない

### commit/push failure
- pre_publish_head（state.json の `pre_publish_head` SHA）へ rollback
- tmp_build 破棄
- state 進行項目は更新しない
- rollback 完了後に `pre_publish_head` を `""` にリセット

### retry 上限超過（publish_retry_count >= 3）
- current_work_status = failed
- 管理者対応待ち（SPEC §17.3 参照）

---

## 4. exhausted
以下のみ exhausted とする。

1. 次作品候補が無い  
2. 原文が恒久的に取得不能

一時ネットワーク障害では exhausted にしない。

---

## 5. 次作品移行
v1 推奨仕様では、現作品 complete 後に next_work_id を次へ進める。  
複数作品の状態照会を works_master.json に求めない。
