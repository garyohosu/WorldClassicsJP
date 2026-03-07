"""State のテスト"""

import json
import pytest

from worldclassicsjp.models.state import State
from worldclassicsjp.models.enums import Stage, WorkStatus


class TestStateInitDefault:
    def test_最小work_idで初期状態が作れる(self):
        s = State.init_default(min_work_id=3)
        assert s.current_work_id == 3
        assert s.next_work_id    == 3
        assert s.current_part    == 1
        assert s.current_segment_id   == ""
        assert s.current_stage        == Stage.IDLE
        assert s.current_work_status  == WorkStatus.ACTIVE
        assert s.translate_retry_count  == 0
        assert s.consecutive_fail_days  == 0
        assert s.publish_retry_count    == 0
        assert s.pre_publish_head       == ""


class TestStateSaveLoad:
    def test_保存したStateをロードすると同じ値が返る(self, tmp_path, active_state):
        path = tmp_path / "state.json"
        active_state.save(path)
        loaded = State.load(path)

        assert loaded.current_work_id     == active_state.current_work_id
        assert loaded.current_part        == active_state.current_part
        assert loaded.current_stage       == active_state.current_stage
        assert loaded.current_work_status == active_state.current_work_status
        assert loaded.pre_publish_head    == active_state.pre_publish_head

    def test_save_は_tmp_経由でアトミックに書き込む(self, tmp_path, active_state):
        path = tmp_path / "state.json"
        active_state.save(path)
        # tmp ファイルが残っていないことを確認
        assert not (tmp_path / "state.tmp").exists()
        assert path.exists()

    def test_save_はJSON形式で書き込む(self, tmp_path, active_state):
        path = tmp_path / "state.json"
        active_state.save(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["current_stage"]       == "translate"
        assert data["current_work_status"] == "active"
        assert data["pre_publish_head"]    == ""

    def test_load_は列挙型に変換する(self, state_json):
        s = State.load(state_json["path"])
        assert isinstance(s.current_stage,       Stage)
        assert isinstance(s.current_work_status, WorkStatus)

    def test_load_でpre_publish_headが欠落していても空文字で補完される(self, tmp_path, active_state):
        path = tmp_path / "state.json"
        active_state.save(path)
        # JSON から pre_publish_head を取り除く
        d = json.loads(path.read_text())
        del d["pre_publish_head"]
        path.write_text(json.dumps(d))

        loaded = State.load(path)
        assert loaded.pre_publish_head == ""


class TestStateConstants:
    def test_translate_retry上限は2(self):
        assert State.MAX_TRANSLATE_RETRIES == 2

    def test_publish_retry上限は3(self):
        assert State.MAX_PUBLISH_RETRIES == 3

    def test_consecutive_fail_days上限は2(self):
        assert State.MAX_CONSECUTIVE_FAIL_DAYS == 2
