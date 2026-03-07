"""StateLock — /data/state.lock 排他実行制御"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

STALE_THRESHOLD = timedelta(hours=6)


@dataclass
class StateLock:
    run_id: str
    pid: int
    started_at: str
    heartbeat_at: str
    _path: Path = field(default=None, repr=False, compare=False)

    # ── ファクトリ ────────────────────────────────────────────────────

    @classmethod
    def acquire(cls, path: Path, run_id: str) -> "StateLock | None":
        """ロックを取得する。取得できない場合は None を返す"""
        if path.exists():
            existing = cls._read(path)
            if existing is not None:
                if not existing.is_stale():
                    # 生存プロセスか確認
                    try:
                        os.kill(existing.pid, 0)
                        return None  # 有効なロックが存在する
                    except (ProcessLookupError, PermissionError):
                        pass  # プロセスが終了していた
                # stale ロックを退避
                stale = path.parent / f"state.lock.stale.{existing.run_id}"
                path.rename(stale)

        now = datetime.now(timezone.utc).isoformat()
        instance = cls(run_id=run_id, pid=os.getpid(), started_at=now, heartbeat_at=now)
        instance._path = path
        instance._write(path)
        return instance

    # ── インスタンスメソッド ──────────────────────────────────────────

    def heartbeat(self) -> None:
        """heartbeat_at を現在時刻に更新する"""
        self.heartbeat_at = datetime.now(timezone.utc).isoformat()
        if self._path:
            self._write(self._path)

    def release(self) -> None:
        """ロックファイルを削除する"""
        if self._path and self._path.exists():
            self._path.unlink()

    def is_stale(self) -> bool:
        """heartbeat_at が STALE_THRESHOLD を超えていれば True"""
        try:
            hb = datetime.fromisoformat(self.heartbeat_at)
            if hb.tzinfo is None:
                hb = hb.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - hb) > STALE_THRESHOLD
        except (ValueError, TypeError):
            return True

    # ── 内部 ──────────────────────────────────────────────────────────

    def _write(self, path: Path) -> None:
        path.write_text(
            json.dumps({
                "run_id":       self.run_id,
                "pid":          self.pid,
                "started_at":   self.started_at,
                "heartbeat_at": self.heartbeat_at,
            }),
            encoding="utf-8",
        )

    @classmethod
    def _read(cls, path: Path) -> "StateLock | None":
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            return cls(
                run_id=d["run_id"], pid=d["pid"],
                started_at=d["started_at"], heartbeat_at=d["heartbeat_at"],
            )
        except Exception:
            return None
