# Changelog

## 2026-03-07（レビュー修正: SPEC v1.5.1）

- `SPEC.md`: バージョンを v1.5.1 に更新、最終更新日を修正
- `SPEC.md` §10: `config.yaml` 必須フィールドに `daily_max_chars` と `current_phase` を追加（フェーズ管理の明確化）
- `SPEC.md` §17.3: `pre_publish_head` の保存仕様を明定（`state.json` の `pre_publish_head` フィールドに 40 桁 SHA を記録）
- `SPEC.md` §17.3: `publish_retry_count >= 3` 時に `current_work_status = failed` へ遷移するルールを追加
- `SPEC.md` §18: `pre_publish_head` フィールドを `state.json` 必須項目に追加、JSON 例を更新
- `SPEC.md` §18: ステータス表の `complete` 行に「直後に LOAD_NEXT を実行し `active` へ遷移」を明記
- `SPEC.md` §22.1: 画像補助ジョブの新規追加検出方法（`works_master.hash` による SHA-256 比較）を定義
- `SPEC.md` §28: `rss.xml` / `sitemap.xml` の生成タイミングを「/tmp_build 生成後・仮反映前」に明確化
- `DATA_MODEL.md`: `state.json` 必須項目に `pre_publish_head` を追加、JSON 例を更新
- `DATA_MODEL.md`: §4「補助ファイル」セクションを新設（`pre_publish_head` フィールド仕様・`/data/works_master.hash` の用途を定義）
- `sequence.md`: バージョンを v1.0.1 に更新、対応 SPEC を v1.5.1 に更新
- `sequence.md` SQ-01: `rss.xml` / `sitemap.xml` の生成を仮反映前（`/tmp_build` 内）に移動
- `sequence.md` SQ-04: 同上（`rss.xml` / `sitemap.xml` を仮反映前に `/tmp_build` 内に生成）
- `sequence.md` SQ-04: `pre_publish_head` の記録先を `state.json` と明記
- `sequence.md` SQ-06: `works_master.hash` による SHA-256 差分検出の Note を追加
- `sequence.md` §8 メモ: `pre_publish_head` の保存先と `rss.xml` 生成タイミングの補足を追記
- `STATE_MACHINE.md` §3: `publish_retry_count >= 3` → `current_work_status = failed` のルールを追加
- `STATE_MACHINE.md` §3: rollback 後に `pre_publish_head` を `""` にリセットするルールを追記
- `IMPLEMENTATION_PLAN.md`: Phase 1 を完了済み（✅）としてマーク
- `README.md`: ドキュメント一覧をバージョン付きテーブルに更新

## 2026-03-07

- `QandA.md`: works_master 必須項目に `work_slug` を追加
- `SPEC.md`: 次作品選択を state 主体に修正（works_master はメタデータ専用に明確化）
- `SPEC.md`: 翻訳失敗時の文言を「状態を更新しない」から「進行状態を進めない」に修正
- `sequence.md`: `C:/PROJECT/...` の絶対パスリンクを相対パスへ修正
- `sequence.md`: 次作品候補の実行可否判定を state/queue 側に修正
- `UI.md`: `USECASE.md` 表記を `usecase.md` に統一
- `usecase.md`: RSS/sitemap の分岐を追加（成功/補助成果物失敗/致命的エラー）
- `usecase.md`: UC-03 と UC-10 の前提・例外条件を更新
- `README.md`: プロジェクト概要と v1 設計原則を新規追加
- `sequence.md`: 次作品移行の Note 対象を OC,STATE に修正（WM はメタデータ取得のみに限定）
- `SPEC.md` §16.2: exhausted 条件 1 を v1 と複数キューで明示的に分離
- `SPEC.md` §28: UC-10 致命的エラーの定義を §28.1 として追加

