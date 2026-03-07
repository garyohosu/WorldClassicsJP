# CODEX CLI 実装指示書

あなたは WorldClassicsJP プロジェクトを実装する Codex CLI エージェントである。  
以下の制約と修正方針に従って、**文書間の不整合を解消しながら安全に実装**せよ。

---

## 1. 最優先原則

1. 仕様の曖昧さを放置しない
2. works_master.json はメタデータ専用とする
3. state.json は実行状態の唯一のソースとする
4. 公開処理は常に `/tmp_build` を経由してアトミックに行う
5. 再実行で壊れない idempotent な実装にする
6. Linux / GitHub Pages / WSL2 で壊れないパス・ファイル名を使う
7. 文書修正が必要な場合は、実装と同時に Markdown も修正する

---

## 2. この実装で解消すべき不整合

必ず `DESIGN_FIXES.md` を参照し、以下を反映すること。

- QandA.md と SPEC.md の works_master 必須項目不一致
- 次作品選択条件とデータモデルの不整合
- 「状態を更新しない」と retry カウンタ更新の自己矛盾
- ローカル絶対パスリンク
- USECASE/usecase の表記ゆれ
- RSS / sitemap 失敗時の分岐欠落

---

## 3. データ責務

### works_master.json
- immutable に近い作品メタデータ
- 状態は持たない
- URL 生成に必要な `work_slug` は必須

### state.json
- 現在処理中作品
- current_stage
- current_work_status
- retry カウンタ
- publish リトライ
- 連続失敗日数

---

## 4. 実装修正ルール

### 4.1 works_master.json
必須項目は以下に統一する。

- work_id
- work_slug
- title
- title_ja
- author_name
- author_name_ja
- author_slug
- source_url
- source_type
- death_year
- pd_verified
- length_class

### 4.2 次作品選択
`works_master.json` には作品状態を持たせない。  
次作品選択は以下のいずれかで実装する。

- 単作品運用なら `state.json.current_work_status` を見る
- 複数作品キュー運用なら、別ファイル `queue_state.json` などを設ける
- 少なくとも **works_master.json 内の未定義 status を参照してはならない**

推奨: v1 は単作品直列運用とし、状態は `state.json` に集約する。

### 4.3 翻訳失敗時
「状態を更新しない」は以下の意味に限定する。

更新しないもの:
- current_part
- next_work_id
- 完了済み公開物の進行状態

更新するもの:
- current_stage
- translate_retry_count
- consecutive_fail_days
- ログ

### 4.4 公開失敗時
- `/tmp_build` を破棄
- 本番反映前なら本番無変更
- commit/push 失敗時は `pre_publish_head` にロールバック
- state.json の進行項目は進めない

### 4.5 RSS / sitemap
- 失敗しても必須成果物ではない
- ログ記録後、commit 継続可
- ただし build 全体が壊れる場合は publish failure とする

---

## 5. 追加で必ず入れる改善

`ADDITIONAL_IMPROVEMENTS.md` を反映すること。特に重要なのは次の 5 点。

1. セグメント再構築は raw source から deterministic に行う  
2. state.json の書き込みはアトミック更新  
3. state.lock に heartbeat を入れる  
4. Git rollback を設計どおり実装  
5. ファイル名とリンクは相対パス + 小文字統一

---

## 6. 実装手順

1. Markdown 文書を修正
2. データモデル定義を修正
3. 状態遷移ロジックを修正
4. publish rollback を実装
5. RSS/sitemap を optional 処理に修正
6. テストを追加
7. 再実行・中断復帰を確認

詳細は `IMPLEMENTATION_PLAN.md` を参照。

---

## 7. テスト観点

最低限、以下を自動テストまたは手順書で確認すること。

- work_slug 欠落時にバリデーションで失敗する
- 翻訳失敗時に current_part が進まない
- retry カウンタだけが更新される
- publish 失敗時に state が進まない
- commit/push 失敗時にロールバックされる
- RSS 失敗のみでは公開自体は継続できる
- stale lock の回収ができる
- Linux でリンク切れしない

---

## 8. 出力方針

Codex CLI は以下を優先して出力すること。

- 修正された Markdown
- スキーマ定義
- 実装コード
- テストコード
- 変更理由の短い要約

不要な長文説明は避け、変更差分が追える形で進めること。

---

## 9. 反映確認チェックリスト（運用用）

実装・文書修正後は、以下を `rg` などで検証してから完了判定すること。

- `QandA.md` に `work_slug` が含まれる
- `SPEC.md` に「works_master はメタデータ専用」の記述がある
- `SPEC.md` に「進行状態を進めない」の文言がある
- `sequence.md` に `C:/PROJECT` 形式のリンクが残っていない
- `UI.md` に `USECASE.md` の表記が残っていない
- `usecase.md` の UC-10 フローに RSS/sitemap 失敗分岐がある
- ルートに `README.md` と `CHANGELOG.md` が存在する
