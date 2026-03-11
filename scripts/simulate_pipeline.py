#!/usr/bin/env python3
"""
パイプラインシミュレーションスクリプト

長編翻訳がパートを正しく進み、作品完了後に次作品へ移行することを検証する。

動作:
  - 本番 data/state.json は変更しない（一時ディレクトリを使用）
  - data/works_master.json は読み取り専用で参照
  - 翻訳は codex CLI なしで実行（フォールバックテキストを利用）
  - git push は無効 (no_git=True)
  - CHUNK_SIZE を大きく設定して短時間で複数作品を処理

使用方法:
  python scripts/simulate_pipeline.py
  python scripts/simulate_pipeline.py --runs 15    # 実行回数を指定
  python scripts/simulate_pipeline.py --chunk 50000 # チャンクサイズ指定
"""

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import worldclassicsjp.run as run_module
from worldclassicsjp.models.state import State
from worldclassicsjp.models.config import Config


# ── デフォルト設定 ────────────────────────────────────────────────
DEFAULT_CHUNK_SIZE = 100_000   # 100k chars/part → Frankenstein(~440k) は約5パートで完了
DEFAULT_MAX_RUNS   = 20


def make_fake_config(chunk_size: int) -> Config:
    return Config(
        host="localhost", port=11434, model="sim",
        daily_max_chars=chunk_size, current_phase=1,
    )


def stub_publisher():
    """Publisher の I/O・git メソッドをすべてスタブ化する"""
    from worldclassicsjp.publisher import Publisher

    originals = {
        "reflect_to_production":    Publisher.reflect_to_production,
        "commit_and_push":          Publisher.commit_and_push,
        "record_pre_publish_head":  Publisher.record_pre_publish_head,
        "cleanup":                  Publisher.cleanup,
        "build_index_page":         Publisher.build_index_page,
        "build_work_page":          Publisher.build_work_page,
        "build_part_page":          Publisher.build_part_page,
        "build_author_page":        Publisher.build_author_page,
        "generate_rss":             Publisher.generate_rss,
        "generate_sitemap":         Publisher.generate_sitemap,
    }

    Publisher.reflect_to_production   = lambda self: None
    Publisher.commit_and_push         = lambda self, message="": True
    Publisher.record_pre_publish_head = lambda self: "sim_sha_dummy"
    Publisher.cleanup                 = lambda self: None
    Publisher.build_index_page        = lambda self, works: None
    Publisher.build_work_page         = lambda self, work, parts=None: None
    Publisher.build_part_page         = lambda self, work, part, result: None
    Publisher.build_author_page       = lambda self, author, works=None: None
    Publisher.generate_rss            = lambda self, works: None
    Publisher.generate_sitemap        = lambda self, works: None

    return originals


def restore_publisher(originals: dict) -> None:
    from worldclassicsjp.publisher import Publisher
    for name, method in originals.items():
        setattr(Publisher, name, method)


def run_simulation(chunk_size: int, max_runs: int) -> None:
    tmpdir = Path(tempfile.mkdtemp(prefix="wcjp_sim_"))
    print(f"[sim] 一時ディレクトリ: {tmpdir}")
    print(f"[sim] チャンクサイズ: {chunk_size:,} chars/part")
    print(f"[sim] 最大実行回数: {max_runs}")
    print()

    # works_master は本番をそのまま使用
    sim_works_path = ROOT / "data" / "works_master.json"

    # state は Frankenstein part-1 からクリーンスタート
    sim_state_path = tmpdir / "state.json"
    state = State.init_default(min_work_id=2)
    state.current_work_id = 2
    state.next_work_id    = 2
    state.current_part    = 1
    state.save(sim_state_path)

    tmp_lock_path = tmpdir / "state.lock"
    tmp_log_dir   = tmpdir / "logs"

    originals = stub_publisher()

    completed_works: list[str] = []
    prev_work_id = 2

    try:
        print("Run  | work_slug                        | Part | has_more | next_wid  | status")
        print("-----|----------------------------------|------|----------|-----------|-------")

        for i in range(1, max_runs + 1):
            date_str = f"2026-04-{i:02d}"

            with patch.object(run_module, "WORKS_MASTER_PATH", sim_works_path), \
                 patch.object(run_module, "STATE_PATH",         sim_state_path), \
                 patch.object(run_module, "LOCK_PATH",          tmp_lock_path), \
                 patch.object(run_module, "LOG_DIR",            tmp_log_dir), \
                 patch.object(run_module, "load_config",        lambda: make_fake_config(chunk_size)):
                result = run_module.run(date_str, no_git=True)

            st = State.load(sim_state_path)
            status = result.get("status", "?")

            # 作品切り替わり検出
            if st.current_work_id != prev_work_id:
                completed_works.append(f"work_id={prev_work_id}")
                prev_work_id = st.current_work_id

            work_slug = result.get("work", "-")[:32]
            part      = result.get("part", "-")
            next_wid  = st.next_work_id

            if status == "ok":
                has_more_flag = "yes" if st.next_work_id == st.current_work_id else "no(done)"
                row = f"{i:4d} | {work_slug:<32} | {str(part):>4} | {has_more_flag:<8} | {next_wid:<9} | ok"
            elif status == "work_complete":
                row = f"{i:4d} | {'(work_complete)':<32} | {'--':>4} | {'--':<8} | {next_wid:<9} | work_complete"
            elif status == "exhausted":
                row = f"{i:4d} | {'(exhausted)':<32} | {'--':>4} | {'--':<8} | {next_wid:<9} | EXHAUSTED"
            else:
                err = str(result.get("error", result))[:50]
                row = f"{i:4d} | {work_slug:<32} | {str(part):>4} | {'--':<8} | {next_wid:<9} | ERROR: {err}"

            print(row)

            if status == "exhausted":
                print()
                print("[sim] all works done")
                break
        else:
            print()
            print(f"[sim] finished after {max_runs} runs")

    finally:
        restore_publisher(originals)
        shutil.rmtree(tmpdir, ignore_errors=True)

    print()
    print("=== Summary ===")
    works_data = json.loads(sim_works_path.read_text(encoding="utf-8"))
    id_to_slug = {w["work_id"]: w["work_slug"] for w in works_data}
    for wid_str in completed_works:
        wid = int(wid_str.split("=")[1])
        print(f"  [done] {id_to_slug.get(wid, wid_str)}")

    st_final = State.load(tmpdir / "state.json") if (tmpdir / "state.json").exists() else None


def main() -> None:
    ap = argparse.ArgumentParser(description="パイプラインシミュレーション")
    ap.add_argument("--runs",  type=int, default=DEFAULT_MAX_RUNS,  help="最大実行回数")
    ap.add_argument("--chunk", type=int, default=DEFAULT_CHUNK_SIZE, help="チャンクサイズ(chars)")
    args = ap.parse_args()
    run_simulation(chunk_size=args.chunk, max_runs=args.runs)


if __name__ == "__main__":
    main()
