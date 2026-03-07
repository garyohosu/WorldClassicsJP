# 追加で入れるべき設計改善

この章は、既出の不整合修正に加えて、運用事故を防ぐために入れる改善点をまとめたもの。

## 1. セグメント再構築の決定性
中断復帰時は前処理キャッシュに依存せず、**raw source から同じ規則で再切り出し**すること。  
これにより `current_segment_id` が安定し、途中再開が壊れにくくなる。

---

## 2. state.json のアトミック更新
必ず以下で更新する。

1. state.json.tmp に書く  
2. JSON バリデーション  
3. rename で state.json に置換  

途中で止まっても壊れた state.json を残さない。

---

## 3. lock + heartbeat の厳密化
`state.lock` に以下を記録する。

- run_id
- pid
- started_at
- heartbeat_at

各ステージ移行で heartbeat を更新し、stale 判定を明確にする。

---

## 4. publish rollback の明文化
`pre_publish_head` を必ず保存し、push 失敗時は以下を行う。

- 本番差分を戻す
- ローカル履歴を戻す
- tmp_build を破棄
- state を進めない

---

## 5. idempotent pipeline
同一日に再実行しても壊れないようにする。

- current_part を重複で進めない
- 既存成果物の上書き条件を明確にする
- ログ・状態更新は再実行に耐える形にする

---

## 6. fetch failure と exhausted の分離
一時取得失敗は exhausted にしない。  
exhausted は「材料が尽きた」または「恒久的取得不能」のみ。

---

## 7. 文書・ファイル名の OS 非依存化
- 相対パスのみ
- 小文字ファイル名統一
- バックスラッシュ依存を避ける

---

## 8. 状態の責務分離
- works_master.json: 作品メタデータ
- state.json: 現在ジョブ状態
- 将来必要なら queue_state.json: 複数作品キュー状態

---

## 9. optional 成果物の分類
必須成果物:
- index.html
- work page
- part page
- author page

補助成果物:
- rss.xml
- sitemap.xml

補助成果物だけの失敗では publish 全体を失敗扱いにしない。

---

## 10. テストの先行整備
コードより先に以下のテスト観点を固定する。

- state 遷移
- retry 増減
- rollback
- stale lock
- path/case 問題
