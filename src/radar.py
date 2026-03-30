"""kc_job_radar — 104 Job Radar CLI entry point."""

import sys
from dataclasses import asdict

from .config import load_config
from .fetcher import fetch_jobs
from .filter import filter_jobs
from .dedup import dedup_jobs
from .writer import write_to_sheet, write_to_csv, print_jobs_table, print_dry_run
from .cache import (
    load_fetch_cache, save_fetch_cache,
    load_filter_cache, save_filter_cache,
)


def main():
    dry_run = "--dry-run" in sys.argv

    print("🔍 kc_job_radar — 104 Job Radar")
    if dry_run:
        print("   (dry-run mode)")
    print()

    config = load_config()
    print(f"關鍵字: {', '.join(config.search.keywords)}")
    areas_display = [a if a else "全區" for a in config.search.areas]
    print(f"地區: {', '.join(areas_display)}")
    print()

    # Step 0: Ensure tabs exist
    if config.google_sheet:
        from .setup_sheet import ensure_tabs
        ensure_tabs(config.google_sheet)

    # Step 0b: Archive rejected jobs (沒興趣 → 封存)
    if config.google_sheet and not dry_run:
        from .archive import archive_rejected
        archived = archive_rejected(config.google_sheet)
        if archived:
            print(f"🗑️ 已封存 {archived} 筆「沒興趣」的職缺\n")

    search_dict = asdict(config.search)
    filter_dict = asdict(config.filter)

    # Step 1: Fetch (with cache, keyed by search config)
    raw_jobs = load_fetch_cache(search_dict)
    if raw_jobs is None:
        raw_jobs = fetch_jobs(config)
        save_fetch_cache(raw_jobs, search_dict)
    print(f"📊 抓取: {len(raw_jobs)} 筆不重複職缺")

    # Step 2: Filter (with cache, keyed by filter config)
    filtered = load_filter_cache(filter_dict)
    if filtered is None:
        filtered = filter_jobs(raw_jobs, config.filter)
        save_filter_cache(filtered, filter_dict)
    print(f"📋 篩選後: {len(filtered)} 筆")

    # Step 3: Dedup
    final = dedup_jobs(filtered, config.google_sheet)
    print(f"✅ 去重後: {len(final)} 筆新職缺")

    print(f"\n{'='*80}")
    print(f"📈 {len(raw_jobs)} → 篩選 {len(filtered)} → 去重 {len(final)}")
    print(f"{'='*80}\n")

    if not final:
        print("沒有新職缺。")
        return

    # Step 4: Output
    if dry_run:
        print_dry_run(final)
    elif config.google_sheet:
        count = write_to_sheet(final, config.google_sheet)
        print(f"📝 已寫入 {count} 筆到 Google Sheet「{config.google_sheet.radar_tab}」")
    else:
        count = write_to_csv(final)
        print(f"📝 已寫入 {count} 筆到 radar.csv")


if __name__ == "__main__":
    main()
