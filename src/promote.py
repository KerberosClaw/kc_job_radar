"""kc_job_radar — Promote: move jobs marked 想投遞 from radar to 追蹤中."""

import sys
from datetime import date

from .config import load_config


def main():
    dry_run = "--dry-run" in sys.argv

    print("📤 kc_job_radar — Promote（雷達 → 追蹤中）")
    if dry_run:
        print("   (dry-run mode)")
    print()

    config = load_config()

    if not config.google_sheet:
        print("❌ promote 需要 google_sheet 設定")
        sys.exit(1)

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
    ws_radar = sh.worksheet(gs.radar_tab)
    ws_active = sh.worksheet(gs.active_tab)

    all_rows = ws_radar.get_all_values()
    # Radar columns: 日期(0) 判定(1) 公司(2) 地點(3) 職務(4) 薪水(5) 備註/URL(6) 評估結果(7)
    targets = []
    for i, row in enumerate(all_rows):
        if i == 0:
            continue
        if len(row) >= 2 and "想投遞" in row[1]:
            targets.append((i + 1, row))  # 1-indexed

    if not targets:
        print("沒有標記「想投遞」的職缺。")
        return

    print(f"找到 {len(targets)} 筆「想投遞」\n")

    today = date.today().strftime("%-m/%-d")

    if dry_run:
        print("📝 Dry Run — 以下會搬到追蹤中：\n")
        for row_num, row in targets:
            company = row[2] if len(row) > 2 else ""
            title = row[4] if len(row) > 4 else ""
            verdict = row[1] if len(row) > 1 else ""
            eval_result = row[7] if len(row) > 7 else ""
            print(f"  {company} | {title}")
            print(f"    備註: {verdict} | {eval_result}")
            print()
        return

    # Move to 追蹤中
    rows_to_delete = []
    for row_num, row in targets:
        verdict = row[1] if len(row) > 1 else ""
        company = row[2] if len(row) > 2 else ""
        location = row[3] if len(row) > 3 else ""
        title = row[4] if len(row) > 4 else ""
        salary = row[5] if len(row) > 5 else ""
        url = row[6] if len(row) > 6 else ""
        eval_result = row[7] if len(row) > 7 else ""

        # Build note: 判定 | 評估結果 | URL
        note_parts = [p for p in [verdict, eval_result, url] if p]
        note = " | ".join(note_parts)

        # 追蹤中 columns: 日期 判定 優先級 公司 地點 職務 薪水 面試狀況 備註 狀態碼
        active_row = [
            today,
            "",          # 判定（refresh 會填）
            "",          # 優先級（refresh 會填）
            company,
            location,
            title,
            salary,
            "",          # 面試狀況
            note,
            "4_已投遞",  # 狀態碼
        ]
        ws_active.append_row(active_row)
        rows_to_delete.append(row_num)
        print(f"  ✅ {company} | {title}")

    # Delete from radar (bottom to top)
    for row_idx in sorted(rows_to_delete, reverse=True):
        ws_radar.delete_rows(row_idx)

    print(f"\n📤 已搬移 {len(targets)} 筆到「追蹤中」")

    # Auto refresh to update priorities
    from .refresh import refresh_sheet
    print("\n🔄 自動刷新追蹤中...")
    stats = refresh_sheet(gs)
    print(f"✅ 追蹤中：{stats['active']} 筆（進行中 {stats['進行中']} / 追蹤中 {stats['追蹤中']} / 等待中 {stats['等待中']}）")


if __name__ == "__main__":
    main()
