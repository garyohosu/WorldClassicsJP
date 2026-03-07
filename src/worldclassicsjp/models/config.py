"""Config — /config.yaml 設定モデル"""

from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_PHASES = frozenset({1, 2, 3})


@dataclass
class Config:
    host: str
    port: int
    model: str
    daily_max_chars: int
    current_phase: int

    @classmethod
    def load(cls, path: Path) -> "Config":
        """config.yaml を読み込み、バリデーションして返す"""
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        if d is None:
            d = {}
        required = ["host", "port", "model", "daily_max_chars", "current_phase"]
        for key in required:
            if key not in d:
                raise ValueError(f"config.yaml に必須フィールド '{key}' がありません")

        cfg = cls(
            host=str(d["host"]),
            port=int(d["port"]),
            model=str(d["model"]),
            daily_max_chars=int(d["daily_max_chars"]),
            current_phase=int(d["current_phase"]),
        )
        if cfg.current_phase not in VALID_PHASES:
            raise ValueError(
                f"current_phase は 1/2/3 のいずれかでなければなりません: {cfg.current_phase}"
            )
        if cfg.daily_max_chars <= 0:
            raise ValueError(
                f"daily_max_chars は正の整数でなければなりません: {cfg.daily_max_chars}"
            )
        return cfg
