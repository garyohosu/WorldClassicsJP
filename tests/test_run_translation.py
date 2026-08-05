import json
import subprocess

import pytest

from worldclassicsjp.models.enums import Stage, WorkStatus
from worldclassicsjp.models.state import State
from worldclassicsjp.run import (
    fetch_complete_source_segment,
    select_complete_segment,
    source_offset,
    translate_to_ja,
)


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


def test_段落末尾まで拡張し次回位置を返す():
    text = "first paragraph.\n\nsecond paragraph is longer.\n\nthird."

    chunk, has_more, next_offset = select_complete_segment(text, 30, 0)

    assert chunk == "first paragraph.\n\nsecond paragraph is longer."
    assert has_more is True
    assert text[next_offset:].startswith("\n\nthird.")


def test_保存済みoffsetを固定文字数計算より優先する():
    state = State(
        next_work_id=9,
        current_work_id=9,
        current_part=10,
        current_segment_id="offset-108177",
        current_stage=Stage.IDLE,
        current_work_status=WorkStatus.ACTIVE,
        last_processed_date="2026-08-05",
        last_run_id="run-2026-08-05",
        translate_retry_count=0,
        consecutive_fail_days=0,
        publish_retry_count=0,
    )

    assert source_offset(state, 12000) == 108177


def test_取得原文の改行をLFへ統一してoffsetを安定させる(monkeypatch):
    class Response:
        text = "*** START OF TEST ***\r\nfirst paragraph.\r\n\r\nsecond paragraph.\r\n\r\nthird.\r\n*** END OF TEST ***"

        def raise_for_status(self):
            return None

    monkeypatch.setattr("worldclassicsjp.run.requests.get", lambda *args, **kwargs: Response())

    chunk, has_more, next_offset = fetch_complete_source_segment("https://example.com", 20, 0)

    assert "\r" not in chunk
    assert chunk == "first paragraph.\n\nsecond paragraph."
    assert has_more is True
    assert next_offset == len("first paragraph.\n\nsecond paragraph.")
