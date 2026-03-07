"""列挙型定義 — class.md §列挙型 対応"""

from enum import Enum


class Stage(str, Enum):
    """処理ステージ（state.json.current_stage）"""
    IDLE          = "idle"
    PREPROCESS    = "preprocess"
    TRANSLATE     = "translate"
    QUALITY_CHECK = "quality_check"
    PUBLISH       = "publish"


class WorkStatus(str, Enum):
    """作品ステータス（state.json.current_work_status）"""
    ACTIVE    = "active"
    PAUSED    = "paused"
    COMPLETE  = "complete"
    EXHAUSTED = "exhausted"
    FAILED    = "failed"


class LengthClass(str, Enum):
    """作品長さ分類（works_master.json.length_class）"""
    SHORT  = "short"
    MEDIUM = "medium"
    LONG   = "long"


class SourceType(str, Enum):
    """原文ソース形式（works_master.json.source_type）"""
    TXT      = "txt"
    TEXT_URL = "text_url"


class RightsLabel(str, Enum):
    """許可された画像ライセンス（SPEC §22）"""
    PUBLIC_DOMAIN      = "Public domain"
    CC0                = "CC0"
    PUBLIC_DOMAIN_MARK = "Public Domain Mark"
