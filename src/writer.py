"""Output writer for kc_job_radar — Google Sheet or local CSV."""

import csv
from datetime import date
from pathlib import Path

from .config import GoogleSheetConfig
from .models import Job

CSV_PATH = Path(__file__).parent.parent / "radar.csv"
CSV_HEADER = ["日期", "判定", "公司", "地點", "職務", "薪水", "備註", "評估結果"]


def _to_row(job: Job) -> list[str]:
    """Convert Job to Google Sheet row."""
    today = date.today().strftime("%-m/%-d")
    return [
        today,              # 日期
        "🆕 雷達",          # 判定
        job.company,        # 公司
        job.location,       # 地點
        job.title,          # 職務
        job.salary,         # 薪水
        job.url,            # 備註 (104 URL)
        "",                 # 評估結果
    ]


def write_to_sheet(jobs: list[Job], gs_config: GoogleSheetConfig) -> int:
    """Append jobs to Google Sheet. Returns number of rows written."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("  ⚠️ gspread 未安裝，無法寫入 Sheet")
        return 0

    creds = Credentials.from_service_account_file(
        gs_config.credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(gs_config.sheet_id)
    # Create radar tab if not exists
    try:
        ws = sh.worksheet(gs_config.radar_tab)
    except Exception:
        ws = sh.add_worksheet(title=gs_config.radar_tab, rows=1000, cols=9)
        ws.append_row(["日期", "判定", "公司", "地點", "職務", "薪水", "備註", "評估結果"])

    rows = [_to_row(job) for job in jobs]
    if rows:
        ws.append_rows(rows)

    return len(rows)


def write_to_csv(jobs: list[Job]) -> int:
    """Append jobs to local CSV. Creates file with header if not exists."""
    is_new = not CSV_PATH.exists()

    with CSV_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(CSV_HEADER)
        rows = [_to_row(job) for job in jobs]
        writer.writerows(rows)

    return len(rows)


def print_jobs_table(jobs: list[Job], limit: int = 30) -> None:
    """Print jobs as readable CLI output."""
    shown = jobs[:limit]
    for i, job in enumerate(shown, 1):
        print(f"{i:3d}. {job.company}")
        print(f"     {job.title}")
        print(f"     {job.location} | {job.salary}")
        print(f"     {job.url}")
        print()

    if len(jobs) > limit:
        print(f"  ... 還有 {len(jobs) - limit} 筆未顯示")


def print_dry_run(jobs: list[Job]) -> None:
    """Preview what would be written to Sheet."""
    print(f"\n📝 Dry Run — 以下 {len(jobs)} 筆會寫入 Google Sheet：\n")
    print(f"{'公司':<25} {'職位':<35} {'薪資':<15}")
    print("-" * 80)
    for job in jobs[:30]:
        company = job.company[:23] if len(job.company) > 23 else job.company
        title = job.title[:33] if len(job.title) > 33 else job.title
        salary = job.salary[:13] if len(job.salary) > 13 else job.salary
        print(f"{company:<25} {title:<35} {salary:<15}")

    if len(jobs) > 30:
        print(f"\n  ... 還有 {len(jobs) - 30} 筆")
