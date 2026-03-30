"""Auto-create Google Sheet tabs with correct headers if they don't exist."""

from .config import GoogleSheetConfig

TABS = {
    "radar": {
        "headers": ["日期", "判定", "公司", "地點", "職務", "薪水", "備註", "評估結果"],
    },
    "active": {
        "headers": ["日期", "判定", "優先級", "公司", "地點", "職務", "薪水", "面試狀況", "備註", "狀態碼"],
    },
    "archive": {
        "headers": ["日期", "判定", "優先級", "公司", "地點", "職務", "薪水", "面試狀況", "備註"],
    },
}


def ensure_tabs(gs_config: GoogleSheetConfig) -> None:
    """Create missing tabs with headers. Safe to call multiple times."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return

    creds = Credentials.from_service_account_file(
        gs_config.credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(gs_config.sheet_id)

    existing = [ws.title for ws in sh.worksheets()]

    tab_map = {
        "radar": gs_config.radar_tab,
        "active": gs_config.active_tab,
        "archive": gs_config.archive_tab,
    }

    created = []
    for key, tab_name in tab_map.items():
        if tab_name not in existing:
            headers = TABS[key]["headers"]
            ws = sh.add_worksheet(title=tab_name, rows=1000, cols=len(headers))
            ws.update(values=[headers], range_name="A1")
            created.append(tab_name)

    if created:
        print(f"📋 自動建立 tab: {', '.join(created)}")
