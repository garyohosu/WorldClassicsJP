"""StateLock のテスト"""

from datetime import datetime, timezone, timedelta
import pytest

from worldclassicsjp.models.state_lock import StateLock, STALE_THRESHOLD


class TestStateLockIsStale:
    def test_6時間以内のheartbeatはstaleでない(self):
        recent = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        lock = StateLock(run_id="r1", pid=1234, started_at=recent, heartbeat_at=recent)
        assert lock.is_stale() is False

    def test_6時間を超えたheartbeatはstale(self):
        old = (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat()
        lock = StateLock(run_id="r1", pid=1234, started_at=old, heartbeat_at=old)
        assert lock.is_stale() is True

    def test_ちょうど6時間はstale(self):
        at_threshold = (datetime.now(timezone.utc) - STALE_THRESHOLD - timedelta(seconds=1)).isoformat()
        lock = StateLock(run_id="r1", pid=1234, started_at=at_threshold, heartbeat_at=at_threshold)
        assert lock.is_stale() is True

    def test_heartbeat_atが不正な文字列はstaleとみなす(self):
        lock = StateLock(run_id="r1", pid=1234, started_at="bad", heartbeat_at="bad")
        assert lock.is_stale() is True


class TestStateLockAcquireRelease:
    def test_ロックが存在しない場合は取得できる(self, tmp_path):
        path = tmp_path / "state.lock"
        lock = StateLock.acquire(path, run_id="run-001")
        assert lock is not None
        assert path.exists()

    def test_取得したロックのrun_idが正しい(self, tmp_path):
        path = tmp_path / "state.lock"
        lock = StateLock.acquire(path, run_id="run-001")
        assert lock.run_id == "run-001"

    def test_release後にロックファイルが削除される(self, tmp_path):
        path = tmp_path / "state.lock"
        lock = StateLock.acquire(path, run_id="run-001")
        lock.release()
        assert not path.exists()

    def test_staleロックは退避されて新規取得できる(self, tmp_path):
        path = tmp_path / "state.lock"
        old_time = (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat()
        # stale なロックを手動で作成
        stale = StateLock(run_id="old-run", pid=99999, started_at=old_time, heartbeat_at=old_time)
        stale._write(path)

        new_lock = StateLock.acquire(path, run_id="new-run")
        assert new_lock is not None
        assert new_lock.run_id == "new-run"
        # stale ファイルが退避されている
        stale_files = list(tmp_path.glob("state.lock.stale.*"))
        assert len(stale_files) == 1


class TestStateLockHeartbeat:
    def test_heartbeat後にheartbeat_atが更新される(self, tmp_path):
        path = tmp_path / "state.lock"
        lock = StateLock.acquire(path, run_id="run-001")
        old_hb = lock.heartbeat_at
        lock.heartbeat()
        assert lock.heartbeat_at >= old_hb
