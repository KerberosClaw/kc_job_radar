"""Deduplication for kc_job_radar — Google Sheet or local CSV."""

import csv
from pathlib import Path

from .config import GoogleSheetConfig
from .models import Job

CSV_PATH = Path(__file__).parent.parent / "radar.csv"


def _load_sheet_keys(gs_config: GoogleSheetConfig) -> set[str]:
    """Load company+title keys from Google Sheet."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("  ⚠️ gspread 未安裝，跳過 Sheet 去重")
        return set()

    creds = Credentials.from_service_account_file(
        gs_config.credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(gs_config.sheet_id)

    keys: set[str] = set()

    # Radar tab: new layout — 公司=col2, 職務=col4
    # 追蹤中/封存: old layout — 公司=col3, 職務=col5
    tab_col_map = {
        gs_config.radar_tab: (2, 4),
        gs_config.active_tab: (3, 5),
        gs_config.archive_tab: (3, 5),
    }

    for tab_name, (company_idx, title_idx) in tab_col_map.items():
        try:
            ws = sh.worksheet(tab_name)
            rows = ws.get_all_values()
            for row in rows[1:]:  # skip header
                if len(row) > max(company_idx, title_idx):
                    company = row[company_idx].strip()
                    title = row[title_idx].strip()
                    if company and title:
                        keys.add(f"{company}|{title}")
        except Exception as e:
            print(f"  ⚠️ 無法讀取 tab「{tab_name}」: {e}")

    return keys


def _load_csv_keys() -> set[str]:
    """Load company+title keys from local CSV."""
    keys: set[str] = set()
    if not CSV_PATH.exists():
        return keys

    with CSV_PATH.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) >= 5:
                company = row[2].strip()
                title = row[4].strip()
                if company and title:
                    keys.add(f"{company}|{title}")

    return keys


def dedup_jobs(jobs: list[Job], gs_config: GoogleSheetConfig | None) -> list[Job]:
    """Remove jobs that already exist in Google Sheet or local CSV."""
    if gs_config:
        print("  讀取 Google Sheet 已有紀錄...")
        existing = _load_sheet_keys(gs_config)
    else:
        print("  讀取本地 CSV 已有紀錄...")
        existing = _load_csv_keys()

    print(f"  已有 {len(existing)} 筆紀錄")

    result = []
    for job in jobs:
        key = f"{job.company}|{job.title}"
        if key not in existing:
            result.append(job)

    return result
