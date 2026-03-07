# WorldClassicsJP Codex CLI 指示書パック

この zip は、WorldClassicsJP の設計レビュー結果を反映した **Codex CLI 用の実装指示書一式**です。

## 目的

以下をまとめて Codex CLI に渡せるようにすること。

- 文書間の矛盾修正
- 実装優先順位の明確化
- state.json / works_master.json の責務分離
- 翻訳失敗時・公開失敗時の正しい状態遷移
- GitHub Pages 前提の公開フロー
- OpenClaw + Codex CLI + ローカル LLM の責務分離

## 同梱ファイル

- `CODEX_CLI_INSTRUCTIONS.md`  
  Codex CLI に最初に読ませるメイン指示書
- `DESIGN_FIXES.md`  
  指摘済み不整合の修正方針
- `ADDITIONAL_IMPROVEMENTS.md`  
  追加で入れるべき設計改善
- `DATA_MODEL.md`  
  works_master.json / state.json の責務定義
- `STATE_MACHINE.md`  
  状態遷移ルール
- `IMPLEMENTATION_PLAN.md`  
  実装順序
- `RUN_EXAMPLES.md`  
  Codex CLI 実行例

## 使い方

Codex CLI にまず `CODEX_CLI_INSTRUCTIONS.md` を読ませ、その後必要に応じて他の md を参照させる。

例:

```bash
codex exec -m gpt-5.4 -c model_reasoning_effort="high" "Read README.md and CODEX_CLI_INSTRUCTIONS.md, then implement the system."
```

## 想定環境

- OpenClaw on Windows 11 WSL2
- GitHub Pages
- ローカル LLM (Ollama 等)
- Codex CLI による翻訳・実装補助

## 反映済みチェック（2026-03-07）

以下は、指示書パックの修正方針がプロジェクト本体へ反映済みであることを確認した項目。

- [x] `QandA.md` の works_master 必須項目へ `work_slug` 追加
- [x] `SPEC.md` の次作品選択を state 主体へ修正（works_master はメタデータ専用）
- [x] `SPEC.md` の「状態を更新しない」表現を「進行状態を進めない」に修正
- [x] `sequence.md` の絶対パスリンクを相対パスへ修正
- [x] `UI.md` の `USECASE.md` 表記を `usecase.md` に統一
- [x] `usecase.md` に RSS/sitemap の分岐（成功/補助成果物失敗/致命的）を追加
- [x] ルート `README.md` を追加し、v1 設計原則を明文化
- [x] ルート `CHANGELOG.md` を追加し、今回修正の履歴を記録
