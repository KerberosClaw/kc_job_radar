#!/bin/sh
# Cron entry point — full pipeline with logging and notification

# Load env from Docker (cron doesn't inherit env)
[ -f /app/.env.cron ] && export $(cat /app/.env.cron | xargs)

cd /app

LOG_DIR="/app/data/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/radar_${TIMESTAMP}.log"

{
    echo "=== kc_job_radar cron run: $(date) ==="

    # 0. Clean up previous output (context is cleaned by Claude after writing letters)
    echo "--- cleanup ---"
    rm -f /app/data/output/*.txt /app/data/output/*.zip 2>/dev/null
    echo "已清除上一輪 output"

    # 1. Radar (archive 沒興趣 + search + filter + dedup + write)
    echo "--- radar ---"
    python3 -m src.radar

    # 2. Scout (auto-evaluate new jobs)
    echo "--- scout ---"
    python3 -m src.scout

    # 3. Sort radar (score desc + date desc)
    echo "--- sort ---"
    python3 -c "
from src.config import load_config
from src.sort_radar import sort_radar
config = load_config()
if config.google_sheet:
    count = sort_radar(config.google_sheet)
    print(f'📊 雷達已排序（{count} 筆）')
"

    # 4. Gmail Watch (scan 104 notifications → update Sheet)
    echo "--- gmail_watch ---"
    python3 -m src.gmail_watch

    # 5. Refresh (recalculate days + sort + archive expired)
    echo "--- refresh ---"
    python3 -m src.refresh

    echo "=== done: $(date) ==="
} >> "$LOG_FILE" 2>&1

# 6. Send Telegram notification with summary
python3 -c "
import sys
sys.path.insert(0, '/app')
from src.config import load_config
from src.notify import send_telegram

config = load_config()
if config.telegram:
    with open('$LOG_FILE') as f:
        log = f.read()

    lines = log.split('\n')
    summary_parts = []
    for line in lines:
        if any(kw in line for kw in ['筆不重複', '去重後', '已更新', '追蹤中：', '已封存', '新職缺', '待評估', '已排序', '移至封存']):
            summary_parts.append(line.strip())

    if summary_parts:
        msg = '🔍 Job Radar 自動報告\n\n' + '\n'.join(summary_parts)
        send_telegram(config.telegram, msg)
" 2>> "$LOG_FILE"

# Keep only last 30 days of logs
find "$LOG_DIR" -name "radar_*.log" -mtime +30 -delete 2>/dev/null
