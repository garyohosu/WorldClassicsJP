"""Publisher の HTML/XML ページ生成テスト（TDD: RED→GREEN サイクル）"""

import pytest
import xml.etree.ElementTree as ET

from worldclassicsjp.models.works_master import WorksMaster
from worldclassicsjp.models.enums import SourceType, LengthClass
from worldclassicsjp.translator import TranslationResult
from worldclassicsjp.publisher import Publisher, AuthorInfo


BASE_URL = "https://example.com/"


# ── フィクスチャ ──────────────────────────────────────────────────────────


def make_work(work_id: int = 1, slug: str = "time-machine",
              title_ja: str = "タイムマシン", author_name_ja: str = "H・G・ウェルズ",
              author_slug: str = "h-g-wells", parts_total: int = 3) -> WorksMaster:
    return WorksMaster(
        work_id=work_id,
        work_slug=slug,
        title=f"The Work {work_id}",
        title_ja=title_ja,
        author_name="H. G. Wells",
        author_name_ja=author_name_ja,
        author_slug=author_slug,
        source_type=SourceType.TEXT_URL,
        source_url="https://gutenberg.org/",
        death_year=1946,
        pd_verified=True,
        length_class=LengthClass.MEDIUM,
        parts_total=parts_total,
    )


def make_pub(tmp_path, base_url: str = BASE_URL) -> Publisher:
    return Publisher(
        repo_root=tmp_path,
        tmp_build_dir=tmp_path / "tmp_build",
        base_url=base_url,
    )


def make_result(text: str = "翻訳済みテキスト", summary: str = "要約") -> TranslationResult:
    return TranslationResult(
        translated_text=text,
        summary=summary,
        keywords=["キーワード"],
    )


# ════════════════════════════════════════════════════════════════════════════
# generate_rss
# ════════════════════════════════════════════════════════════════════════════


class TestGenerateRss:
    def test_rss_xmlファイルが生成される(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.generate_rss([make_work()])
        assert (tmp_path / "tmp_build" / "rss.xml").exists()

    def test_rssが有効なXML(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.generate_rss([make_work()])
        content = (tmp_path / "tmp_build" / "rss.xml").read_text(encoding="utf-8")
        ET.fromstring(content)  # 例外が出なければ有効

    def test_rssのversionが2_0(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.generate_rss([make_work()])
        content = (tmp_path / "tmp_build" / "rss.xml").read_text(encoding="utf-8")
        root = ET.fromstring(content)
        assert root.attrib.get("version") == "2.0"

    def test_rssに作品タイトルが含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.generate_rss([make_work(title_ja="タイムマシン")])
        content = (tmp_path / "tmp_build" / "rss.xml").read_text(encoding="utf-8")
        assert "タイムマシン" in content

    def test_rssに著者名が含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.generate_rss([make_work(author_name_ja="H・G・ウェルズ")])
        content = (tmp_path / "tmp_build" / "rss.xml").read_text(encoding="utf-8")
        assert "H・G・ウェルズ" in content

    def test_rssに作品URLが含まれる(self, tmp_path):
        pub = make_pub(tmp_path, base_url="https://example.com/")
        pub.generate_rss([make_work(slug="time-machine")])
        content = (tmp_path / "tmp_build" / "rss.xml").read_text(encoding="utf-8")
        assert "https://example.com/works/time-machine/" in content

    def test_rssに複数作品のアイテムが含まれる(self, tmp_path):
        works = [
            make_work(work_id=1, slug="work-one", title_ja="作品一"),
            make_work(work_id=2, slug="work-two", title_ja="作品二"),
        ]
        pub = make_pub(tmp_path)
        pub.generate_rss(works)
        content = (tmp_path / "tmp_build" / "rss.xml").read_text(encoding="utf-8")
        assert "作品一" in content
        assert "作品二" in content

    def test_tmp_buildが存在しなくても自動作成される(self, tmp_path):
        pub = make_pub(tmp_path)
        assert not (tmp_path / "tmp_build").exists()
        pub.generate_rss([make_work()])
        assert (tmp_path / "tmp_build" / "rss.xml").exists()


# ════════════════════════════════════════════════════════════════════════════
# generate_sitemap
# ════════════════════════════════════════════════════════════════════════════


class TestGenerateSitemap:
    def test_sitemap_xmlファイルが生成される(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.generate_sitemap([make_work()])
        assert (tmp_path / "tmp_build" / "sitemap.xml").exists()

    def test_sitemapが有効なXML(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.generate_sitemap([make_work()])
        content = (tmp_path / "tmp_build" / "sitemap.xml").read_text(encoding="utf-8")
        ET.fromstring(content)

    def test_sitemapにトップページURLが含まれる(self, tmp_path):
        pub = make_pub(tmp_path, base_url="https://example.com/")
        pub.generate_sitemap([])
        content = (tmp_path / "tmp_build" / "sitemap.xml").read_text(encoding="utf-8")
        assert "https://example.com/" in content

    def test_sitemapに作品ページURLが含まれる(self, tmp_path):
        pub = make_pub(tmp_path, base_url="https://example.com/")
        pub.generate_sitemap([make_work(slug="time-machine")])
        content = (tmp_path / "tmp_build" / "sitemap.xml").read_text(encoding="utf-8")
        assert "https://example.com/works/time-machine/" in content

    def test_sitemapに著者ページURLが含まれる(self, tmp_path):
        pub = make_pub(tmp_path, base_url="https://example.com/")
        pub.generate_sitemap([make_work(author_slug="h-g-wells")])
        content = (tmp_path / "tmp_build" / "sitemap.xml").read_text(encoding="utf-8")
        assert "https://example.com/authors/h-g-wells/" in content


# ════════════════════════════════════════════════════════════════════════════
# build_part_page
# ════════════════════════════════════════════════════════════════════════════


class TestBuildPartPage:
    def test_ファイルが生成される(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_part_page(make_work(), part=1, result=make_result())
        assert (tmp_path / "tmp_build" / "works" / "time-machine" / "part-001" / "index.html").exists()

    def test_翻訳テキストが含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_part_page(make_work(), part=1, result=make_result(text="これはテスト翻訳です。"))
        content = (tmp_path / "tmp_build" / "works" / "time-machine" / "part-001" / "index.html").read_text()
        assert "これはテスト翻訳です。" in content

    def test_作品タイトルが含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_part_page(make_work(title_ja="タイムマシン"), part=1, result=make_result())
        content = (tmp_path / "tmp_build" / "works" / "time-machine" / "part-001" / "index.html").read_text()
        assert "タイムマシン" in content

    def test_著者リンクが含まれる(self, tmp_path):
        pub = make_pub(tmp_path, base_url="https://example.com/")
        pub.build_part_page(make_work(author_slug="h-g-wells"), part=1, result=make_result())
        content = (tmp_path / "tmp_build" / "works" / "time-machine" / "part-001" / "index.html").read_text()
        assert "authors/h-g-wells/" in content

    def test_part番号がゼロ埋めでパスに使われる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_part_page(make_work(), part=5, result=make_result())
        assert (tmp_path / "tmp_build" / "works" / "time-machine" / "part-005" / "index.html").exists()

    def test_HTMLのlang属性がja(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_part_page(make_work(), part=1, result=make_result())
        content = (tmp_path / "tmp_build" / "works" / "time-machine" / "part-001" / "index.html").read_text()
        assert 'lang="ja"' in content

    def test_AdSenseスクリプトが含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_part_page(make_work(), part=1, result=make_result())
        content = (tmp_path / "tmp_build" / "works" / "time-machine" / "part-001" / "index.html").read_text()
        assert "adsbygoogle" in content

    def test_part1の前ページリンクは存在しない(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_part_page(make_work(), part=1, result=make_result())
        content = (tmp_path / "tmp_build" / "works" / "time-machine" / "part-001" / "index.html").read_text()
        assert "part-000" not in content

    def test_目次リンクが含まれる(self, tmp_path):
        pub = make_pub(tmp_path, base_url="https://example.com/")
        pub.build_part_page(make_work(), part=2, result=make_result())
        content = (tmp_path / "tmp_build" / "works" / "time-machine" / "part-002" / "index.html").read_text()
        assert "works/time-machine/" in content


# ════════════════════════════════════════════════════════════════════════════
# build_work_page
# ════════════════════════════════════════════════════════════════════════════


class TestBuildWorkPage:
    def test_ファイルが生成される(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_work_page(make_work(), published_parts=[1, 2])
        assert (tmp_path / "tmp_build" / "works" / "time-machine" / "index.html").exists()

    def test_作品タイトルが含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_work_page(make_work(title_ja="タイムマシン"), published_parts=[1])
        content = (tmp_path / "tmp_build" / "works" / "time-machine" / "index.html").read_text()
        assert "タイムマシン" in content

    def test_公開済みパートのリンクが含まれる(self, tmp_path):
        pub = make_pub(tmp_path, base_url="https://example.com/")
        pub.build_work_page(make_work(), published_parts=[1, 2])
        content = (tmp_path / "tmp_build" / "works" / "time-machine" / "index.html").read_text()
        assert "part-001" in content
        assert "part-002" in content

    def test_著者リンクが含まれる(self, tmp_path):
        pub = make_pub(tmp_path, base_url="https://example.com/")
        pub.build_work_page(make_work(author_slug="h-g-wells", author_name_ja="H・G・ウェルズ"), published_parts=[])
        content = (tmp_path / "tmp_build" / "works" / "time-machine" / "index.html").read_text()
        assert "authors/h-g-wells/" in content

    def test_AdSenseスクリプトが含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_work_page(make_work(), published_parts=[1])
        content = (tmp_path / "tmp_build" / "works" / "time-machine" / "index.html").read_text()
        assert "adsbygoogle" in content


# ════════════════════════════════════════════════════════════════════════════
# build_author_page
# ════════════════════════════════════════════════════════════════════════════


class TestBuildAuthorPage:
    def make_author(self) -> AuthorInfo:
        return AuthorInfo(
            name="H. G. Wells",
            name_ja="H・G・ウェルズ",
            slug="h-g-wells",
            birth_year=1866,
            death_year=1946,
            description="イギリスのSF作家。",
        )

    def test_ファイルが生成される(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_author_page(self.make_author())
        assert (tmp_path / "tmp_build" / "authors" / "h-g-wells" / "index.html").exists()

    def test_著者名が含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_author_page(self.make_author())
        content = (tmp_path / "tmp_build" / "authors" / "h-g-wells" / "index.html").read_text()
        assert "H・G・ウェルズ" in content

    def test_略歴が含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_author_page(self.make_author())
        content = (tmp_path / "tmp_build" / "authors" / "h-g-wells" / "index.html").read_text()
        assert "イギリスのSF作家" in content

    def test_作品リンクが含まれる(self, tmp_path):
        pub = make_pub(tmp_path, base_url="https://example.com/")
        works = [make_work(slug="time-machine", title_ja="タイムマシン")]
        pub.build_author_page(self.make_author(), works=works)
        content = (tmp_path / "tmp_build" / "authors" / "h-g-wells" / "index.html").read_text()
        assert "works/time-machine/" in content
        assert "タイムマシン" in content

    def test_AdSenseスクリプトが含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_author_page(self.make_author())
        content = (tmp_path / "tmp_build" / "authors" / "h-g-wells" / "index.html").read_text()
        assert "adsbygoogle" in content


# ════════════════════════════════════════════════════════════════════════════
# build_index_page
# ════════════════════════════════════════════════════════════════════════════


class TestBuildIndexPage:
    def test_ファイルが生成される(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_index_page([make_work()])
        assert (tmp_path / "tmp_build" / "index.html").exists()

    def test_作品タイトルが含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_index_page([make_work(title_ja="タイムマシン")])
        content = (tmp_path / "tmp_build" / "index.html").read_text()
        assert "タイムマシン" in content

    def test_著者名が含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_index_page([make_work(author_name_ja="H・G・ウェルズ")])
        content = (tmp_path / "tmp_build" / "index.html").read_text()
        assert "H・G・ウェルズ" in content

    def test_作品へのリンクが含まれる(self, tmp_path):
        pub = make_pub(tmp_path, base_url="https://example.com/")
        pub.build_index_page([make_work(slug="time-machine")])
        content = (tmp_path / "tmp_build" / "index.html").read_text()
        assert "works/time-machine/" in content

    def test_複数作品がすべてリストされる(self, tmp_path):
        works = [
            make_work(work_id=1, slug="work-one", title_ja="作品一"),
            make_work(work_id=2, slug="work-two", title_ja="作品二"),
        ]
        pub = make_pub(tmp_path)
        pub.build_index_page(works)
        content = (tmp_path / "tmp_build" / "index.html").read_text()
        assert "作品一" in content
        assert "作品二" in content

    def test_AdSenseスクリプトが含まれる(self, tmp_path):
        pub = make_pub(tmp_path)
        pub.build_index_page([make_work()])
        content = (tmp_path / "tmp_build" / "index.html").read_text()
        assert "adsbygoogle" in content
