"""Publisher のテスト"""

import subprocess
import pytest

from worldclassicsjp.publisher import Publisher


# ── ヘルパー ─────────────────────────────────────────────────────────────


def make_git_runner(responses: dict | None = None):
    """
    コマンドのリストをキーにレスポンスを返す擬似 git_runner。
    responses: {(cmd_tuple): CompletedProcess, ...}
    マッチしない場合は returncode=0 を返す。
    """
    responses = responses or {}

    def _runner(cmd, **kwargs):
        key = tuple(cmd)
        if key in responses:
            return responses[key]
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
    return _runner


def success_process(stdout: str = ""):
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


def failure_process(stderr: str = "error"):
    return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=stderr)


# ── record_pre_publish_head のテスト ─────────────────────────────────────


class TestRecordPrePublishHead:
    def test_git_HEAD_SHAを返す(self, tmp_path):
        sha = "abc123def456" * 3 + "abcd"  # 40 chars
        runner = make_git_runner({
            ("git", "rev-parse", "HEAD"): success_process(stdout=sha + "\n"),
        })
        pub = Publisher(repo_root=tmp_path, git_runner=runner)
        result = pub.record_pre_publish_head()
        assert result == sha

    def test_git失敗でRuntimeError(self, tmp_path):
        runner = make_git_runner({
            ("git", "rev-parse", "HEAD"): failure_process(stderr="not a git repo"),
        })
        pub = Publisher(repo_root=tmp_path, git_runner=runner)
        with pytest.raises(RuntimeError, match="git rev-parse"):
            pub.record_pre_publish_head()


# ── reflect_to_production のテスト ───────────────────────────────────────


class TestReflectToProduction:
    def test_tmp_buildのファイルがコピーされる(self, tmp_path):
        tmp_build = tmp_path / "tmp_build"
        tmp_build.mkdir()
        (tmp_build / "index.html").write_text("<html></html>")
        (tmp_build / "subdir").mkdir()
        (tmp_build / "subdir" / "page.html").write_text("<p>page</p>")

        pub = Publisher(repo_root=tmp_path, tmp_build_dir=tmp_build)
        pub.reflect_to_production()

        assert (tmp_path / "index.html").exists()
        assert (tmp_path / "subdir" / "page.html").exists()

    def test_tmp_buildが存在しないとFileNotFoundError(self, tmp_path):
        pub = Publisher(repo_root=tmp_path, tmp_build_dir=tmp_path / "nonexistent")
        with pytest.raises(FileNotFoundError):
            pub.reflect_to_production()


# ── commit_and_push のテスト ──────────────────────────────────────────────


class TestCommitAndPush:
    def test_全コマンド成功でTrueを返す(self, tmp_path):
        runner = make_git_runner()  # 全コマンドが returncode=0
        pub = Publisher(repo_root=tmp_path, git_runner=runner)
        assert pub.commit_and_push() is True

    def test_commitが失敗するとFalseを返す(self, tmp_path):
        responses = {
            ("git", "add", "."): success_process(),
            ("git", "commit", "-m", "日次翻訳公開"): failure_process(),
        }
        runner = make_git_runner(responses)
        pub = Publisher(repo_root=tmp_path, git_runner=runner)
        assert pub.commit_and_push() is False


# ── rollback のテスト ────────────────────────────────────────────────────


class TestRollback:
    def test_有効なSHAでgit_resetが呼ばれる(self, tmp_path):
        sha = "a" * 40
        called_with = []

        def recording_runner(cmd, **kwargs):
            called_with.append(cmd)
            return success_process()

        pub = Publisher(repo_root=tmp_path, git_runner=recording_runner)
        pub.rollback(sha)
        assert any("reset" in cmd for cmd in called_with)

    def test_空のSHAはValueError(self, tmp_path):
        pub = Publisher(repo_root=tmp_path, git_runner=make_git_runner())
        with pytest.raises(ValueError, match="pre_publish_head"):
            pub.rollback("")

    def test_git_resetが失敗するとRuntimeError(self, tmp_path):
        sha = "a" * 40
        responses = {
            ("git", "reset", "--hard", sha): failure_process(stderr="reset failed"),
        }
        pub = Publisher(repo_root=tmp_path, git_runner=make_git_runner(responses))
        with pytest.raises(RuntimeError, match="git reset"):
            pub.rollback(sha)


# ── cleanup のテスト ────────────────────────────────────────────────────


class TestCleanup:
    def test_tmp_buildが削除される(self, tmp_path):
        tmp_build = tmp_path / "tmp_build"
        tmp_build.mkdir()
        (tmp_build / "file.html").write_text("content")

        pub = Publisher(repo_root=tmp_path, tmp_build_dir=tmp_build)
        pub.cleanup()
        assert not tmp_build.exists()

    def test_tmp_buildが存在しなくてもエラーにならない(self, tmp_path):
        pub = Publisher(repo_root=tmp_path, tmp_build_dir=tmp_path / "nonexistent")
        pub.cleanup()  # 例外が発生しないことを確認
