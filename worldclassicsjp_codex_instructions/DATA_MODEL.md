# データモデル定義

## 1. works_master.json

作品メタデータのマスタ。  
原則として人手または登録処理で生成し、パイプライン実行中に状態更新しない。

### 必須項目
- work_id: int
- work_slug: str
- title: str
- title_ja: str
- author_name: str
- author_name_ja: str
- author_slug: str
- source_url: str
- source_type: "txt" | "text_url"
- death_year: int
- pd_verified: bool
- length_class: "short" | "medium" | "long"

### 例
```json
{
  "work_id": 1,
  "work_slug": "the-time-machine",
  "title": "The Time Machine",
  "title_ja": "タイム・マシン",
  "author_name": "H. G. Wells",
  "author_name_ja": "H・G・ウェルズ",
  "author_slug": "h-g-wells",
  "source_url": "https://example.com/time_machine.txt",
  "source_type": "text_url",
  "death_year": 1946,
  "pd_verified": true,
  "length_class": "medium"
}
```

---

## 2. state.json

現在のジョブ状態を表す唯一の実行状態ファイル。

### 必須項目
- next_work_id
- current_work_id
- current_part
- current_segment_id
- current_stage
- current_work_status
- last_processed_date
- last_run_id
- translate_retry_count
- consecutive_fail_days
- publish_retry_count
- pre_publish_head

### 許容値

#### current_stage
- idle
- preprocess
- translate
- quality_check
- publish

#### current_work_status
- active
- paused
- complete
- exhausted
- failed

### 例
```json
{
  "next_work_id": 2,
  "current_work_id": 1,
  "current_part": 4,
  "current_segment_id": "chapter-04-part-01",
  "current_stage": "translate",
  "current_work_status": "active",
  "last_processed_date": "2026-03-06",
  "last_run_id": "20260306T030000Z-18432",
  "translate_retry_count": 1,
  "consecutive_fail_days": 0,
  "publish_retry_count": 0,
  "pre_publish_head": ""
}
```

---

## 3. 補足

### state.json に持たせるもの
- 実行中の進行
- 失敗回数
- 再開位置
- publish 直前の git HEAD SHA（`pre_publish_head`）

### works_master.json に持たせないもの
- complete / failed / paused などの実行状態
- retry 回数
- その日だけの一時的状態

---

## 4. 補助ファイル

### pre_publish_head（state.json 内フィールド）

| 項目 | 内容 |
|------|------|
| 型 | str（40桁の git SHA、または空文字列 `""`） |
| 書き込みタイミング | `/tmp_build` を本番パスへ仮反映する直前（`git rev-parse HEAD` で取得） |
| リセットタイミング | publish 成功後・ロールバック完了後に `""` へ |
| ロールバック時の使用 | `git reset --hard <pre_publish_head>` で本番パスとローカル履歴を復元 |

### /data/works_master.hash

| 項目 | 内容 |
|------|------|
| 内容 | `works_master.json` の SHA-256 ハッシュ値（1行テキスト） |
| 用途 | 画像取得補助ジョブの差分検出（§22.1 参照） |
| 更新タイミング | 補助ジョブ処理完了後・`works_master.json` 更新後 |
| 強制再実行 | ファイルを削除すると次回起動時に補助ジョブが実行される |
