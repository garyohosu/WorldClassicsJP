"""Publisher — HTML 生成・Git 反映・ロールバック"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Protocol


class GitRunner(Protocol):
    """git コマンドのプロトコル（テスト時はモックに差し替え可能）"""
    def __call__(self, cmd: list[str], **kwargs) -> subprocess.CompletedProcess: ...


class Publisher:
    """
    /tmp_build に成果物を生成し、本番パスへ仮反映して git push する。
    失敗時は pre_publish_head へロールバックする。
    """

    def __init__(
        self,
        repo_root: Path,
        tmp_build_dir: Path | None = None,
        git_runner: GitRunner | None = None,
    ) -> None:
        self.repo_root    = repo_root
        self.tmp_build_dir = tmp_build_dir or (repo_root / "tmp_build")
        self._git: GitRunner = git_runner or self._default_git

    # ── ページ生成 ────────────────────────────────────────────────────

    def build_index_page(self, works: list) -> None:
        raise NotImplementedError

    def build_work_page(self, work) -> None:
        raise NotImplementedError

    def build_part_page(self, work, part: int, result) -> None:
        raise NotImplementedError

    def build_author_page(self, author) -> None:
        raise NotImplementedError

    def generate_rss(self, works: list) -> None:
        raise NotImplementedError

    def generate_sitemap(self, works: list) -> None:
        raise NotImplementedError

    # ── 反映・コミット ────────────────────────────────────────────────

    def record_pre_publish_head(self) -> str:
        """現在の git HEAD SHA を返す"""
        result = self._git(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=self.repo_root,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git rev-parse HEAD が失敗しました: {result.stderr.strip()}")
        return result.stdout.strip()

    def reflect_to_production(self) -> None:
        """
        /tmp_build の内容を本番パス（repo_root 直下）へコピーする。
        rss.xml / sitemap.xml は /tmp_build に生成済みであること。
        """
        if not self.tmp_build_dir.exists():
            raise FileNotFoundError(f"/tmp_build が存在しません: {self.tmp_build_dir}")
        for src in self.tmp_build_dir.rglob("*"):
            if src.is_file():
                rel = src.relative_to(self.tmp_build_dir)
                dst = self.repo_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    def commit_and_push(self, message: str = "日次翻訳公開") -> bool:
        """git add / commit / push を実行する。成功した場合 True を返す"""
        for cmd in [
            ["git", "add", "."],
            ["git", "commit", "-m", message],
            ["git", "push", "origin", "main"],
        ]:
            r = self._git(cmd, capture_output=True, text=True, cwd=self.repo_root)
            if r.returncode != 0:
                return False
        return True

    def rollback(self, pre_publish_head: str) -> None:
        """pre_publish_head SHA に git reset して本番パスを復元する"""
        if not pre_publish_head:
            raise ValueError("pre_publish_head が空です。ロールバック不可")
        r = self._git(
            ["git", "reset", "--hard", pre_publish_head],
            capture_output=True, text=True, cwd=self.repo_root,
        )
        if r.returncode != 0:
            raise RuntimeError(f"git reset が失敗しました: {r.stderr.strip()}")

    def cleanup(self) -> None:
        """/tmp_build を削除する"""
        if self.tmp_build_dir.exists():
            shutil.rmtree(self.tmp_build_dir)

    # ── ヘルパー ──────────────────────────────────────────────────────

    @staticmethod
    def _default_git(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, **kwargs)
