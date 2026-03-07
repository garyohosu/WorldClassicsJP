"""Preprocessor — 原文の段落分割・クリーニング（ローカル LLM 利用）"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Segment:
    """翻訳単位のセグメント（値オブジェクト）"""
    segment_id: str
    part_number: int
    text: str
    char_count: int


class LLMClient(Protocol):
    """ローカル LLM クライアントのプロトコル（テスト時は差し替え可能）"""
    def generate(self, prompt: str) -> str: ...


class Preprocessor:
    """原文テキストを翻訳可能なセグメントに分割する"""

    # Project Gutenberg ヘッダー/フッター除去パターン
    _GUTENBERG_HEADER_RE = re.compile(
        r"\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*",
        re.IGNORECASE | re.DOTALL,
    )
    _GUTENBERG_FOOTER_RE = re.compile(
        r"\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG.*",
        re.IGNORECASE | re.DOTALL,
    )

    def __init__(self, model: str, llm_client: LLMClient | None = None) -> None:
        self.model = model
        self._llm = llm_client  # None の場合は外部 LLM を使わない純粋実装にフォールバック

    # ── 公開メソッド ──────────────────────────────────────────────────

    def clean_text(self, raw_text: str) -> str:
        """Gutenberg ヘッダー/フッターを除去し、余分な空行を正規化する"""
        text = self._GUTENBERG_HEADER_RE.sub("", raw_text)
        text = self._GUTENBERG_FOOTER_RE.sub("", text)
        # 3行以上の連続空行を 2行に正規化
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def split_segments(self, raw_text: str, max_chars: int) -> list[Segment]:
        """
        段落境界を尊重しながら max_chars 以下のセグメントに分割する。
        LLM クライアントが注入されている場合は LLM に段落分割を委譲する。
        """
        if self._llm is not None:
            return self._split_via_llm(raw_text, max_chars)
        return self._split_pure(raw_text, max_chars)

    def generate_metadata(self, text: str) -> dict:
        """本文から要約・キーワードを生成する（LLM 利用）"""
        if self._llm is None:
            raise NotImplementedError("generate_metadata には LLM クライアントが必要です")
        prompt = f"以下のテキストから要約とキーワードを JSON で返してください。\n\n{text}"
        return {"raw": self._llm.generate(prompt)}

    # ── 内部実装 ──────────────────────────────────────────────────────

    def _split_pure(self, raw_text: str, max_chars: int) -> list[Segment]:
        """純粋 Python の段落境界分割（LLM なし）"""
        paragraphs = [p for p in raw_text.split("\n\n") if p.strip()]
        segments: list[Segment] = []
        buffer = ""
        part = 1

        for para in paragraphs:
            candidate = (buffer + "\n\n" + para).strip() if buffer else para
            if buffer and len(candidate) > max_chars:
                segments.append(self._make_segment(buffer, part))
                part += 1
                buffer = para
            else:
                buffer = candidate

        if buffer:
            segments.append(self._make_segment(buffer, part))

        return segments

    def _split_via_llm(self, raw_text: str, max_chars: int) -> list[Segment]:
        """LLM に段落分割を依頼したあと、max_chars でさらに分割する"""
        prompt = (
            f"以下のテキストを段落単位で分割し、各段落を JSON 配列として返してください。\n\n{raw_text}"
        )
        paragraphs = self._llm.generate(prompt).split("\n\n")
        return self._split_pure("\n\n".join(paragraphs), max_chars)

    @staticmethod
    def _make_segment(text: str, part: int) -> Segment:
        t = text.strip()
        return Segment(
            segment_id=f"part-{part:03d}",
            part_number=part,
            text=t,
            char_count=len(t),
        )
