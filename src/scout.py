"""kc_job_radar — Scout: batch evaluate jobs marked 需調查."""

import sys
import random
import time

from .config import load_config, ScoutConfig
from .detail import fetch_detail, extract_job_id_from_url
from .scorer import score_job


EVAL_COL = 8  # Column H: 評估結果 (1-indexed)


def main():
    dry_run = "--dry-run" in sys.argv

    print("🔎 kc_job_radar — Scout（輕量評估）")
    if dry_run:
        print("   (dry-run mode)")
    print()

    config = load_config()

    if not config.google_sheet:
        print("❌ scout 需要 google_sheet 設定")
        sys.exit(1)

    if not config.scout:
        print("❌ 缺少 scout 設定（my_skills, red_flags）")
        sys.exit(1)

    # Connect to Sheet
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("❌ gspread 未安裝")
        sys.exit(1)

    gs = config.google_sheet
    creds = Credentials.from_service_account_file(
        gs.credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(gs.sheet_id)
    ws = sh.worksheet(gs.radar_tab)

    # Verify header has 評估結果 at column H
    header = ws.row_values(1)
    if len(header) < EVAL_COL or header[EVAL_COL - 1] != "評估結果":
        while len(header) < EVAL_COL:
            header.append("")
        header[EVAL_COL - 1] = "評估結果"
        ws.update(range_name="1:1", values=[header])
        print("  ✅ 已新增「評估結果」欄位")

    # Find rows with 需調查
    all_rows = ws.get_all_values()
    targets = []
    for i, row in enumerate(all_rows):
        if i == 0:
            continue
        if len(row) >= 2 and "🆕 雷達" in row[1]:
            # Get job URL from 備註 column (index 6)
            url = row[6] if len(row) > 6 else ""
            job_id = extract_job_id_from_url(url)
            if job_id:
                targets.append((i + 1, row, job_id))  # 1-indexed row number
            else:
                print(f"  ⚠️ 第 {i+1} 行：找不到 job_id（URL: {url}）")

    if not targets:
        print("沒有待評估的職缺。")
        return

    print(f"找到 {len(targets)} 筆待評估\n")

    # Evaluate each
    results = []
    for row_num, row, job_id in targets:
        company = row[2] if len(row) > 2 else "?"
        title = row[4] if len(row) > 4 else "?"
        print(f"  評估: {company} | {title} ...", end=" ")

        detail = fetch_detail(job_id)
        if detail is None:
            print("⚠️ 已下架或無法取得")
            results.append((row_num, "⚠️ 已下架", "職缺已下架或無法取得詳情"))
            continue

        score = score_job(detail, config.scout)
        verdict = f"{score.light} {score.total}"
        print(f"{verdict}")

        results.append((row_num, verdict, score.summary))

        # Rate limit
        time.sleep(random.uniform(1, 3))

    # Write back
    print()
    if dry_run:
        print("📝 Dry Run — 評估結果：\n")
        for row_num, verdict, summary in results:
            print(f"  Row {row_num}: {verdict} | {summary}")
    else:
        # Batch update to avoid API rate limit
        batch_updates = []
        for row_num, verdict, summary in results:
            batch_updates.append({
                "range": f"B{row_num}",
                "values": [[verdict]],
            })
            batch_updates.append({
                "range": f"{chr(64 + EVAL_COL)}{row_num}",
                "values": [[summary]],
            })
        ws.batch_update(batch_updates)
        print(f"📝 已更新 {len(results)} 筆評估結果到 Google Sheet")


if __name__ == "__main__":
    main()
