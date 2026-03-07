# 実装計画

## Phase 1: 文書修正 ✅（完了: 2026-03-07）
1. [x] QandA.md に `work_slug` を追加
2. [x] sequence.md の絶対パスを相対パス化
3. [x] UI.md の `USECASE.md` 表記を `usecase.md` に統一
4. [x] usecase.md に RSS/sitemap 失敗分岐を追加
5. [x] SPEC.md の「状態を更新しない」を「進行状態を進めない」に修正

---

## Phase 2: スキーマとバリデーション
1. works_master.json schema を定義
2. state.json schema を定義
3. `work_slug` 欠落時に即失敗するバリデーションを追加

---

## Phase 3: パイプライン実装修正
1. 次作品選択ロジックを state 主体に修正
2. translate retry / consecutive fail 処理を明確化
3. publish rollback を実装
4. RSS/sitemap を optional 扱いに修正

---

## Phase 4: テスト
1. schema validation test
2. translate failure state test
3. publish rollback test
4. stale lock recovery test
5. Linux path/case test

---

## Phase 5: 仕上げ
1. README 更新
2. 変更履歴を残す
3. 運用手順を簡潔に整理
