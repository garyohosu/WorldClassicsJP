"""Translator — Codex CLI を使った翻訳コンポーネント"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Protocol


@dataclass
class TranslationResult:
    """翻訳結果（値オブジェクト）"""
    translated_text: str
    summary: str
    keywords: list[str]


class SubprocessRunner(Protocol):
    """subprocess.run のプロトコル（テスト時はモックに差し替え可能）"""
    def __call__(self, *args, **kwargs) -> subprocess.CompletedProcess: ...


class Translator:
    """展開済みプロンプトを Codex CLI に渡して翻訳結果 JSON を受け取る"""

    TIMEOUT = 300  # 秒

    def __init__(
        self,
        model: str,
        runner: SubprocessRunner | None = None,
    ) -> None:
        self.model = model
        self._runner: SubprocessRunner = runner or subprocess.run

    def translate(self, expanded_prompt: str) -> TranslationResult:
        """
        展開済みプロンプト文字列を stdin で Codex CLI に渡し、
        JSON レスポンスを TranslationResult に変換して返す。

        Raises:
            RuntimeError: Codex CLI が非ゼロ終了した場合
            ValueError:   JSON 形式が不正な場合、または必須キーが欠落している場合
        """
        result = self._runner(
            ["codex", "exec", "-m", self.model, "-"],
            input=expanded_prompt,
            capture_output=True,
            text=True,
            timeout=self.TIMEOUT,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Codex CLI が失敗しました (exit={result.returncode}): {result.stderr.strip()}"
            )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Codex CLI の出力が JSON 形式ではありません: {exc}") from exc

        for key in ("translated_text", "summary", "keywords"):
            if key not in data:
                raise ValueError(f"Codex CLI の JSON レスポンスに '{key}' がありません")

        return TranslationResult(
            translated_text=data["translated_text"],
            summary=data["summary"],
            keywords=data["keywords"],
        )
