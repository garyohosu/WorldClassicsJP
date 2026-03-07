"""共通フィクスチャ"""

import json
import pytest

from worldclassicsjp.models.enums import (
    LengthClass, SourceType, Stage, WorkStatus,
)
from worldclassicsjp.models.works_master import WorksMaster
from worldclassicsjp.models.state import State


# ── WorksMaster フィクスチャ ──────────────────────────────────────────

@pytest.fixture
def sample_work() -> WorksMaster:
    return WorksMaster(
        work_id=1,
        work_slug="the-time-machine",
        title="The Time Machine",
        title_ja="タイム・マシン",
        author_name="H. G. Wells",
        author_name_ja="H・G・ウェルズ",
        author_slug="h-g-wells",
        source_url="https://www.gutenberg.org/files/35/35-0.txt",
        source_type=SourceType.TEXT_URL,
        death_year=1946,
        pd_verified=True,
        length_class=LengthClass.MEDIUM,
    )


@pytest.fixture
def works_master_json(tmp_path, sample_work) -> dict:
    """works_master.json ファイルをテンポラリディレクトリに作成"""
    data = [
        {
            "work_id": 1,
            "work_slug": "the-time-machine",
            "title": "The Time Machine",
            "title_ja": "タイム・マシン",
            "author_name": "H. G. Wells",
            "author_name_ja": "H・G・ウェルズ",
            "author_slug": "h-g-wells",
            "source_url": "https://www.gutenberg.org/files/35/35-0.txt",
            "source_type": "text_url",
            "death_year": 1946,
            "pd_verified": True,
            "length_class": "medium",
        }
    ]
    path = tmp_path / "works_master.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return {"path": path, "data": data}


# ── State フィクスチャ ────────────────────────────────────────────────

@pytest.fixture
def default_state() -> State:
    return State.init_default(min_work_id=1)


@pytest.fixture
def active_state() -> State:
    return State(
        next_work_id=2,
        current_work_id=1,
        current_part=3,
        current_segment_id="part-003",
        current_stage=Stage.TRANSLATE,
        current_work_status=WorkStatus.ACTIVE,
        last_processed_date="2026-03-06",
        last_run_id="20260306T030000Z-00001",
        translate_retry_count=0,
        consecutive_fail_days=0,
        publish_retry_count=0,
        pre_publish_head="",
    )


@pytest.fixture
def state_json(tmp_path, active_state) -> dict:
    """state.json ファイルをテンポラリディレクトリに作成"""
    path = tmp_path / "state.json"
    active_state.save(path)
    return {"path": path, "state": active_state}


# ── config.yaml フィクスチャ ──────────────────────────────────────────

@pytest.fixture
def config_yaml(tmp_path) -> dict:
    content = (
        "host: localhost\n"
        "port: 11434\n"
        "model: llama3\n"
        "daily_max_chars: 12000\n"
        "current_phase: 1\n"
    )
    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")
    return {"path": path}
