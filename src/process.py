"""kc_job_radar — Process: archive + promote + cover_letter + send via Telegram."""

import sys
from pathlib import Path

from .config import load_config
from .archive import archive_rejected
from .refresh import refresh_sheet
from .notify import send_telegram, send_document


def main():
    dry_run = "--dry-run" in sys.argv

    print("⚡ kc_job_radar — Process（封存 + 搬移 + 求職信）")
    if dry_run:
        print("   (dry-run mode)")
    print()

    config = load_config()
    if not config.google_sheet:
        print("❌ 需要 google_sheet 設定")
        sys.exit(1)

    gs = config.google_sheet

    # Step 1: Archive 沒興趣
    print("🗑️ 封存「沒興趣」...")
    if not dry_run:
        archived = archive_rejected(gs)
        if archived:
            print(f"   已封存 {archived} 筆")
        else:
            print("   沒有需要封存的")
    print()

    # Step 2: Promote 想投遞
    print("📤 搬移「想投遞」到追蹤中...")
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("❌ gspread 未安裝")
        sys.exit(1)

    creds = Credentials.from_service_account_file(
        gs.credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(gs.sheet_id)
    ws_radar = sh.worksheet(gs.radar_tab)
    ws_active = sh.worksheet(gs.active_tab)

    all_rows = ws_radar.get_all_values()
    from datetime import date
    today = date.today().strftime("%-m/%-d")

    targets = []
    for i, row in enumerate(all_rows):
        if i == 0:
            continue
        if len(row) >= 2 and "想投遞" in row[1]:
            targets.append((i + 1, row))

    promoted_jobs = []  # (company, title, url, row_num_in_active)
    if targets:
        if dry_run:
            for _, row in targets:
                company = row[2] if len(row) > 2 else ""
                title = row[4] if len(row) > 4 else ""
                print(f"   會搬移: {company} | {title}")
        else:
            rows_to_delete = []
            for row_num, row in targets:
                verdict = row[1] if len(row) > 1 else ""
                company = row[2] if len(row) > 2 else ""
                location = row[3] if len(row) > 3 else ""
                title = row[4] if len(row) > 4 else ""
                salary = row[5] if len(row) > 5 else ""
                url = row[6] if len(row) > 6 else ""
                eval_result = row[7] if len(row) > 7 else ""

                note_parts = [p for p in [verdict, eval_result, url] if p]
                note = " | ".join(note_parts)

                active_row = [today, "", "", company, location, title, salary, "", note, "4_已投遞"]
                ws_active.append_row(active_row)
                rows_to_delete.append(row_num)
                promoted_jobs.append((company, title, url))
                print(f"   ✅ {company} | {title}")

            for row_idx in sorted(rows_to_delete, reverse=True):
                ws_radar.delete_rows(row_idx)

            print(f"   搬移 {len(targets)} 筆")
    else:
        print("   沒有「想投遞」的職缺")
    print()

    # Step 3: Cover Letter for promoted jobs
    if promoted_jobs and not dry_run:
        print("✉️ 產生求職信...")

        resume_path = Path(__file__).parent.parent / "data" / "resume.md"
        if not resume_path.exists():
            print("   ⚠️ 找不到 data/resume.md，跳過求職信")
        else:
            import re
            import random
            import time
            from .detail import fetch_detail, extract_job_id_from_url

            resume = resume_path.read_text(encoding="utf-8")
            output_dir = Path(__file__).parent.parent / "data" / "output"
            context_dir = Path(__file__).parent.parent / "data" / "context"
            output_dir.mkdir(parents=True, exist_ok=True)
            context_dir.mkdir(parents=True, exist_ok=True)

            # Get row numbers for the just-promoted jobs in 追蹤中
            ws_active_values = ws_active.get_all_values()
            active_row_count = len(ws_active_values)

            for idx, (company, title, url) in enumerate(promoted_jobs):
                job_id = extract_job_id_from_url(url) if url else None
                if not job_id:
                    print(f"   ⚠️ {company}: 找不到 job_id")
                    continue

                detail = fetch_detail(job_id)
                if not detail:
                    print(f"   ⚠️ {company}: 職缺已下架")
                    continue

                fname = re.sub(r'[/\\:*?"<>|【】（）\(\)\s]+', '_', f"{company}_{title}")[:60].strip('_')
                output_path = f"data/output/{fname}.txt"
                context_path = context_dir / f"{fname}.md"

                # Row number in 追蹤中 (the ones we just appended)
                row_num = active_row_count - len(promoted_jobs) + idx + 1

                context = f"""# 求職信產生指令

請根據以下履歷和職缺資訊，產生一封求職信。

## 規則
- 繁體中文
- 簡潔，不超過 300 字
- 開頭「您好：」直接切入，不要寒暄
- 誠實列出匹配的技能，沒有的不要灌水
- 強項是「把 AI 能力整合進既有系統架構」，不是純模型研究
- 結尾附上 GitHub（github.com/KerberosClaw）
- 輸出為純文字
- 寫完後存到：{output_path}
- 存完後執行：更新 Google Sheet「追蹤中」tab 第 {row_num} 行 B 欄判定為「📝 待投遞」

## 履歷

{resume}

## 職缺資訊
- 公司：{detail.company}
- 職位：{detail.job_name}
- 產業：{detail.industry}
- 員工數：{detail.employees}
- 薪資：{detail.salary_desc or '面議'}
- 經歷要求：{detail.work_exp}
- 技能需求：{', '.join(detail.specialties)}
- 工作技能：{', '.join(detail.skills)}

### 工作內容
{detail.description}
"""
                context_path.write_text(context, encoding="utf-8")
                print(f"   📄 {fname}.md")

                time.sleep(random.uniform(1, 2))

            print(f"   已產生 {len(promoted_jobs)} 份 context")

            # Send one notification
            if config.telegram:
                companies = "\n".join(f"  • {c} | {t}" for c, t, _ in promoted_jobs)
                send_telegram(
                    config.telegram,
                    f"✉️ 已產生 {len(promoted_jobs)} 份求職信 context\n\n{companies}\n\n檔案在 data/context/，要寫求職信時跟我說",
                )
    print()

    # Step 4: Refresh
    if not dry_run:
        print("🔄 刷新追蹤中...")
        stats = refresh_sheet(gs)
        print(f"   追蹤中：{stats['active']} 筆（進行中 {stats['進行中']} / 追蹤中 {stats['追蹤中']} / 等待中 {stats['等待中']}）")

    print("\n⚡ Process 完成")


if __name__ == "__main__":
    main()
