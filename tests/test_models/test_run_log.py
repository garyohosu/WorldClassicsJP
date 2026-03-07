"""RunLog のテスト"""

import json
import pytest

from worldclassicsjp.models.run_log import RunLog


class TestRunLog:
    def test_エントリを追記できる(self):
        log = RunLog(run_id="r1", date="2026-03-07", stage="translate", status="fail")
        log.append({"msg": "翻訳エラー", "segment": "part-001"})
        assert len(log.errors) == 1
        assert log.errors[0]["msg"] == "翻訳エラー"

    def test_saveでJSONファイルが作成される(self, tmp_path):
        log = RunLog(run_id="r1", date="2026-03-07", stage="translate", status="ok")
        path = tmp_path / "logs" / "2026" / "03" / "07" / "r1.json"
        log.save(path)
        assert path.exists()

    def test_saveしたJSONが正しい内容を持つ(self, tmp_path):
        log = RunLog(run_id="r1", date="2026-03-07", stage="publish", status="ok")
        log.append({"msg": "テスト"})
        path = tmp_path / "r1.json"
        log.save(path)

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["run_id"] == "r1"
        assert data["stage"]  == "publish"
        assert len(data["errors"]) == 1

    def test_親ディレクトリが存在しなくても自動作成される(self, tmp_path):
        log = RunLog(run_id="r1", date="2026-03-07", stage="idle", status="ok")
        nested = tmp_path / "a" / "b" / "c" / "r1.json"
        log.save(nested)
        assert nested.exists()
