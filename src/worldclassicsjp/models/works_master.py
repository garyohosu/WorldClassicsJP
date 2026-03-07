"""WorksMaster — /data/works_master.json データモデル"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .enums import LengthClass, SourceType

_SLUG_RE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*(-[2-9]|-[1-9][0-9]+)?$')


@dataclass
class WorksMaster:
    work_id: int
    work_slug: str
    title: str
    title_ja: str
    author_name: str
    author_name_ja: str
    author_slug: str
    source_url: str
    source_type: SourceType
    death_year: int
    pd_verified: bool
    length_class: LengthClass
    parts_total: int = 0   # 0 = 未確定（連載中）

    def __post_init__(self) -> None:
        if not isinstance(self.work_id, int) or self.work_id < 1:
            raise ValueError(f"work_id は 1 以上の整数でなければなりません: {self.work_id}")
        if not _SLUG_RE.match(self.work_slug):
            raise ValueError(
                f"work_slug は ASCII 小文字・数字・ハイフンのみ使用可能です: {self.work_slug!r}"
            )
        if not isinstance(self.pd_verified, bool):
            raise TypeError(f"pd_verified は bool でなければなりません: {self.pd_verified!r}")
        self.source_type   = SourceType(self.source_type)
        self.length_class  = LengthClass(self.length_class)

    @classmethod
    def load_all(cls, path: Path) -> list["WorksMaster"]:
        """works_master.json から全作品を読み込む"""
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
        return [cls(**item) for item in items]
