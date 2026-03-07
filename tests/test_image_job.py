"""ImageJob のテスト"""

import hashlib
import json
import pytest

from worldclassicsjp.image_job import ImageJob


# ── detect_changes のテスト ───────────────────────────────────────────────


class TestDetectChanges:
    def _write_json(self, path, data: dict) -> None:
        path.write_text(json.dumps(data), encoding="utf-8")

    def _sha256(self, path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_ハッシュファイルが存在しない場合はTrue(self, tmp_path):
        wm_path = tmp_path / "works_master.json"
        self._write_json(wm_path, {"works": []})
        hash_path = tmp_path / "works_master.hash"

        job = ImageJob()
        assert job.detect_changes(wm_path, hash_path) is True

    def test_内容が同じならFalse(self, tmp_path):
        wm_path = tmp_path / "works_master.json"
        self._write_json(wm_path, {"works": []})
        hash_path = tmp_path / "works_master.hash"
        hash_path.write_text(self._sha256(wm_path), encoding="utf-8")

        job = ImageJob()
        assert job.detect_changes(wm_path, hash_path) is False

    def test_内容が変わったらTrue(self, tmp_path):
        wm_path = tmp_path / "works_master.json"
        self._write_json(wm_path, {"works": []})
        hash_path = tmp_path / "works_master.hash"
        hash_path.write_text(self._sha256(wm_path), encoding="utf-8")

        # 内容を変更
        self._write_json(wm_path, {"works": [{"id": 1}]})

        job = ImageJob()
        assert job.detect_changes(wm_path, hash_path) is True


# ── update_hash のテスト ─────────────────────────────────────────────────


class TestUpdateHash:
    def test_SHA256をハッシュファイルに書き込む(self, tmp_path):
        wm_path = tmp_path / "works_master.json"
        wm_path.write_text('{"works":[]}', encoding="utf-8")
        hash_path = tmp_path / "works_master.hash"

        job = ImageJob()
        job.update_hash(wm_path, hash_path)

        expected = hashlib.sha256(wm_path.read_bytes()).hexdigest()
        assert hash_path.read_text(encoding="utf-8") == expected

    def test_update_hash後にdetect_changesがFalseになる(self, tmp_path):
        wm_path = tmp_path / "works_master.json"
        wm_path.write_text('{"works":[]}', encoding="utf-8")
        hash_path = tmp_path / "works_master.hash"

        job = ImageJob()
        job.update_hash(wm_path, hash_path)
        assert job.detect_changes(wm_path, hash_path) is False
