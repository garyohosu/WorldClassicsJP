from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

import requests

from worldclassicsjp.models.config import Config
from worldclassicsjp.models.enums import Stage, WorkStatus
from worldclassicsjp.models.run_log import RunLog
from worldclassicsjp.models.state import State
from worldclassicsjp.models.state_lock import StateLock
from worldclassicsjp.models.works_master import WorksMaster
from worldclassicsjp.publisher import AuthorInfo, Publisher
from worldclassicsjp.translator import TranslationResult

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
LOG_DIR = ROOT / "logs"
WORKS_MASTER_PATH = DATA_DIR / "works_master.json"
STATE_PATH = DATA_DIR / "state.json"
LOCK_PATH = DATA_DIR / "state.lock"
CONFIG_PATH = ROOT / "config.yaml"


def today_jst() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat()


def ensure_seed_data() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not WORKS_MASTER_PATH.exists():
        seed = [
            {
                "work_id": 1,
                "work_slug": "the-raven",
                "title": "The Raven",
                "title_ja": "大鴉",
                "author_name": "Edgar Allan Poe",
                "author_name_ja": "エドガー・アラン・ポー",
                "author_slug": "edgar-allan-poe",
                "source_url": "https://www.gutenberg.org/cache/epub/1065/pg1065.txt",
                "source_type": "text_url",
                "death_year": 1849,
                "pd_verified": True,
                "length_class": "short",
                "parts_total": 1,
            },
            {
                "work_id": 2,
                "work_slug": "frankenstein",
                "title": "Frankenstein",
                "title_ja": "フランケンシュタイン",
                "author_name": "Mary Shelley",
                "author_name_ja": "メアリー・シェリー",
                "author_slug": "mary-shelley",
                "source_url": "https://www.gutenberg.org/cache/epub/84/pg84.txt",
                "source_type": "text_url",
                "death_year": 1851,
                "pd_verified": True,
                "length_class": "long",
                "parts_total": 0,
            },
        ]
        WORKS_MASTER_PATH.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")

    if not STATE_PATH.exists():
        State.init_default(min_work_id=1).save(STATE_PATH)


def load_config() -> Config:
    if CONFIG_PATH.exists():
        return Config.load(CONFIG_PATH)
    return Config(host="localhost", port=11434, model="phi3:mini", daily_max_chars=12000, current_phase=1)


def fetch_source_text(url: str, limit_chars: int, offset: int = 0) -> tuple[str, bool]:
    """テキストを取得し、(chunk, has_more) のタプルを返す"""
    r = requests.get(url, timeout=45, headers={"User-Agent": "WorldClassicsJP/1.0"})
    r.raise_for_status()
    text = r.text
    text = re.sub(r"\*\*\*\s*START OF .*?\*\*\*", "", text, flags=re.I | re.S)
    text = re.sub(r"\*\*\*\s*END OF .*", "", text, flags=re.I | re.S)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    chunk = text[offset:offset + limit_chars]
    has_more = len(text) > offset + limit_chars
    return chunk, has_more


def translate_to_ja(text_en: str, title: str, author: str) -> TranslationResult:
    prompt = (
        "Translate English literary text to natural Japanese. Return JSON with translated_text, summary, keywords.\n"
        f"title={title}\nauthor={author}\n\n{text_en[:9000]}"
    )
    try:
        res = subprocess.run(["codex", "exec", prompt], capture_output=True, text=True, timeout=600)
        if res.returncode == 0 and res.stdout:
            body = res.stdout
            s = body.find("{")
            e = body.rfind("}")
            if s >= 0 and e > s:
                data = json.loads(body[s : e + 1])
                return TranslationResult(
                    translated_text=str(data.get("translated_text", "")).strip(),
                    summary=str(data.get("summary", "")).strip(),
                    keywords=[str(x) for x in data.get("keywords", [])],
                )
    except Exception:
        pass

    return TranslationResult(
        translated_text="（翻訳生成に失敗しました。次回再実行してください）\n\n" + text_en[:1200],
        summary="自動翻訳一時失敗",
        keywords=["文学", "翻訳"],
    )


def run(date_str: str, no_git: bool = False) -> dict:
    ensure_seed_data()
    cfg = load_config()

    lock = StateLock.acquire(LOCK_PATH, run_id=f"run-{date_str}")
    if lock is None:
        return {"status": "locked"}

    run_log = RunLog(run_id=lock.run_id, date=date_str, stage="start", status="running")
    try:
        works = WorksMaster.load_all(WORKS_MASTER_PATH)
        state = State.load(STATE_PATH)

        candidates = [w for w in works if w.pd_verified and w.work_id >= state.next_work_id]
        candidates.sort(key=lambda x: x.work_id)
        if not candidates:
            state.current_work_status = WorkStatus.EXHAUSTED
            state.current_stage = Stage.IDLE
            state.save(STATE_PATH)
            return {"status": "exhausted"}

        w = candidates[0]
        state.current_work_id = w.work_id
        state.current_stage = Stage.TRANSLATE
        state.last_run_id = lock.run_id
        state.save(STATE_PATH)
        lock.heartbeat()

        # 長編作品は current_part のオフセットから取得
        char_offset = (state.current_part - 1) * cfg.daily_max_chars
        source_text, has_more = fetch_source_text(w.source_url, cfg.daily_max_chars, char_offset)

        if not source_text:
            # この作品のテキストは全て処理済み → 次の作品へ
            state.next_work_id = w.work_id + 1
            state.current_part = 1
            state.current_stage = Stage.IDLE
            state.current_work_status = WorkStatus.ACTIVE
            state.save(STATE_PATH)
            return {"status": "work_complete", "work": w.work_slug}

        tr = translate_to_ja(source_text, w.title, w.author_name)

        current_part = state.current_part
        pub = Publisher(repo_root=ROOT, base_url="https://garyohosu.github.io/WorldClassicsJP/")
        pre_head = pub.record_pre_publish_head()
        state.pre_publish_head = pre_head
        state.current_stage = Stage.PUBLISH
        state.save(STATE_PATH)

        published = [x for x in works if x.pd_verified and x.work_id <= w.work_id]
        pub.build_index_page(published)
        for pw in published:
            auth = AuthorInfo(name=pw.author_name, name_ja=pw.author_name_ja, slug=pw.author_slug, death_year=pw.death_year)
            same = [x for x in published if x.author_slug == pw.author_slug]
            pub.build_author_page(auth, same)
            if pw.work_id == w.work_id:
                pub.build_work_page(pw, list(range(1, current_part + 1)))
                pub.build_part_page(pw, current_part, tr)
            else:
                pub.build_work_page(pw, [1])
        pub.generate_rss(published)
        pub.generate_sitemap(published)
        pub.reflect_to_production()

        pushed = False
        if not no_git:
            pushed = pub.commit_and_push(message=f"daily: {date_str} publish {w.work_slug} part-{current_part:03d}")
            if not pushed:
                pub.rollback(pre_head)
                raise RuntimeError("git commit/push failed")

        state.current_stage = Stage.IDLE
        state.current_work_status = WorkStatus.ACTIVE
        state.last_processed_date = date_str
        state.pre_publish_head = ""
        if has_more:
            # まだテキストが残っている → 同じ作品の次のパートへ
            state.next_work_id = w.work_id
            state.current_part = current_part + 1
        else:
            # 作品完了 → 次の作品へ
            state.next_work_id = w.work_id + 1
            state.current_part = 1
        state.save(STATE_PATH)
        pub.cleanup()

        run_log.stage = "done"
        run_log.status = "success"
        run_log.save(LOG_DIR / date_str[:4] / date_str[5:7] / date_str[8:10] / f"{lock.run_id}.json")

        return {
            "status": "ok",
            "work": w.work_slug,
            "part": current_part,
            "url": f"https://garyohosu.github.io/WorldClassicsJP/works/{w.work_slug}/part-{current_part:03d}/",
            "git_pushed": pushed,
        }
    except Exception as exc:
        run_log.stage = "error"
        run_log.status = "failed"
        run_log.append({"error": str(exc)})
        run_log.save(LOG_DIR / date_str[:4] / date_str[5:7] / date_str[8:10] / f"{lock.run_id}.json")
        return {"status": "error", "error": str(exc)}
    finally:
        lock.release()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=today_jst())
    ap.add_argument("--no-git", action="store_true")
    args = ap.parse_args()
    print(json.dumps(run(args.date, no_git=args.no_git), ensure_ascii=False))


if __name__ == "__main__":
    main()
