# Job Radar -- Because Life's Too Short to Browse 104 Manually

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

[正體中文](README_zh.md)

Job hunting on 104.com.tw is like scrolling through an endless buffet where 90% of the dishes are "salary negotiable" and the rest require mass clicking to find anything relevant. We got tired of manually browsing hundreds of listings, so we built a radar that does the boring part for us.

Automated job radar for [104.com.tw](https://www.104.com.tw) -- search, filter, deduplicate, score, and pipe new matches straight into your Google Sheet. Then write 25 cover letters before your coffee gets cold.

## What It Actually Does

### Phase A -- "Please Stop Making Me Click Through 104 Manually"

| Feature | What It Does |
|---------|-------------|
| Auto-search | Hits 104's public API. We found the endpoint by reading their Vue.js bundle -- the old one is dead |
| Smart filter | Salary floor, location whitelist, keyword blacklist. All config-driven |
| Dedup | Cross-references three Sheet tabs. Same job won't appear twice |
| Sheet writer | New jobs append to "radar" tab. No Sheet? Writes local CSV |
| Caching | 12-hour TTL + config hash. Change keywords, cache auto-invalidates |
| Config-driven | Key exists in `config.yaml` = feature on. Missing = skip. No crashes |

### Phase B -- "It Runs While I Sleep"

| Feature | What It Does |
|---------|-------------|
| Docker | Everything containerized. 8 services, one `build` |
| Cron | Twice-daily: radar, scout, sort, gmail_watch, refresh, notify |
| Gmail watch | Intercepts 104's "resume was read" emails, auto-updates Sheet |
| Telegram | Side-channel push via same bot as Claude Code. One message, not 25 files |
| Auto-refresh | Recalculates days, sorts by priority, archives ghosters after 21 days |
| Claude Code Skill | Say "write letters" in Telegram, AI writes them, zips, sends back |

## Quick Start

```bash
# Clone
git clone https://github.com/KerberosClaw/kc_job_radar.git
cd kc_job_radar

# Install
pip install -r requirements.txt

# Config
cp config.sample.yaml config.yaml
# Edit config.yaml with your search criteria

# Run (dry-run first)
python3 -m src.radar --dry-run

# Run for real
python3 -m src.radar
```

### Claude Code Skill (Optional)

The Telegram interactive commands (write cover letters, run process, etc.) require a Claude Code skill. Install it from [kc_ai_skills](https://github.com/KerberosClaw/kc_ai_skills):

```bash
# Copy the skill to your Claude Code skills directory
cp -r /path/to/kc_ai_skills/job-radar ~/.claude/skills/
```

This is only needed if you want to control kc_job_radar via Telegram through Claude Code. The CLI pipeline and Docker cron work without it.

## Config

Copy `config.sample.yaml` to `config.yaml` and fill in your criteria. The sample file has comments explaining everything, but here's the gist:

```yaml
search:
  keywords:
    - "AI工程師"
    - "軟體架構師"
  areas:
    - ""            # Empty = all regions (104 defaults to relevance sort)
    - "6001008000"  # Taichung
  max_pages: 2

filter:
  min_salary_annual: 1000000  # 1M TWD/year
  accept_negotiable: true
  exclude_keywords:
    - "博弈"
    - "棋牌"
    - "直銷"
```

### Google Sheet (Optional)

Provide a Sheet ID and service account credentials. Tabs (radar, active, archive) are **auto-created with correct headers** on first run -- just give it an empty Sheet:

```yaml
google_sheet:
  sheet_id: "your-sheet-id"
  credentials_path: "credentials.json"
  radar_tab: "雷達"       # Where radar dumps new finds
  active_tab: "追蹤中"    # For dedup + refresh
  archive_tab: "封存"     # For dedup + auto-archive
```

No `google_sheet` config? Results go to a local `radar.csv`. We don't judge.

## Workflow -- "What Do I Actually Do Every Day?"

After cron fills the radar tab with scored jobs, you review them in Google Sheet and mark the verdict column (B) with one of these keywords:

| Keyword | What Happens |
|---------|-------------|
| `沒興趣` | Next run archives it to 封存 tab. Won't appear again |
| `想投遞` | Running `process` moves it to 追蹤中 tab + generates cover letter context |

Everything else (scoring, sorting, new/old detection) is automatic. You just decide: interested or not.

For the **追蹤中 tab**, the status code column (J) drives auto-classification:

| Code | When To Set It |
|------|---------------|
| `1_offer` | You got an offer |
| `2_面試中` | Interview scheduled or waiting for next round |
| `3_已讀` | Set automatically by Gmail watch when company reads your resume |
| `4_已投遞` | Set automatically when promoted from radar. Or set manually after applying |
| `5_感謝函` | You got a rejection letter |
| `6_放棄` | You don't want to pursue this anymore |

`3_已讀` is usually set automatically. The rest you update manually as things progress. Refresh handles the rest (day counting, priority sorting, auto-archiving).

### Telegram Commands (via Claude Code Skill)

If you have the [job-radar skill](https://github.com/KerberosClaw/kc_ai_skills/tree/main/job-radar) installed, tell your Claude Code in Telegram:

| Say This | What Happens |
|----------|-------------|
| 整理雷達 | Archive + promote + generate cover letter context |
| 寫信 | Read context files, write cover letters, zip, send back via Telegram |
| 搜尋職缺 | Run radar pipeline manually |
| 評估雷達 | Score unscored jobs in radar tab |
| 刷新追蹤 | Scan Gmail + recalculate days + sort + auto-archive |

## Architecture -- "Who Does What"

```
Docker cron (automated, no LLM needed):
  radar → scout → sort_radar → gmail_watch → refresh → Telegram notify

Claude Code skill (interactive, via Telegram):
  寫求職信 → read context → write letters → zip → send Telegram
  跑 process → archive + promote + cover_letter
  跑 scout, refresh, radar → docker compose run
```

The split is intentional: everything that can run without a brain, runs without a brain. The stuff that needs judgment (writing cover letters, deciding what to apply to) goes through Claude via Telegram.

## Pipeline

```
104 API → Fetch → Filter → Dedup → Write to Sheet (or CLI)
```

| Stage | What Happens |
|-------|-------------|
| Fetch | Hit 104 search API, multiple keywords x regions, paginate + dedup by job ID |
| Filter | Salary floor + location whitelist + keyword blacklist |
| Dedup | Cross-check against three Sheet tabs (radar / active / archive) |
| Write | Append to "radar" tab, or write to local CSV if no Sheet |

Cache lives in `.cache/`, 12-hour TTL, auto-invalidates when you change config. Because we got burned by stale results exactly once.

## Status Codes -- "How Dead Is This Application?"

The active tracking tab uses status codes (column J) to drive auto-classification:

| Code | Meaning | Display | Priority |
|------|---------|---------|----------|
| `1_offer` | Got an offer | 💰 Offer 在手 | 🟢 Active |
| `2_面試中` | In interview pipeline | 🔥 面試中 | 🟢 Active |
| `3_已讀` | Company read your resume | 🟢 已讀 N天 | 🟢 Tracking |
| `4_已投遞` | Applied, waiting | 📮 剛投(N天) | 🟡 Waiting |
| `5_感謝函` | "Thank you for your interest" | ❌ 感謝函 | Archived |
| `6_放棄` | You gave up on them | ❌ 已放棄 | Archived |

Refresh auto-escalates: >14 days unread = dying, >21 days = dead and archived. The job hunting circle of life, automated.

## Docker Commands

```bash
docker compose run --rm radar        # Search + filter + dedup + write
docker compose run --rm scout        # Score new jobs in radar tab
docker compose run --rm promote      # Move "想投遞" from radar → active
docker compose run --rm process      # Archive + promote + generate cover letter context
docker compose run --rm refresh      # Recalculate days + sort + auto-archive
docker compose run --rm gmail-watch  # Scan Gmail for 104 notifications
docker compose run --rm cover-letter # Generate cover letter context files
```

## Area Codes

For the `areas` field in config. Empty string = search all regions.

| Region | Code |
|--------|------|
| All | `""` |
| Taipei | `6001001000` |
| New Taipei | `6001002000` |
| Taichung | `6001008000` |
| Kaohsiung | `6001014000` |

## Requirements

- Python 3.10+
- httpx, PyYAML
- gspread, google-auth (optional, for Google Sheet)
- google-api-python-client, google-auth-oauthlib (optional, for Gmail)
- Docker + Docker Compose (for Phase B deployment)

## Disclaimer & Security Notice

This is a **personal job-hunting tool**. It does not scrape, crawl, or bypass any authentication. All 104.com.tw data is fetched through public API endpoints with standard rate limiting -- the same requests your browser makes when you search for jobs.

A few things to keep in mind:

- `config.yaml` contains API tokens and credentials -- it's gitignored, but make sure you don't accidentally commit it
- Gmail OAuth tokens are stored locally in `gmail_token.json` -- treat them like passwords
- The 104 API calls use standard HTTP with rate limiting, no authentication bypass or scraping workarounds
- Telegram notifications use the Bot API with your own bot token -- messages go to your private chat only
- All credentials are volume-mounted into Docker containers at runtime, never baked into images

If you find a security issue, please open an issue on GitHub.

## License

MIT
