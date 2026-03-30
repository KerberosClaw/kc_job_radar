"""kc_job_radar — Gmail Watch: scan 104 notification emails and update Sheet."""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from .config import load_config, GmailConfig, GoogleSheetConfig

PROCESSED_PATH = Path(__file__).parent.parent / "data" / "gmail_processed.json"

# Subject patterns
PATTERNS = {
    "read": re.compile(r"您主動應徵(.+?)職務的信函已被讀取"),
    "reply": re.compile(r"(.+?)已回覆您"),
    "reject": re.compile(r"感謝您應徵(.+?)"),
}


def _load_processed() -> set[str]:
    if PROCESSED_PATH.exists():
        return set(json.loads(PROCESSED_PATH.read_text(encoding="utf-8")))
    return set()


def _save_processed(ids: set[str]) -> None:
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_PATH.write_text(json.dumps(sorted(ids), ensure_ascii=False), encoding="utf-8")


def _get_gmail_service(gmail_config: GmailConfig):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    token_path = Path(gmail_config.token_path)
    if not token_path.exists():
        print(f"❌ 找不到 Gmail token：{token_path}")
        print("   請先在本機跑 OAuth 授權取得 token")
        return None

    token_data = json.loads(token_path.read_text(encoding="utf-8"))
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
    )

    # Auto-refresh if expired
    if creds.expired or not creds.valid:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        # Save refreshed token back
        token_data["token"] = creds.token
        token_path.write_text(json.dumps(token_data, indent=2), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def _parse_subject(subject: str) -> tuple[str, str, str] | None:
    """Parse 104 notification subject. Returns (status, company, title) or None."""
    # 已讀: 您主動應徵{公司}{職位}職務的信函已被讀取
    m = PATTERNS["read"].search(subject)
    if m:
        full = m.group(1)
        # company and title are concatenated, no clear delimiter
        # Return full text, we'll fuzzy match against Sheet
        return ("已讀", full, "")

    # TODO: add reply/reject patterns when we see actual emails

    return None


def _find_sheet_row(ws_values: list[list[str]], company_title: str) -> int | None:
    """Find matching row in 追蹤中 tab by fuzzy matching company name."""
    for i, row in enumerate(ws_values):
        if i == 0:
            continue
        if len(row) >= 6:
            company = row[3]  # 公司
            title = row[5]    # 職務
            # Check if company name appears in the subject text
            if company and company in company_title:
                return i + 1  # 1-indexed
    return None


def _update_sheet_status(ws, row_num: int, status: str, date_str: str) -> None:
    """Update 狀態碼 + 面試狀況 columns."""
    # Status code mapping
    code_map = {
        "已讀": "3_已讀",
        "已回覆": "2_面試中",
        "感謝函": "5_感謝函",
    }
    code = code_map.get(status)

    updates = []
    # Update 狀態碼 (J = col 10)
    if code:
        updates.append({"range": f"J{row_num}", "values": [[code]]})
    # Append to 面試狀況 (H = col 8)
    current = ws.cell(row_num, 8).value or ""
    new_status = f"{current}, {date_str}{status}".strip(", ")
    updates.append({"range": f"H{row_num}", "values": [[new_status]]})

    ws.batch_update(updates)


def main():
    dry_run = "--dry-run" in sys.argv

    print("📬 kc_job_radar — Gmail Watch")
    if dry_run:
        print("   (dry-run mode)")
    print()

    config = load_config()

    if not config.gmail:
        print("❌ 缺少 gmail 設定")
        sys.exit(1)

    if not config.google_sheet:
        print("❌ 缺少 google_sheet 設定")
        sys.exit(1)

    # Gmail
    service = _get_gmail_service(config.gmail)
    if not service:
        sys.exit(1)

    # Get unprocessed 104 emails
    processed = _load_processed()
    results = service.users().messages().list(
        userId="me",
        q=f"from:{config.gmail.watch_sender}",
        maxResults=50,
    ).execute()
    messages = results.get("messages", [])

    new_messages = [m for m in messages if m["id"] not in processed]
    if not new_messages:
        print("沒有新的 104 通知信。")
        return

    print(f"找到 {len(new_messages)} 封未處理的通知\n")

    # Parse each email
    updates = []
    for msg in new_messages:
        detail = service.users().messages().get(
            userId="me", id=msg["id"],
            format="metadata", metadataHeaders=["Subject", "Date"],
        ).execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        subject = headers.get("Subject", "")
        date_raw = headers.get("Date", "")

        parsed = _parse_subject(subject)
        if parsed:
            status, company_title, _ = parsed
            # Extract date (approximate)
            date_str = datetime.now().strftime("%-m/%-d")
            updates.append((msg["id"], status, company_title, date_str, subject))
            print(f"  📧 {status}: {company_title}")
        else:
            print(f"  ⚠️ 無法解析: {subject}")
            # Still mark as processed to avoid retrying
            updates.append((msg["id"], None, None, None, subject))

    if dry_run:
        print(f"\n📝 Dry Run — {len([u for u in updates if u[1]])} 筆會更新 Sheet")
        return

    # Connect to Sheet and update
    import gspread
    from google.oauth2.service_account import Credentials

    gs = config.google_sheet
    creds = Credentials.from_service_account_file(
        gs.credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(gs.sheet_id)
    ws = sh.worksheet(gs.active_tab)
    ws_values = ws.get_all_values()

    updated_count = 0
    for msg_id, status, company_title, date_str, subject in updates:
        if status and company_title:
            row_num = _find_sheet_row(ws_values, company_title)
            if row_num:
                _update_sheet_status(ws, row_num, status, date_str)
                updated_count += 1
                print(f"  ✅ 更新 Row {row_num}: {status}")
            else:
                print(f"  ⚠️ 找不到對應列: {company_title}")

    # Mark all as processed
    processed.update(u[0] for u in updates)
    _save_processed(processed)

    print(f"\n📬 已更新 {updated_count} 筆，已處理 {len(updates)} 封信")

    return updated_count


if __name__ == "__main__":
    main()
