"""kc_job_radar — Cover Letter: prepare context files for Claude to write cover letters."""

import re
import sys
import random
import time
from pathlib import Path

from .config import load_config
from .detail import fetch_detail, extract_job_id_from_url

DATA_DIR = Path(__file__).parent.parent / "data"
RESUME_PATH = DATA_DIR / "resume.md"
CONTEXT_DIR = DATA_DIR / "context"
OUTPUT_DIR = DATA_DIR / "output"


def _sanitize_filename(s: str) -> str:
    """Remove special chars for filename."""
    s = re.sub(r'[/\\:*?"<>|【】（）\(\)\s]+', '_', s)
    s = s.strip('_')
    return s[:60]  # limit length


def _extract_url(note: str) -> str | None:
    """Extract 104 URL from note field."""
    match = re.search(r'https?://www\.104\.com\.tw/job/\S+', note)
    if match:
        return match.group(0).rstrip('|').strip()
    return None


def main():
    dry_run = "--dry-run" in sys.argv

    print("✉️ kc_job_radar — Cover Letter（求職信 Context 準備）")
    if dry_run:
        print("   (dry-run mode)")
    print()

    config = load_config()

    if not config.google_sheet:
        print("❌ 需要 google_sheet 設定")
        sys.exit(1)

    # Check resume
    if not RESUME_PATH.exists():
        print(f"❌ 找不到履歷：{RESUME_PATH}")
        print(f"   請建立 data/resume.md")
        sys.exit(1)

    resume = RESUME_PATH.read_text(encoding="utf-8")
    print(f"📄 履歷：{RESUME_PATH}（{len(resume)} 字）")

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
    ws = sh.worksheet(gs.active_tab)

    # Find 🆕 雷達推薦
    all_rows = ws.get_all_values()
    # 追蹤中: 日期(0) 判定(1) 優先級(2) 公司(3) 地點(4) 職務(5) 薪水(6) 面試狀況(7) 備註(8)
    targets = []
    for i, row in enumerate(all_rows):
        if i == 0:
            continue
        if len(row) >= 2 and "雷達推薦" in row[1]:
            note = row[8] if len(row) > 8 else ""
            url = _extract_url(note)
            job_id = extract_job_id_from_url(url) if url else None
            company = row[3] if len(row) > 3 else ""
            title = row[5] if len(row) > 5 else ""
            if job_id:
                targets.append((i + 1, company, title, job_id))
            else:
                print(f"  ⚠️ 第 {i+1} 行：找不到 104 URL（{company} | {title}）")

    if not targets:
        print("沒有「🆕 雷達推薦」的職缺。")
        return

    print(f"找到 {len(targets)} 筆\n")

    if dry_run:
        print("📝 Dry Run — 以下會產生 context：\n")
        for row_num, company, title, job_id in targets:
            fname = f"{_sanitize_filename(company)}_{_sanitize_filename(title)}"
            print(f"  {company} | {title}")
            print(f"    → data/context/{fname}.md")
            print(f"    → data/output/{fname}.txt")
            print()
        return

    # Generate context files
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated = []
    for row_num, company, title, job_id in targets:
        print(f"  抓取 JD: {company} | {title} ...", end=" ")

        detail = fetch_detail(job_id)
        if detail is None:
            print("⚠️ 已下架")
            continue

        fname = f"{_sanitize_filename(company)}_{_sanitize_filename(title)}"
        output_path = f"data/output/{fname}.txt"
        context_path = CONTEXT_DIR / f"{fname}.md"

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
        print(f"✅ {context_path.name}")
        generated.append((row_num, company, title, context_path))

        time.sleep(random.uniform(1, 2))

    print(f"\n✉️ 已產生 {len(generated)} 份 context\n")
    print("接下來請在 Claude Code 中執行：")
    print(f"  讀 data/context/ 裡的檔案，照指令寫求職信\n")

    for _, company, title, path in generated:
        print(f"  📄 {path.name}")


if __name__ == "__main__":
    main()
