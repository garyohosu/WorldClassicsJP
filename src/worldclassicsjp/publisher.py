"""Publisher — HTML 生成・Git 反映・ロールバック"""

from __future__ import annotations

import shutil
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Protocol


class GitRunner(Protocol):
    """git コマンドのプロトコル（テスト時はモックに差し替え可能）"""
    def __call__(self, cmd: list[str], **kwargs) -> subprocess.CompletedProcess: ...


@dataclass
class AuthorInfo:
    name: str
    name_ja: str
    slug: str
    birth_year: int | None = None
    death_year: int | None = None
    description: str = ""


class Publisher:
    """
    /tmp_build に成果物を生成し、本番パスへ仮反映して git push する。
    失敗時は pre_publish_head へロールバックする。
    """

    def __init__(
        self,
        repo_root: Path,
        tmp_build_dir: Path | None = None,
        base_url: str = "https://example.com/",
        git_runner: GitRunner | None = None,
    ) -> None:
        self.repo_root    = repo_root
        self.tmp_build_dir = tmp_build_dir or (repo_root / "tmp_build")
        self.base_url = base_url.rstrip("/") + "/"
        self._git: GitRunner = git_runner or self._default_git

    # ── ページ生成 ────────────────────────────────────────────────────

    def build_index_page(self, works: list) -> None:
        self._ensure_tmp_build()
        items = "\n".join(
            (
                f'<li><a href="{self._url(f"works/{work.work_slug}/")}">{escape(work.title_ja)}</a> '
                f'<span>{escape(work.author_name_ja)}</span></li>'
            )
            for work in works
        )
        html = self._wrap_html(
            "World Classics JP",
            (
                "<h1>World Classics JP</h1>"
                f"<ul>{items}</ul>"
            ),
        )
        self._write_text(self.tmp_build_dir / "index.html", html)

    def build_work_page(self, work, published_parts: list[int] | None = None) -> None:
        self._ensure_tmp_build()
        published_parts = published_parts or []
        parts = "\n".join(
            (
                f'<li><a href="{self._url(f"works/{work.work_slug}/part-{part:03d}/")}">'
                f"Part {part:03d}</a></li>"
            )
            for part in published_parts
        )
        body = (
            f"<h1>{escape(work.title_ja)}</h1>"
            f'<p><a href="{self._url(f"authors/{work.author_slug}/")}">{escape(work.author_name_ja)}</a></p>'
            f"<ol>{parts}</ol>"
        )
        html = self._wrap_html(work.title_ja, body)
        self._write_text(self.tmp_build_dir / "works" / work.work_slug / "index.html", html)

    def build_part_page(self, work, part: int, result) -> None:
        self._ensure_tmp_build()
        prev_link = ""
        if part > 1:
            prev_link = (
                f'<a href="{self._url(f"works/{work.work_slug}/part-{part - 1:03d}/")}">前へ</a>'
            )
        body = (
            f"<h1>{escape(work.title_ja)}</h1>"
            f'<p><a href="{self._url(f"authors/{work.author_slug}/")}">{escape(work.author_name_ja)}</a></p>'
            f'<p><a href="{self._url(f"works/{work.work_slug}/")}">目次</a></p>'
            f"<nav>{prev_link}</nav>"
            f"<article>{escape(result.translated_text)}</article>"
            f"<section>{escape(result.summary)}</section>"
        )
        html = self._wrap_html(f"{work.title_ja} Part {part:03d}", body)
        self._write_text(
            self.tmp_build_dir / "works" / work.work_slug / f"part-{part:03d}" / "index.html",
            html,
        )

    def build_author_page(self, author, works: list | None = None) -> None:
        self._ensure_tmp_build()
        works = works or []
        years = self._format_years(author.birth_year, author.death_year)
        works_html = "\n".join(
            (
                f'<li><a href="{self._url(f"works/{work.work_slug}/")}">{escape(work.title_ja)}</a></li>'
            )
            for work in works
        )
        body = (
            f"<h1>{escape(author.name_ja)}</h1>"
            f"<p>{escape(author.name)}</p>"
            f"<p>{escape(years)}</p>"
            f"<p>{escape(author.description)}</p>"
            f"<ul>{works_html}</ul>"
        )
        html = self._wrap_html(author.name_ja, body)
        self._write_text(self.tmp_build_dir / "authors" / author.slug / "index.html", html)

    def generate_rss(self, works: list) -> None:
        self._ensure_tmp_build()
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "World Classics JP"
        ET.SubElement(channel, "link").text = self.base_url
        ET.SubElement(channel, "description").text = "Public domain world classics in Japanese."
        for work in works:
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = work.title_ja
            ET.SubElement(item, "link").text = self._url(f"works/{work.work_slug}/")
            ET.SubElement(item, "author").text = work.author_name_ja
            ET.SubElement(item, "description").text = f"{work.title_ja} - {work.author_name_ja}"
        xml = ET.tostring(rss, encoding="unicode")
        self._write_text(self.tmp_build_dir / "rss.xml", xml)

    def generate_sitemap(self, works: list) -> None:
        self._ensure_tmp_build()
        urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        self._append_url(urlset, self.base_url)
        author_slugs: set[str] = set()
        for work in works:
            self._append_url(urlset, self._url(f"works/{work.work_slug}/"))
            if work.author_slug not in author_slugs:
                author_slugs.add(work.author_slug)
                self._append_url(urlset, self._url(f"authors/{work.author_slug}/"))
        xml = ET.tostring(urlset, encoding="unicode")
        self._write_text(self.tmp_build_dir / "sitemap.xml", xml)

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

    def _ensure_tmp_build(self) -> None:
        self.tmp_build_dir.mkdir(parents=True, exist_ok=True)

    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _url(self, path: str) -> str:
        return self.base_url + path.lstrip("/")

    @staticmethod
    def _format_years(birth_year: int | None, death_year: int | None) -> str:
        if birth_year is None and death_year is None:
            return ""
        if birth_year is None:
            return f"?-{death_year}"
        if death_year is None:
            return f"{birth_year}-?"
        return f"{birth_year}-{death_year}"

    @staticmethod
    def _append_url(root: ET.Element, loc: str) -> None:
        url = ET.SubElement(root, "url")
        ET.SubElement(url, "loc").text = loc

    @staticmethod
    def _wrap_html(title: str, body: str) -> str:
        escaped_title = escape(title)
        return (
            "<!doctype html>\n"
            '<html lang="ja">\n'
            "<head>\n"
            '  <meta charset="utf-8">\n'
            f"  <title>{escaped_title}</title>\n"
            '  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>\n'
            "</head>\n"
            "<body>\n"
            f"{body}\n"
            '<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>\n'
            "</body>\n"
            "</html>\n"
        )
