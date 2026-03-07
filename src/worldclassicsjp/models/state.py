"""State — /data/state.json データモデル（実行状態の唯一ソース）"""

import json
from dataclasses import dataclass
from pathlib import Path

from .enums import Stage, WorkStatus


@dataclass
class State:
    next_work_id: int
    current_work_id: int
    current_part: int
    current_segment_id: str
    current_stage: Stage
    current_work_status: WorkStatus
    last_processed_date: str
    last_run_id: str
    translate_retry_count: int
    consecutive_fail_days: int
    publish_retry_count: int
    pre_publish_head: str = ""

    # ── 上限値定数 ──────────────────────────────────────────────────
    MAX_TRANSLATE_RETRIES    = 2   # 初回 1 回 + 再翻訳最大 2 回
    MAX_PUBLISH_RETRIES      = 3   # 公開リトライ上限
    MAX_CONSECUTIVE_FAIL_DAYS = 2  # 連続失敗日数上限

    # ── ファクトリメソッド ────────────────────────────────────────────

    @classmethod
    def load(cls, path: Path) -> "State":
        """state.json を読み込む"""
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return cls(
            next_work_id         = d["next_work_id"],
            current_work_id      = d["current_work_id"],
            current_part         = d["current_part"],
            current_segment_id   = d["current_segment_id"],
            current_stage        = Stage(d["current_stage"]),
            current_work_status  = WorkStatus(d["current_work_status"]),
            last_processed_date  = d["last_processed_date"],
            last_run_id          = d["last_run_id"],
            translate_retry_count  = d["translate_retry_count"],
            consecutive_fail_days  = d["consecutive_fail_days"],
            publish_retry_count    = d["publish_retry_count"],
            pre_publish_head       = d.get("pre_publish_head", ""),
        )

    @classmethod
    def init_default(cls, min_work_id: int) -> "State":
        """state.json が存在しない場合の初期状態を生成する"""
        return cls(
            next_work_id         = min_work_id,
            current_work_id      = min_work_id,
            current_part         = 1,
            current_segment_id   = "",
            current_stage        = Stage.IDLE,
            current_work_status  = WorkStatus.ACTIVE,
            last_processed_date  = "",
            last_run_id          = "",
            translate_retry_count  = 0,
            consecutive_fail_days  = 0,
            publish_retry_count    = 0,
            pre_publish_head       = "",
        )

    # ── 保存（アトミック） ────────────────────────────────────────────

    def save(self, path: Path) -> None:
        """state.json.tmp 経由でアトミックに書き込む"""
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self._to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(path)

    def _to_dict(self) -> dict:
        return {
            "next_work_id":          self.next_work_id,
            "current_work_id":       self.current_work_id,
            "current_part":          self.current_part,
            "current_segment_id":    self.current_segment_id,
            "current_stage":         self.current_stage.value,
            "current_work_status":   self.current_work_status.value,
            "last_processed_date":   self.last_processed_date,
            "last_run_id":           self.last_run_id,
            "translate_retry_count": self.translate_retry_count,
            "consecutive_fail_days": self.consecutive_fail_days,
            "publish_retry_count":   self.publish_retry_count,
            "pre_publish_head":      self.pre_publish_head,
        }
