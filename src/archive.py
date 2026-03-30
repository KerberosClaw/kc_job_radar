"""Archive jobs marked 沒興趣 from radar tab to 封存 tab."""

import time

from .config import GoogleSheetConfig


def archive_rejected(gs_config: GoogleSheetConfig) -> int:
    """Move rows with 判定=沒興趣 from radar to archive. Returns count.
    Uses batch operations to avoid API rate limits."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return 0

    creds = Credentials.from_service_account_file(
        gs_config.credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(gs_config.sheet_id)
    ws_radar = sh.worksheet(gs_config.radar_tab)
    ws_archive = sh.worksheet(gs_config.archive_tab)

    all_rows = ws_radar.get_all_values()
    header = all_rows[0] if all_rows else []
    keep_rows = []
    archive_rows = []

    for i, row in enumerate(all_rows):
        if i == 0:
            continue
        if len(row) >= 2 and "沒興趣" in row[1]:
            eval_result = row[7] if len(row) > 7 else ""
            note = f"{row[6]} | {eval_result}".strip(" |") if eval_result else row[6] if len(row) > 6 else ""
            archive_rows.append([
                row[0],
                "❌ 沒興趣（雷達）",
                "已結束",
                row[2] if len(row) > 2 else "",
                row[3] if len(row) > 3 else "",
                row[4] if len(row) > 4 else "",
                row[5] if len(row) > 5 else "",
                "",
                note,
            ])
        else:
            keep_rows.append(row)

    if not archive_rows:
        return 0

    # Batch append to archive (with retry for rate limit)
    for attempt in range(3):
        try:
            ws_archive.append_rows(archive_rows)
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"  ⚠️ API rate limit，等 60 秒重試...")
                time.sleep(60)
            else:
                raise

    # Rewrite radar (clear + write is one batch, not N deletes)
    ws_radar.clear()
    ws_radar.update(values=[header] + keep_rows, range_name="A1")

    return len(archive_rows)
