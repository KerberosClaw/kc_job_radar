"""kc_job_radar — Refresh: classify by status code, sort, auto-archive expired."""

import re
import sys
from datetime import datetime

from .config import load_config, GoogleSheetConfig

STATUS_COL = 9  # J column, 0-indexed


def _classify(row: list[str], today: datetime) -> tuple[str, str]:
    """Classify a row by status code + days. Returns (verdict, priority)."""
    date_col = (row[0] if len(row) > 0 else "").strip()
    code = (row[STATUS_COL] if len(row) > STATUS_COL else "").strip()

    days = _days_since_date(date_col, today)
    days_str = f"{days}天" if days is not None else ""

    # Parse code number
    code_num = 0
    if code and code[0].isdigit():
        code_num = int(code[0])

    # 1_offer
    if code_num == 1:
        return "💰 Offer 在手", "🟢 進行中"

    # 2_面試中
    if code_num == 2:
        return "🔥 面試中", "🟢 進行中"

    # 3_已讀
    if code_num == 3:
        if days is not None:
            if days > 21:
                return f"❌ 已讀{days_str}無回應", "已結束"
            elif days > 14:
                return f"⚠️ 已讀{days_str}", "🟡 快死了"
            else:
                return f"🟢 已讀{days_str}", "🟢 追蹤中"
        return "🟢 已讀", "🟢 追蹤中"

    # 4_已投遞
    if code_num == 4:
        if days is not None:
            if days > 21:
                return f"❌ 投遞{days_str}無回應", "已結束"
            elif days > 14:
                return f"⚠️ 投遞{days_str}未讀", "🟡 快死了"
            else:
                return f"📮 剛投({days_str})", "🟡 等待中"
        return "📮 剛投遞", "🟡 等待中"

    # 5_感謝函
    if code_num == 5:
        return "❌ 感謝函", "已結束"

    # 6_放棄
    if code_num == 6:
        return "❌ 已放棄", "已結束"

    # No code or unknown — treat as 已投遞
    if days is not None:
        if days > 21:
            return f"❌ 投遞{days_str}無回應", "已結束"
        elif days > 14:
            return f"⚠️ 投遞{days_str}未讀", "🟡 快死了"
        else:
            return f"📮 剛投({days_str})", "🟡 等待中"
    return "❓ 待確認", "🟡 等待中"


def _days_since_date(date_str: str, today: datetime) -> int | None:
    if not date_str or "/" not in date_str:
        return None
    try:
        parts = date_str.split("/")
        month, day = int(parts[0]), int(parts[1])
        year = today.year if month <= today.month else today.year - 1
        return (today - datetime(year, month, day)).days
    except (ValueError, IndexError):
        return None


def refresh_sheet(gs_config: GoogleSheetConfig) -> dict:
    """Run refresh on 追蹤中 tab. Returns stats dict."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_file(
        gs_config.credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(gs_config.sheet_id)
    ws = sh.worksheet(gs_config.active_tab)
    rows = ws.get_all_values()

    headers = rows[0]
    data = rows[1:]
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    still_active = []
    newly_archived = []

    for row in data:
        verdict, priority = _classify(row, today)
        updated = list(row)
        while len(updated) < len(headers):
            updated.append("")
        updated[1] = verdict
        updated[2] = priority

        if priority == "已結束":
            newly_archived.append(updated)
        else:
            still_active.append(updated)

    # Sort
    priority_order = {"🟢 進行中": 0, "🟢 追蹤中": 1, "🟡 等待中": 2, "🟡 快死了": 3}

    def _sort_key(row):
        pri = priority_order.get(row[2] if len(row) > 2 else "", 99)
        code = row[STATUS_COL] if len(row) > STATUS_COL else ""
        code_num = int(code[0]) if code and code[0].isdigit() else 9

        # Extract days
        verdict = row[1] if len(row) > 1 else ""
        days_match = re.search(r"(\d+)天", verdict)
        days = int(days_match.group(1)) if days_match else 0

        return (pri, code_num, days)

    still_active.sort(key=_sort_key)

    # Archive
    if newly_archived:
        try:
            archive_ws = sh.worksheet(gs_config.archive_tab)
        except Exception:
            archive_ws = sh.add_worksheet(title=gs_config.archive_tab, rows=1000, cols=len(headers))
            archive_ws.update(values=[headers], range_name="A1")

        archive_ws.append_rows(newly_archived)

    # Rewrite main tab
    ws.clear()
    ws.update(values=[headers] + still_active, range_name="A1")

    stats = {
        "active": len(still_active),
        "archived": len(newly_archived),
        "進行中": sum(1 for r in still_active if r[2] == "🟢 進行中"),
        "追蹤中": sum(1 for r in still_active if r[2] == "🟢 追蹤中"),
        "等待中": sum(1 for r in still_active if r[2] == "🟡 等待中"),
        "快死了": sum(1 for r in still_active if r[2] == "🟡 快死了"),
    }
    return stats


def main():
    dry_run = "--dry-run" in sys.argv

    print("🔄 kc_job_radar — Refresh")
    if dry_run:
        print("   (dry-run 不支援 refresh，因為需要重寫整個 tab）")
        return

    config = load_config()
    if not config.google_sheet:
        print("❌ 缺少 google_sheet 設定")
        sys.exit(1)

    stats = refresh_sheet(config.google_sheet)

    print(f"✅ 追蹤中：{stats['active']} 筆")
    print(f"   🟢 進行中：{stats['進行中']}")
    print(f"   🟢 追蹤中：{stats['追蹤中']}")
    print(f"   🟡 等待中：{stats['等待中']}")
    print(f"   🟡 快死了：{stats['快死了']}")
    if stats["archived"]:
        print(f"📦 {stats['archived']} 筆移至封存")

    return stats


if __name__ == "__main__":
    main()
