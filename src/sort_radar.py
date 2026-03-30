"""Sort radar tab by score (descending) then date (descending)."""

import re

from .config import GoogleSheetConfig


def _extract_score(verdict: str) -> float:
    """Extract numeric score from verdict like '🟢 4.2' or '🟡 3.1'."""
    m = re.search(r"[\d.]+", verdict)
    return float(m.group()) if m else 0.0


def _date_sort_key(date_str: str) -> str:
    """Convert M/D to sortable string like '0330'."""
    parts = date_str.strip().split("/")
    if len(parts) == 2:
        try:
            return f"{int(parts[0]):02d}{int(parts[1]):02d}"
        except ValueError:
            pass
    return "0000"


def sort_radar(gs_config: GoogleSheetConfig) -> int:
    """Sort radar tab by score desc, then date desc. Returns row count."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_file(
        gs_config.credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(gs_config.sheet_id)
    ws = sh.worksheet(gs_config.radar_tab)

    all_rows = ws.get_all_values()
    if len(all_rows) <= 1:
        return 0

    header = all_rows[0]
    data = all_rows[1:]

    # Sort: score desc, then date desc
    data.sort(key=lambda r: (
        -_extract_score(r[1] if len(r) > 1 else ""),
        -int(_date_sort_key(r[0] if len(r) > 0 else "")),
    ))

    # Rewrite
    ws.clear()
    ws.update(values=[header] + data, range_name="A1")

    return len(data)
