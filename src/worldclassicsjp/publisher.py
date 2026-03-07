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
    UI.md に基づくモダンな日本語読書 UI を生成する。
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
        """ホームページを生成する"""
        self._ensure_tmp_build()
        
        # 本日の新着 (最新 1 件)
        new_arrival = works[-1] if works else None
        new_arrival_html = ""
        if new_arrival:
            new_arrival_html = f"""
            <div class="glass shadow-pane rounded-3xl p-6 sm:p-10 relative overflow-hidden reveal">
                <p class="text-xs tracking-[0.18em] text-slate mb-2">本日の新着</p>
                <h3 class="jp-title text-2xl sm:text-4xl mb-4">{escape(new_arrival.title_ja)}</h3>
                <p class="text-slate mb-6">{escape(new_arrival.author_name_ja)}</p>
                <a href="{self._url(f"works/{new_arrival.work_slug}/")}" 
                   class="inline-block px-6 py-2.5 rounded-full bg-pine text-white hover:bg-opacity-90 transition-all">
                   今すぐ読む
                </a>
            </div>
            """

        # 連載中作品 (最新 3 件)
        serializing_works = works[-3:] if works else []
        serializing_html = "\n".join(
            f"""
            <div class="rounded-2xl border border-line p-4 bg-paper/70">
                <p class="text-sm font-semibold mb-1">{escape(w.title_ja)}</p>
                <p class="text-xs text-slate">{escape(w.author_name_ja)}</p>
                <a href="{self._url(f"works/{w.work_slug}/")}" class="text-xs text-pine mt-2 inline-block">続きを読む →</a>
            </div>
            """
            for w in serializing_works
        )

        body = f"""
        <section class="max-w-7xl mx-auto px-4 sm:px-6 pt-10 pb-10">
            <div class="mb-10 text-center">
                <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6743751614716161" data-ad-slot="top" data-ad-format="auto" data-full-width-responsive="true"></ins>
            </div>

            {new_arrival_html}
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mt-12 reveal">
                <div>
                    <h3 class="jp-title text-xl mb-4 flex items-center gap-2">
                        <span class="w-1.5 h-6 bg-amber"></span>連載中
                    </h3>
                    <div class="space-y-4">
                        {serializing_html}
                    </div>
                </div>
                <div>
                    <h3 class="jp-title text-xl mb-4 flex items-center gap-2">
                        <span class="w-1.5 h-6 bg-pine"></span>注目作者
                    </h3>
                    <div class="flex flex-wrap gap-2">
                        <a href="{self._url("authors/")}" class="px-4 py-2 rounded-xl border border-line bg-paper/50 hover:border-pine hover:text-pine transition-all">作者一覧へ</a>
                    </div>
                </div>
            </div>

            <div class="mt-12 text-center">
                <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6743751614716161" data-ad-slot="bottom" data-ad-format="auto" data-full-width-responsive="true"></ins>
            </div>
        </section>
        """
        html = self._wrap_html("World Classics JP - 世界文学を日本語で読む", body)
        self._write_text(self.tmp_build_dir / "index.html", html)

    def build_work_page(self, work, published_parts: list[int] | None = None) -> None:
        """作品トップページを生成する"""
        self._ensure_tmp_build()
        published_parts = published_parts or []
        parts_html = "\n".join(
            f"""
            <a href="{self._url(f"works/{work.work_slug}/part-{part:03d}/")}" 
               class="block p-4 rounded-xl border border-line bg-paper/70 hover:border-pine hover:bg-paper transition-all">
               <span class="text-xs text-slate tracking-widest uppercase">Part {part:03d}</span>
               <p class="jp-title mt-1">第 {part} 部</p>
            </a>
            """
            for part in published_parts
        )
        
        body = f"""
        <section class="max-w-4xl mx-auto px-4 sm:px-6 py-10 reveal">
            <nav class="mb-8">
                <a href="{self._url("")}" class="text-slate hover:text-pine">← ホーム</a>
            </nav>
            
            <div class="mb-8 text-center">
                <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6743751614716161" data-ad-slot="top" data-ad-format="auto" data-full-width-responsive="true"></ins>
            </div>

            <div class="glass p-6 sm:p-10 rounded-3xl mb-10">
                <h1 class="jp-title text-3xl sm:text-5xl mb-4">{escape(work.title_ja)}</h1>
                <p class="text-lg text-slate mb-6">
                    著者: <a href="{self._url(f"authors/{work.author_slug}/")}" class="text-pine border-b border-pine/30">{escape(work.author_name_ja)}</a>
                </p>
                <div class="neon-line mb-6"></div>
                <div class="grid grid-cols-2 gap-4 text-sm text-slate">
                    <p>出典: Project Gutenberg</p>
                    <p>状態: 連載中</p>
                </div>
            </div>

            <div class="space-y-4">
                <h3 class="jp-title text-xl mb-6 flex items-center gap-2">
                    <span class="w-1.5 h-6 bg-amber"></span>目次
                </h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {parts_html}
                </div>
            </div>

            <div class="mt-12 text-center">
                <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6743751614716161" data-ad-slot="bottom" data-ad-format="auto" data-full-width-responsive="true"></ins>
            </div>
        </section>
        """
        html = self._wrap_html(work.title_ja, body)
        self._write_text(self.tmp_build_dir / "works" / work.work_slug / "index.html", html)

    def build_part_page(self, work, part: int, result) -> None:
        """本文ページを生成する"""
        self._ensure_tmp_build()
        
        nav_html = f"""
        <div class="flex items-center justify-between gap-4 py-4 border-b border-line mb-8 sticky top-0 bg-paper/80 backdrop-blur-md z-30">
            <div class="flex items-center gap-2">
                <a href="{self._url(f"works/{work.work_slug}/")}" class="px-3 py-1 rounded-full border border-line text-sm hover:border-pine">目次</a>
            </div>
            <div class="flex items-center gap-2 text-sm">
                {f'<a href="{self._url(f"works/{work.work_slug}/part-{part - 1:03d}/")}" class="px-3 py-1 rounded-full border border-line hover:border-pine">前へ</a>' if part > 1 else ''}
                <span class="text-slate">{part} / {work.parts_total if work.parts_total > 0 else '??'}</span>
                <a href="#" class="px-3 py-1 rounded-full border border-line hover:border-pine opacity-30 cursor-not-allowed">次へ</a>
            </div>
        </div>
        """

        # 本文の整形（改行を <p> タグに）
        paragraphs = escape(result.translated_text).split("\n\n")
        # 途中に広告を挟む
        content_parts = []
        for i, p in enumerate(paragraphs):
            if p.strip():
                p_html = p.replace("\n", "<br>")
                content_parts.append(f'<p class="mb-6">{p_html}</p>')
            if i == len(paragraphs) // 2:
                content_parts.append('<div class="my-10 text-center"><ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6743751614716161" data-ad-slot="middle" data-ad-format="auto" data-full-width-responsive="true"></ins></div>')
        
        content_html = "\n".join(content_parts)

        body = f"""
        <article class="max-w-3xl mx-auto px-4 sm:px-6 py-10 reveal">
            <header class="mb-12 text-center">
                <p class="text-xs tracking-[0.2em] text-slate mb-2 uppercase">{escape(work.author_name_ja)}</p>
                <h1 class="jp-title text-2xl sm:text-4xl mb-4">{escape(work.title_ja)}</h1>
                <p class="text-pine tracking-widest font-semibold">第 {part} 部</p>
            </header>

            <div class="mb-8 text-center">
                <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6743751614716161" data-ad-slot="top" data-ad-format="auto" data-full-width-responsive="true"></ins>
            </div>

            {nav_html}

            <div class="leading-9 text-[1.1rem] text-ink font-serif tracking-wide">
                {content_html}
            </div>

            <div class="mt-16 p-6 rounded-2xl border-l-4 border-amber bg-amber/5 text-sm text-slate italic">
                <p>翻訳注記: この翻訳は AI によって自動生成されたものであり、不自然な表現や誤りが含まれている可能性があります。原典の格調高い雰囲気を再現するよう努めていますが、正確な内容は原語版をご参照ください。</p>
            </div>

            <div class="mt-12 flex justify-center gap-4">
                <a href="{self._url(f"authors/{work.author_slug}/")}" class="px-6 py-2 rounded-full border border-line hover:border-pine hover:text-pine transition-all">作者ページへ</a>
                <a href="{self._url(f"works/{work.work_slug}/")}" class="px-6 py-2 rounded-full border border-line hover:border-pine hover:text-pine transition-all">作品目次へ</a>
            </div>

            <div class="mt-12 text-center">
                <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6743751614716161" data-ad-slot="bottom" data-ad-format="auto" data-full-width-responsive="true"></ins>
            </div>
        </article>
        """
        html = self._wrap_html(f"{work.title_ja} 第{part}部", body)
        self._write_text(
            self.tmp_build_dir / "works" / work.work_slug / f"part-{part:03d}" / "index.html",
            html,
        )

    def build_author_page(self, author, works: list | None = None) -> None:
        """作者ページを生成する"""
        self._ensure_tmp_build()
        works = works or []
        years = self._format_years(author.birth_year, author.death_year)
        works_html = "\n".join(
            f"""
            <a href="{self._url(f"works/{w.work_slug}/")}" 
               class="block p-4 rounded-xl border border-line bg-paper/70 hover:border-pine transition-all">
                <p class="jp-title">{escape(w.title_ja)}</p>
                <p class="text-xs text-slate mt-1 italic">{"連載中" if w.parts_total == 0 else "公開済み"}</p>
            </a>
            """
            for w in works
        )
        
        body = f"""
        <section class="max-w-4xl mx-auto px-4 sm:px-6 py-10 reveal">
            <nav class="mb-8 text-sm">
                <a href="{self._url("")}" class="text-slate hover:text-pine">ホーム</a> / 
                <a href="{self._url("authors/")}" class="text-slate hover:text-pine">作者一覧</a>
            </nav>

            <div class="mb-8 text-center">
                <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6743751614716161" data-ad-slot="top" data-ad-format="auto" data-full-width-responsive="true"></ins>
            </div>

            <div class="glass p-6 sm:p-10 rounded-3xl mb-12 flex flex-col md:flex-row gap-8 items-center md:items-start text-center md:text-left">
                <div class="w-32 h-32 sm:w-48 sm:h-48 rounded-2xl bg-line flex items-center justify-center text-slate text-4xl shrink-0">
                    <span class="opacity-30">肖像</span>
                </div>
                <div>
                    <p class="text-xs tracking-[0.2em] text-slate mb-2 uppercase">{escape(author.name)}</p>
                    <h1 class="jp-title text-3xl sm:text-5xl mb-4">{escape(author.name_ja)}</h1>
                    <p class="text-amber font-semibold mb-4">{escape(years)}</p>
                    <p class="text-slate leading-relaxed">{escape(author.description)}</p>
                </div>
            </div>

            <div class="space-y-6">
                <h3 class="jp-title text-xl mb-6 flex items-center gap-2">
                    <span class="w-1.5 h-6 bg-pine"></span>作品一覧
                </h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {works_html}
                </div>
            </div>

            <div class="mt-12 text-center">
                <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6743751614716161" data-ad-slot="bottom" data-ad-format="auto" data-full-width-responsive="true"></ins>
            </div>
        </section>
        """
        html = self._wrap_html(author.name_ja, body)
        self._write_text(self.tmp_build_dir / "authors" / author.slug / "index.html", html)

    def build_authors_list_page(self, authors: list) -> None:
        """作者一覧ページを生成する"""
        self._ensure_tmp_build()
        authors_html = "\n".join(
            f"""
            <a href="{self._url(f"authors/{a.slug}/")}" 
               class="glass p-6 rounded-2xl border border-line hover:border-pine transition-all block group">
                <h4 class="jp-title text-xl group-hover:text-pine transition-colors">{escape(a.name_ja)}</h4>
                <p class="text-xs text-slate mt-1 uppercase tracking-wider">{escape(a.name)}</p>
            </a>
            """
            for a in authors
        )
        body = f"""
        <section class="max-w-7xl mx-auto px-4 sm:px-6 py-10 reveal">
            <header class="mb-12">
                <p class="text-xs tracking-[0.2em] text-slate mb-2 uppercase">Library</p>
                <h1 class="jp-title text-3xl sm:text-5xl">作者一覧</h1>
            </header>

            <div class="mb-8 text-center">
                <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6743751614716161" data-ad-slot="top" data-ad-format="auto" data-full-width-responsive="true"></ins>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {authors_html}
            </div>

            <div class="mt-12 text-center">
                <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6743751614716161" data-ad-slot="bottom" data-ad-format="auto" data-full-width-responsive="true"></ins>
            </div>
        </section>
        """
        html = self._wrap_html("作者一覧 - World Classics JP", body)
        self._write_text(self.tmp_build_dir / "authors" / "index.html", html)

    def build_about_page(self) -> None:
        """このサイトについてページを生成する"""
        self._ensure_tmp_build()
        body = f"""
        <section class="max-w-3xl mx-auto px-4 sm:px-6 py-10 reveal">
            <header class="mb-12">
                <p class="text-xs tracking-[0.2em] text-slate mb-2 uppercase">About</p>
                <h1 class="jp-title text-3xl sm:text-5xl">このサイトについて</h1>
            </header>

            <div class="glass p-6 sm:p-10 rounded-3xl space-y-8 leading-relaxed">
                <div>
                    <h3 class="jp-title text-xl mb-4 text-pine">プロジェクトの目的</h3>
                    <p>WorldClassicsJP は、パブリックドメインとなった世界文学の至宝を、最新の AI 技術を用いて日本語に翻訳し、広く公開する実験的なプロジェクトです。言語の壁を取り払い、時代を超えて愛される名作を現代の日本語読者に届けることを目指しています。</p>
                </div>

                <div>
                    <h3 class="jp-title text-xl mb-4 text-pine">パブリックドメイン方針</h3>
                    <p>当サイトで公開している作品は、すべて日本国内および原産国においてパブリックドメイン（著作権保護期間が満了したもの）であることを確認しています。Project Gutenberg などの信頼できるソースから取得したテキストを使用しています。</p>
                </div>

                <div>
                    <h3 class="jp-title text-xl mb-4 text-amber">AI 翻訳に関する免責事項</h3>
                    <p>本サイトの翻訳は、大規模言語モデル（LLM）を用いて生成されています。文脈の理解や表現の美しさを追求していますが、時に誤訳や不自然な表現、時代背景にそぐわない解釈が含まれる場合があります。本サイトは「AI による翻訳の可能性」を探求するものであり、翻訳の完全な正確性を保証するものではありません。</p>
                </div>
                
                <div class="pt-6 border-t border-line text-sm text-slate">
                    <p>運営: WorldClassicsJP チーム</p>
                    <p>リポジトリ: <a href="https://github.com/garyohosu/WorldClassicsJP" class="text-pine underline">GitHub</a></p>
                </div>
            </div>
        </section>
        """
        html = self._wrap_html("このサイトについて - World Classics JP", body)
        self._write_text(self.tmp_build_dir / "about" / "index.html", html)

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
        self._append_url(urlset, self._url("authors/"))
        self._append_url(urlset, self._url("about/"))
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
        # 1. git add
        r = self._git(["git", "add", "."], capture_output=True, text=True, cwd=self.repo_root)
        if r.returncode != 0:
            return False

        # 2. git commit
        r = self._git(["git", "commit", "-m", message], capture_output=True, text=True, cwd=self.repo_root)
        if r.returncode != 0:
            # "nothing to commit" なら続行 (push はスキップして成功扱い)
            if "nothing to commit" in r.stdout or "nothing to commit" in r.stderr:
                return True
            return False

        # 3. git push
        r = self._git(["git", "push", "origin", "main"], capture_output=True, text=True, cwd=self.repo_root)
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

    def _wrap_html(self, title: str, body: str) -> str:
        escaped_title = escape(title)
        return f"""<!doctype html>
<html lang="ja">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escaped_title} | WorldClassicsJP</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@500;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">

    <script src="https://cdn.tailwindcss.com"></script>
    <script>
    tailwind.config = {{
        theme: {{
            extend: {{
                colors: {{
                    ink: '#14110f',
                    mist: '#f5f0e6',
                    paper: '#fffdf8',
                    line: '#dfd4bf',
                    pine: '#0d6157',
                    amber: '#c06d1b',
                    slate: '#6f6555'
                }},
                boxShadow: {{
                    pane: '0 18px 40px rgba(35, 23, 10, 0.12)'
                }}
            }}
        }}
    }}
    </script>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
    <script src="https://unpkg.com/@studio-freight/lenis@1.0.42/bundled/lenis.min.js"></script>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6743751614716161" crossorigin="anonymous"></script>

    <style>
    body {{
        font-family: 'Zen Kaku Gothic New', sans-serif;
        background: #f3ecdd;
        color: #14110f;
    }}
    .jp-title {{ font-family: 'Shippori Mincho B1', serif; }}
    .glass {{
        background: linear-gradient(145deg, rgba(255,253,247,.9), rgba(255,249,236,.78));
        border: 1px solid rgba(223,212,191,.9);
        backdrop-filter: blur(8px);
    }}
    .neon-line {{
        background: linear-gradient(90deg, transparent, rgba(13,97,87,.7), rgba(192,109,27,.6), transparent);
        height: 1px;
    }}
    </style>
</head>
<body class="bg-[#f8f2e8] min-h-screen overflow-x-hidden">
    <header class="sticky top-0 z-40 border-b border-line/70 bg-paper/80 backdrop-blur-xl">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
            <a href="{self._url("")}" class="block">
                <p class="text-xs tracking-[0.18em] text-slate uppercase">WorldClassicsJP</p>
                <h1 class="jp-title text-xl">世界文学の至宝</h1>
            </a>
            <nav class="hidden md:flex items-center gap-4 text-sm font-medium">
                <a href="{self._url("")}" class="hover:text-pine transition-colors">ホーム</a>
                <a href="{self._url("authors/")}" class="hover:text-pine transition-colors">作者一覧</a>
                <a href="{self._url("about/")}" class="hover:text-pine transition-colors">このサイトについて</a>
            </nav>
        </div>
    </header>

    <main>
        {body}
    </main>

    <footer class="py-12 border-t border-line/50 mt-12 bg-paper/50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row justify-between items-center gap-6">
            <div class="text-center md:text-left">
                <p class="jp-title text-lg mb-2">WorldClassicsJP</p>
                <p class="text-xs text-slate">パブリックドメイン文学を AI で日本語に。</p>
            </div>
            <div class="flex gap-6 text-sm text-slate">
                <a href="{self._url("")}" class="hover:text-pine">ホーム</a>
                <a href="{self._url("authors/")}" class="hover:text-pine">作者一覧</a>
                <a href="{self._url("about/")}" class="hover:text-pine">このサイトについて</a>
            </div>
            <p class="text-[10px] text-slate/50">© 2026 WorldClassicsJP Project. Works are in public domain.</p>
        </div>
    </footer>

    <script>
    gsap.registerPlugin(ScrollTrigger);
    const lenis = new Lenis({{
        duration: 1.2,
        smoothWheel: true
    }});
    function raf(time) {{
        lenis.raf(time);
        requestAnimationFrame(raf);
    }}
    requestAnimationFrame(raf);

    gsap.utils.toArray('.reveal').forEach((el) => {{
        gsap.from(el, {{
            y: 30,
            opacity: 0,
            duration: 0.8,
            ease: 'power2.out',
            scrollTrigger: {{
                trigger: el,
                start: 'top 85%'
            }}
        }});
    }});
    (adsbygoogle = window.adsbygoogle || []).push({{}});
    </script>
</body>
</html>
"""
