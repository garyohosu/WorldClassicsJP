# Codex CLI 実行例

## 1. 設計書を読ませて実装開始
```bash
codex exec -m gpt-5.4 -c model_reasoning_effort="high" "Read README.md and CODEX_CLI_INSTRUCTIONS.md. Then update the project docs and implementation to match the corrected design."
```

## 2. ドキュメント修正だけ先にやらせる
```bash
codex exec -m gpt-5.4 "Read DESIGN_FIXES.md and patch QandA.md, SPEC.md, sequence.md, UI.md, and usecase.md."
```

## 3. 状態管理ロジックを重点実装
```bash
codex exec -m gpt-5.4 "Read DATA_MODEL.md and STATE_MACHINE.md, then implement safe state management and retry handling."
```

## 4. rollback 重点
```bash
codex exec -m gpt-5.4 "Implement publish rollback using pre_publish_head and ensure state does not advance on publish failure."
```

## 5. テスト生成
```bash
codex exec -m gpt-5.4 "Generate tests for schema validation, translate retry behavior, publish rollback, and stale lock recovery."
```

## 6. OpenClaw から呼ぶ想定メモ
- 非対話実行を使う
- 作業ディレクトリを固定する
- ログを保存する
- 自動 push 前に安全確認ロジックを置く
