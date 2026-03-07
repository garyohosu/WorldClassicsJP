# 設計不整合の修正方針

## 1. works_master.json 必須項目不一致
### 問題
QandA.md では `work_slug` が必須から漏れているが、SPEC.md では必須である。

### 修正
QandA.md の必須項目に `work_slug` を追加する。

### 理由
作品 URL 生成に必須であり、Publisher が依存するため。

---

## 2. 次作品選択条件とデータモデル不一致
### 問題
SPEC.md / sequence.md では `complete / failed / paused 以外` を条件にしているが、
works_master.json に status 項目が定義されていない。

### 修正
- works_master.json は状態を持たない
- 作品状態は state.json で管理する
- 複数作品管理が必要なら queue_state 系の別管理を導入する

### 理由
メタデータと実行状態を混ぜると破綻しやすい。

---

## 3. 翻訳失敗時の「状態を更新しない」矛盾
### 問題
SPEC.md では「状態を更新しない」としつつ、current_stage や retry を更新している。

### 修正
「進行状態を進めない」に表現を修正する。

更新しない:
- current_part
- next_work_id
- current_work_status の成功側進行

更新する:
- current_stage
- translate_retry_count
- consecutive_fail_days
- ログ

---

## 4. sequence.md の絶対パスリンク
### 問題
`C:/PROJECT/...` に依存している。

### 修正
相対パスリンクに置換する。

例:
- `./SPEC.md`
- `./usecase.md`

---

## 5. USECASE.md / usecase.md の表記ゆれ
### 問題
Linux や CI でケースセンシティブ問題が起きる。

### 修正
ファイル名表記を `usecase.md` に統一する。

---

## 6. RSS / sitemap エラー分岐欠落
### 問題
usecase.md の説明とフロー図が食い違っている。

### 修正
`RSS_SITEMAP_OK?` の分岐を追加する。

- 失敗: ログ記録、commit 継続
- 致命的エラー: publish failure とする

---

## 7. ドキュメント修正対象
- QandA.md
- SPEC.md
- sequence.md
- UI.md
- usecase.md
