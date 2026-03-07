"""QualityChecker のテスト"""

import json
import pytest

from worldclassicsjp.quality_checker import QualityChecker, QAResult


# ── フィクスチャ ──────────────────────────────────────────────────────────


class FakeLLMPass:
    def generate(self, prompt: str) -> str:
        return json.dumps({"status": "pass", "score": 0.9, "issues": []})


class FakeLLMFail:
    def generate(self, prompt: str) -> str:
        return json.dumps({"status": "fail", "score": 0.4, "issues": ["誤訳あり"]})


class FakeLLMBadJSON:
    def generate(self, prompt: str) -> str:
        return "not valid json"


# ── QAResult バリデーションのテスト ──────────────────────────────────────


class TestQAResultValidation:
    def test_正常なQAResultが作れる(self):
        r = QAResult(status="pass", score=0.9)
        assert r.status == "pass"
        assert r.score == 0.9

    def test_statusがpass_or_fail以外はValueError(self):
        with pytest.raises(ValueError, match="status"):
            QAResult(status="ok", score=0.5)

    def test_scoreが1_0を超えるとValueError(self):
        with pytest.raises(ValueError, match="score"):
            QAResult(status="pass", score=1.1)

    def test_scoreが0_0未満はValueError(self):
        with pytest.raises(ValueError, match="score"):
            QAResult(status="fail", score=-0.1)

    def test_issues省略時は空リスト(self):
        r = QAResult(status="pass", score=1.0)
        assert r.issues == []


# ── QualityChecker.check のテスト ────────────────────────────────────────


class TestQualityCheckerCheck:
    def test_LLMなしでNotImplementedError(self):
        qc = QualityChecker(model="llama3")
        with pytest.raises(NotImplementedError):
            qc.check("original", "translated")

    def test_passのQAResultを返す(self):
        qc = QualityChecker(model="llama3", llm_client=FakeLLMPass())
        result = qc.check("Hello", "こんにちは")
        assert result.status == "pass"
        assert result.score == 0.9
        assert result.issues == []

    def test_failのQAResultを返す(self):
        qc = QualityChecker(model="llama3", llm_client=FakeLLMFail())
        result = qc.check("Hello", "誤訳")
        assert result.status == "fail"
        assert len(result.issues) == 1

    def test_LLMが不正JSONを返すとValueError(self):
        qc = QualityChecker(model="llama3", llm_client=FakeLLMBadJSON())
        with pytest.raises(ValueError, match="JSON"):
            qc.check("Hello", "こんにちは")
