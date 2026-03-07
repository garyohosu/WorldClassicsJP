"""Translator のテスト"""

import json
import subprocess
import pytest

from worldclassicsjp.translator import Translator, TranslationResult


# ── ヘルパー ─────────────────────────────────────────────────────────────


def make_completed_process(stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(
        args=["codex"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def make_runner(stdout: str = "", stderr: str = "", returncode: int = 0):
    """成功する擬似 subprocess.run を返す"""
    def _runner(*args, **kwargs):
        return make_completed_process(stdout=stdout, stderr=stderr, returncode=returncode)
    return _runner


VALID_RESPONSE = json.dumps({
    "translated_text": "タイムマシン",
    "summary": "時間旅行の物語",
    "keywords": ["時間", "旅行"],
})


# ── 正常系 ───────────────────────────────────────────────────────────────


class TestTranslatorSuccess:
    def test_正常なJSONレスポンスでTranslationResultが返る(self):
        runner = make_runner(stdout=VALID_RESPONSE)
        translator = Translator(model="gpt-5", runner=runner)
        result = translator.translate("Translate this.")
        assert isinstance(result, TranslationResult)
        assert result.translated_text == "タイムマシン"
        assert result.summary == "時間旅行の物語"
        assert result.keywords == ["時間", "旅行"]

    def test_keywordsがリストとして返る(self):
        runner = make_runner(stdout=VALID_RESPONSE)
        translator = Translator(model="gpt-5", runner=runner)
        result = translator.translate("Translate this.")
        assert isinstance(result.keywords, list)


# ── 異常系 ───────────────────────────────────────────────────────────────


class TestTranslatorErrors:
    def test_非ゼロ終了でRuntimeError(self):
        runner = make_runner(stderr="fatal error", returncode=1)
        translator = Translator(model="gpt-5", runner=runner)
        with pytest.raises(RuntimeError, match="Codex CLI"):
            translator.translate("Translate this.")

    def test_JSON形式でない応答でValueError(self):
        runner = make_runner(stdout="not json at all")
        translator = Translator(model="gpt-5", runner=runner)
        with pytest.raises(ValueError, match="JSON"):
            translator.translate("Translate this.")

    def test_必須キーが欠落するとValueError(self):
        incomplete = json.dumps({"translated_text": "テキスト"})
        runner = make_runner(stdout=incomplete)
        translator = Translator(model="gpt-5", runner=runner)
        with pytest.raises(ValueError, match="summary"):
            translator.translate("Translate this.")

    def test_translated_textが欠落するとValueError(self):
        incomplete = json.dumps({"summary": "要約", "keywords": []})
        runner = make_runner(stdout=incomplete)
        translator = Translator(model="gpt-5", runner=runner)
        with pytest.raises(ValueError, match="translated_text"):
            translator.translate("Translate this.")

    def test_keywordsが欠落するとValueError(self):
        incomplete = json.dumps({"translated_text": "テキスト", "summary": "要約"})
        runner = make_runner(stdout=incomplete)
        translator = Translator(model="gpt-5", runner=runner)
        with pytest.raises(ValueError, match="keywords"):
            translator.translate("Translate this.")
