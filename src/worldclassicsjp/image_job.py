"""ImageJob — 画像取得補助ジョブ（日次パイプラインと独立）"""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path
from typing import Protocol

from .models.enums import RightsLabel
from .models.image_meta import ImageMeta

ALLOWED_RIGHTS = frozenset({
    RightsLabel.PUBLIC_DOMAIN,
    RightsLabel.CC0,
    RightsLabel.PUBLIC_DOMAIN_MARK,
})


class HttpFetcher(Protocol):
    """HTTP フェッチャーのプロトコル（テスト時はモックに差し替え可能）"""
    def get(self, url: str) -> bytes: ...


class ImageJob:
    """works_master の変化を検出し、Wikimedia Commons から画像を取得する"""

    def __init__(self, http_fetcher: HttpFetcher | None = None) -> None:
        self._http = http_fetcher or self._default_http

    # ── 差分検出 ──────────────────────────────────────────────────────

    def detect_changes(self, works_master_path: Path, hash_file_path: Path) -> bool:
        """
        works_master.json の SHA-256 を hash_file と比較する。
        変化があった場合（または hash_file が存在しない場合）に True を返す。
        """
        current_hash = self._sha256(works_master_path)
        if not hash_file_path.exists():
            return True
        saved_hash = hash_file_path.read_text(encoding="utf-8").strip()
        return current_hash != saved_hash

    def update_hash(self, works_master_path: Path, hash_file_path: Path) -> None:
        """現在の SHA-256 を hash_file に書き込む"""
        hash_file_path.write_text(
            self._sha256(works_master_path), encoding="utf-8"
        )

    # ── 画像取得 ──────────────────────────────────────────────────────

    def search_image(self, name: str) -> list[str]:
        """Wikimedia Commons で著者名/作品名を検索し、候補 URL リストを返す"""
        raise NotImplementedError

    def verify_rights(self, file_page_url: str) -> RightsLabel | None:
        """
        個別ファイルページの権利表示を確認し、許可されたライセンスなら RightsLabel を返す。
        許可外の場合は None を返す。
        """
        raise NotImplementedError

    def download(self, file_url: str) -> bytes:
        """画像ファイルをダウンロードして返す"""
        return self._http.get(file_url)

    def save(self, image_path: Path, meta: ImageMeta) -> None:
        """画像ファイルと YAML sidecar を保存する"""
        raise NotImplementedError

    # ── 内部 ──────────────────────────────────────────────────────────

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _default_http(url: str) -> bytes:
        with urllib.request.urlopen(url) as resp:
            return resp.read()
