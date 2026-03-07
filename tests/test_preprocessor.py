"""Preprocessor のテスト"""

import pytest

from worldclassicsjp.preprocessor import Preprocessor, Segment


# ── フィクスチャ ──────────────────────────────────────────────────────────


class FakeLLMClient:
    """テスト用のダミー LLM クライアント"""
    def __init__(self, response: str = ""):
        self._response = response

    def generate(self, prompt: str) -> str:
        return self._response


# ── clean_text のテスト ───────────────────────────────────────────────────


class TestCleanText:
    def test_Gutenbergヘッダーが除去される(self):
        text = (
            "*** START OF THE PROJECT GUTENBERG EBOOK THE TIME MACHINE ***\n\n"
            "Chapter 1\n\nThis is the story."
        )
        preprocessor = Preprocessor(model="llama3")
        result = preprocessor.clean_text(text)
        assert "PROJECT GUTENBERG" not in result
        assert "Chapter 1" in result

    def test_Gutenbergフッターが除去される(self):
        text = (
            "The End.\n\n"
            "*** END OF THE PROJECT GUTENBERG EBOOK THE TIME MACHINE ***\n\n"
            "Some license text here."
        )
        preprocessor = Preprocessor(model="llama3")
        result = preprocessor.clean_text(text)
        assert "PROJECT GUTENBERG" not in result
        assert "The End." in result

    def test_3行以上の空行が2行に正規化される(self):
        text = "Paragraph 1.\n\n\n\n\nParagraph 2."
        preprocessor = Preprocessor(model="llama3")
        result = preprocessor.clean_text(text)
        assert "\n\n\n" not in result
        assert "Paragraph 1." in result
        assert "Paragraph 2." in result

    def test_前後の空白が除去される(self):
        text = "\n\n  Hello World  \n\n"
        preprocessor = Preprocessor(model="llama3")
        result = preprocessor.clean_text(text)
        assert result == "Hello World"

    def test_ヘッダーもフッターもない場合はそのまま返る(self):
        text = "Just a plain text paragraph."
        preprocessor = Preprocessor(model="llama3")
        result = preprocessor.clean_text(text)
        assert result == text


# ── split_segments のテスト（LLM なし）─────────────────────────────────────


class TestSplitSegmentsPure:
    def test_単一段落がひとつのセグメントになる(self):
        text = "This is a single paragraph."
        preprocessor = Preprocessor(model="llama3")
        segments = preprocessor.split_segments(text, max_chars=500)
        assert len(segments) == 1
        assert segments[0].text == text
        assert segments[0].part_number == 1
        assert segments[0].segment_id == "part-001"

    def test_max_charsを超えると分割される(self):
        para1 = "A" * 100
        para2 = "B" * 100
        text = para1 + "\n\n" + para2
        preprocessor = Preprocessor(model="llama3")
        segments = preprocessor.split_segments(text, max_chars=150)
        assert len(segments) == 2

    def test_max_chars以内なら結合される(self):
        text = "Short.\n\nAlso short."
        preprocessor = Preprocessor(model="llama3")
        segments = preprocessor.split_segments(text, max_chars=500)
        assert len(segments) == 1

    def test_segment_idは連番になる(self):
        para = "X" * 100
        text = "\n\n".join([para] * 3)
        preprocessor = Preprocessor(model="llama3")
        segments = preprocessor.split_segments(text, max_chars=150)
        ids = [s.segment_id for s in segments]
        assert ids[0] == "part-001"
        assert ids[1] == "part-002"

    def test_char_countはテキスト長と一致する(self):
        text = "Hello, world!"
        preprocessor = Preprocessor(model="llama3")
        segments = preprocessor.split_segments(text, max_chars=500)
        assert segments[0].char_count == len(text)

    def test_空段落は無視される(self):
        text = "Para 1.\n\n\n\nPara 2."
        preprocessor = Preprocessor(model="llama3")
        segments = preprocessor.split_segments(text, max_chars=500)
        # 空段落は無視されるが 2 段落は合体
        assert len(segments) == 1


# ── split_segments のテスト（LLM あり）──────────────────────────────────────


class TestSplitSegmentsViaLLM:
    def test_LLMがあれば_split_via_llmが使われる(self):
        llm = FakeLLMClient(response="Paragraph from LLM.\n\nSecond paragraph.")
        preprocessor = Preprocessor(model="llama3", llm_client=llm)
        segments = preprocessor.split_segments("any input", max_chars=1000)
        # LLM の応答がセグメントになる
        assert len(segments) == 1  # 2 段落が max_chars 内に収まるので 1 セグメント


# ── generate_metadata のテスト ───────────────────────────────────────────


class TestGenerateMetadata:
    def test_LLMなしでNotImplementedError(self):
        preprocessor = Preprocessor(model="llama3")
        with pytest.raises(NotImplementedError):
            preprocessor.generate_metadata("some text")

    def test_LLMありで辞書を返す(self):
        llm = FakeLLMClient(response='{"summary": "test", "keywords": ["a"]}')
        preprocessor = Preprocessor(model="llama3", llm_client=llm)
        result = preprocessor.generate_metadata("some text")
        assert "raw" in result
