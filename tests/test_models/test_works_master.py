"""WorksMaster のテスト"""

import json
import pytest

from worldclassicsjp.models.works_master import WorksMaster
from worldclassicsjp.models.enums import LengthClass, SourceType


class TestWorksMasterCreation:
    def test_正常な作品データが作れる(self, sample_work):
        assert sample_work.work_id == 1
        assert sample_work.work_slug == "the-time-machine"
        assert sample_work.pd_verified is True

    def test_source_type_が列挙型に変換される(self, sample_work):
        assert sample_work.source_type == SourceType.TEXT_URL

    def test_length_class_が列挙型に変換される(self, sample_work):
        assert sample_work.length_class == LengthClass.MEDIUM


class TestWorksMasterValidation:
    def test_work_id_が0以下の場合エラー(self, sample_work):
        with pytest.raises(ValueError, match="work_id"):
            WorksMaster(**{**sample_work.__dict__, "work_id": 0})

    def test_work_slug_に大文字が含まれるとエラー(self, sample_work):
        with pytest.raises(ValueError, match="work_slug"):
            WorksMaster(**{**sample_work.__dict__, "work_slug": "The-Time-Machine"})

    def test_work_slug_にスペースが含まれるとエラー(self, sample_work):
        with pytest.raises(ValueError, match="work_slug"):
            WorksMaster(**{**sample_work.__dict__, "work_slug": "the time machine"})

    def test_work_slug_の重複サフィックス付きは有効(self, sample_work):
        w = WorksMaster(**{**sample_work.__dict__, "work_slug": "the-time-machine-2"})
        assert w.work_slug == "the-time-machine-2"

    def test_pd_verified_が非boolの場合エラー(self, sample_work):
        with pytest.raises(TypeError, match="pd_verified"):
            WorksMaster(**{**sample_work.__dict__, "pd_verified": 1})

    def test_不正なsource_typeはエラー(self, sample_work):
        with pytest.raises(ValueError):
            WorksMaster(**{**sample_work.__dict__, "source_type": "html"})

    def test_不正なlength_classはエラー(self, sample_work):
        with pytest.raises(ValueError):
            WorksMaster(**{**sample_work.__dict__, "length_class": "huge"})


class TestWorksMasterLoadAll:
    def test_JSONファイルから全作品を読み込める(self, works_master_json):
        works = WorksMaster.load_all(works_master_json["path"])
        assert len(works) == 1
        assert works[0].work_id == 1
        assert works[0].source_type == SourceType.TEXT_URL
