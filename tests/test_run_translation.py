import json
import subprocess

import pytest

from worldclassicsjp.run import translate_to_ja


def completed(stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(
        args=["codex"], returncode=returncode, stdout=stdout, stderr=stderr
    )


def test_正常な和訳を返す(monkeypatch):
    source = "This is a long English sentence. " * 30
    payload = json.dumps({
        "translated_text": "これは十分な長さを持つ日本語の翻訳文です。" * 20,
        "summary": "要約",
        "keywords": ["文学"],
    }, ensure_ascii=False)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed(stdout=payload))

    result = translate_to_ja(source, "Title", "Author")

    assert result.summary == "要約"


def test_翻訳コマンド不在を成功扱いしない(monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError("codex")

    monkeypatch.setattr(subprocess, "run", missing)

    with pytest.raises(RuntimeError, match="実行できません"):
        translate_to_ja("English source", "Title", "Author")


def test_翻訳コマンド失敗を成功扱いしない(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: completed(stderr="model unavailable", returncode=1),
    )

    with pytest.raises(RuntimeError, match="exit=1"):
        translate_to_ja("English source", "Title", "Author")


def test_極端に短い翻訳を拒否する(monkeypatch):
    source = "This is source material with many words and sentences. " * 40
    payload = json.dumps({
        "translated_text": "短すぎる訳です。",
        "summary": "要約",
        "keywords": ["文学"],
    }, ensure_ascii=False)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed(stdout=payload))

    with pytest.raises(ValueError, match="短すぎます"):
        translate_to_ja(source, "Title", "Author")


def test_英語原文の混入を拒否する(monkeypatch):
    source = "This is source material with many words and sentences. " * 20
    payload = json.dumps({
        "translated_text": "翻訳失敗。" + source,
        "summary": "要約",
        "keywords": ["文学"],
    }, ensure_ascii=False)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed(stdout=payload))

    with pytest.raises(ValueError, match="英語原文"):
        translate_to_ja(source, "Title", "Author")
