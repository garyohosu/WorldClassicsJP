"""QualityChecker — ローカル LLM を使った翻訳品質チェック"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class QAResult:
    """品質チェック結果（値オブジェクト）"""
    status: str          # "pass" または "fail"
    score: float         # 0.0〜1.0
    issues: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in ("pass", "fail"):
            raise ValueError(f"status は 'pass' か 'fail' でなければなりません: {self.status!r}")
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"score は 0.0〜1.0 の範囲でなければなりません: {self.score}")


class LLMClient(Protocol):
    """ローカル LLM クライアントのプロトコル"""
    def generate(self, prompt: str) -> str: ...


class QualityChecker:
    """翻訳テキストの品質を判定する"""

    def __init__(self, model: str, llm_client: LLMClient | None = None) -> None:
        self.model = model
        self._llm = llm_client

    def check(self, original: str, translated: str) -> QAResult:
        """
        原文と翻訳文を比較して品質を判定する。

        Returns:
            QAResult: status="pass" or "fail", score, issues

        Raises:
            NotImplementedError: LLM クライアントが未注入の場合
            ValueError:          LLM の応答が JSON 形式でない場合
        """
        if self._llm is None:
            raise NotImplementedError("QualityChecker には LLM クライアントが必要です")

        prompt = self._build_prompt(original, translated)
        raw = self._llm.generate(prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM の応答が JSON 形式ではありません: {exc}") from exc

        return QAResult(
            status=data["status"],
            score=float(data["score"]),
            issues=data.get("issues", []),
        )

    @staticmethod
    def _build_prompt(original: str, translated: str) -> str:
        return (
            "以下の原文と翻訳文を比較し、品質を評価してください。\n"
            "結果は JSON で返してください: {\"status\": \"pass\" or \"fail\", \"score\": 0.0〜1.0, \"issues\": [...]}\n\n"
            f"=== 原文 ===\n{original}\n\n"
            f"=== 翻訳文 ===\n{translated}"
        )
