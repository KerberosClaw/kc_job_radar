# Job Radar -- 人生苦短，不要手動刷 104

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

[English](README.md)

在 104 上找工作就像逛一個 90% 寫「薪資面議」、剩下的要瘋狂點開才知道在幹嘛的吃到飽餐廳。我們受夠了每天手動點開幾百筆職缺，所以寫了一個雷達幫我們做無聊的部分。

104 人力銀行職缺雷達 -- 自動搜尋、篩選、去重、評分，把新職缺直接灌進你的 Google Sheet。然後在你咖啡還沒涼之前寫完 25 封求職信。

## 它到底做了什麼

### Phase A --「拜託不要再讓我手動瀏覽 104 了」

| 功能 | 說明 |
|------|------|
| 自動搜尋 | 打 104 公開 API 抓職缺。API endpoint 是從 Vue.js bundle 裡挖出來的，舊的已死 |
| 智慧篩選 | 薪資門檻、地區白名單、排除關鍵字。全部 config 驅動 |
| 去重 | 跟 Google Sheet 三個 tab 交叉比對，同職缺不會出現兩次 |
| 寫入 Sheet | 新職缺 append 到「雷達」tab。沒設 Sheet？寫本地 CSV |
| 快取 | 12 小時 TTL + config hash，改條件自動失效 |
| config 驅動 | `config.yaml` 有 key 就啟用，沒有就跳過。不爆炸 |

### Phase B --「我睡覺的時候它在跑」

| 功能 | 說明 |
|------|------|
| Docker | 全部容器化，docker-compose 管 8 個 service |
| Cron | 一天跑兩次：radar → scout → sort → gmail_watch → refresh → notify |
| Gmail 監聽 | 攔截 104 的「履歷已被讀取」通知信，自動更新追蹤表 |
| Telegram | 旁路推送，跟 Claude Code 共用同一個 bot。一則訊息不是 25 個附件 |
| 自動刷新 | 重算天數、排序、超過 21 天自動封存 |
| Claude Code Skill | Telegram 說「寫信」，AI 就寫。讀 context、寫信、zip、傳回來 |

## 快速開始

```bash
# 複製 repo
git clone https://github.com/KerberosClaw/kc_job_radar.git
cd kc_job_radar

# 安裝相依套件
pip install -r requirements.txt

# 設定
cp config.sample.yaml config.yaml
# 依照你的搜尋條件編輯 config.yaml

# 試跑（dry-run）
python3 -m src.radar --dry-run

# 正式執行
python3 -m src.radar
```

### Claude Code Skill（選配）

Telegram 互動指令（寫求職信、整理雷達等）需要安裝 Claude Code skill。從 [kc_ai_skills](https://github.com/KerberosClaw/kc_ai_skills) 取得：

```bash
# 複製 skill 到你的 Claude Code skills 目錄
cp -r /path/to/kc_ai_skills/job-radar ~/.claude/skills/
```

只有透過 Telegram 操作 Claude Code 時才需要。CLI pipeline 和 Docker cron 不需要 skill 也能跑。

## 設定

把 `config.sample.yaml` 複製成 `config.yaml`，裡面有註解說明。重點長這樣：

```yaml
search:
  keywords:
    - "AI工程師"
    - "軟體架構師"
  areas:
    - ""            # 空 = 全區（104 預設按相關度排）
    - "6001008000"  # 台中市
  max_pages: 2

filter:
  min_salary_annual: 1000000  # 年薪 100 萬
  accept_negotiable: true
  exclude_keywords:
    - "博弈"
    - "棋牌"
    - "直銷"
```

### Google Sheet（選填）

丟個 Sheet ID 和 service account credentials 進去。Tab（雷達、追蹤中、封存）**第一次跑時自動建立**，給一個空 Sheet 就好：

```yaml
google_sheet:
  sheet_id: "your-sheet-id"
  credentials_path: "credentials.json"
  radar_tab: "雷達"       # 雷達結果寫入
  active_tab: "追蹤中"    # 去重 + refresh 用
  archive_tab: "封存"     # 去重 + 自動封存用
```

沒設 `google_sheet`？結果寫到本地 `radar.csv`。我們不嫌棄。

## 日常操作 --「我每天到底要幹嘛」

cron 自動把評分好的職缺灌進雷達 tab 後，你去 Google Sheet 看一看，在判定欄（B 欄）填上關鍵字：

| 關鍵字 | 效果 |
|--------|------|
| `沒興趣` | 下次執行時自動搬到封存，不會再出現 |
| `想投遞` | 跑 `process` 時搬到追蹤中 + 產生求職信 context |

其他的（評分、排序、新舊判斷）都是自動的。你只要決定：有沒有興趣。

追蹤中 tab 用**狀態碼（J 欄）**驅動自動分類：

| 狀態碼 | 什麼時候填 |
|--------|----------|
| `1_offer` | 收到 offer |
| `2_面試中` | 約了面試或等下一輪 |
| `3_已讀` | Gmail 監聽自動設定，公司讀了你的履歷 |
| `4_已投遞` | 從雷達搬過來時自動設定，或手動投遞後自己填 |
| `5_感謝函` | 收到感謝函 |
| `6_放棄` | 你不想追了 |

`3_已讀` 通常自動設定。其他的隨著進度手動更新。Refresh 會處理剩下的（算天數、排序、超時封存）。

### Telegram 指令（透過 Claude Code Skill）

裝了 [job-radar skill](https://github.com/KerberosClaw/kc_ai_skills/tree/main/job-radar) 之後，在 Telegram 跟 Claude 說：

| 你說 | 它做 |
|------|------|
| 整理雷達 | 封存沒興趣 + 搬移想投遞 + 產生求職信 context |
| 寫信 | 讀 context、寫求職信、打包 zip、傳回 Telegram |
| 搜尋職缺 | 手動跑一次 radar pipeline |
| 評估雷達 | 評估雷達裡還沒評分的職缺 |
| 刷新追蹤 | 掃 Gmail + 重算天數 + 排序 + 自動封存 |

## 架構 --「誰做什麼事」

```
Docker cron（自動化，不需要 LLM）:
  radar → scout → sort_radar → gmail_watch → refresh → Telegram notify

Claude Code skill（互動式，透過 Telegram 觸發）:
  寫求職信 → read context → write letters → zip → send Telegram
  跑 process → archive + promote + cover_letter
  跑 scout, refresh, radar → docker compose run
```

這個分工是刻意的：能不用腦跑的東西，就不用腦跑。需要判斷的事（寫求職信、決定要不要投）才透過 Telegram 叫 Claude 處理。

## Pipeline

```
104 API → Fetch → Filter → Dedup → Write to Sheet (or CLI)
```

| 階段 | 做了什麼 |
|------|---------|
| Fetch | 打 104 搜尋 API，多關鍵字 x 多地區，分頁抓取 + job ID 去重 |
| Filter | 薪資門檻 + 地區白名單 + 關鍵字黑名單 |
| Dedup | 跟 Sheet 三個 tab 交叉比對（雷達 / 追蹤中 / 封存）|
| Write | 寫到「雷達」tab，沒 Sheet 就印終端機 |

快取存在 `.cache/`，12 小時 TTL，改了 config 自動失效。因為我們被 stale 結果雷過剛好一次。

## 狀態碼 --「這筆應徵到底死了沒」

追蹤中 tab 用狀態碼（J 欄）驅動自動分類：

| 狀態碼 | 意思 | 顯示 | 優先級 |
|--------|------|------|--------|
| `1_offer` | 收到 offer | 💰 Offer 在手 | 🟢 進行中 |
| `2_面試中` | 進面試了 | 🔥 面試中 | 🟢 進行中 |
| `3_已讀` | 公司看了你的履歷 | 🟢 已讀 N天 | 🟢 追蹤中 |
| `4_已投遞` | 投了，在等 | 📮 剛投(N天) | 🟡 等待中 |
| `5_感謝函` | 「感謝你的興趣」| ❌ 感謝函 | 封存 |
| `6_放棄` | 你放棄它了 | ❌ 已放棄 | 封存 |

Refresh 會依天數自動升級：超過 14 天未讀 = 快死了，超過 21 天 = 死了，自動封存。求職的生命週期，自動化版。

## Docker 指令

```bash
docker compose run --rm radar        # 搜尋 + 篩選 + 去重 + 寫入
docker compose run --rm scout        # 評估雷達裡的新職缺
docker compose run --rm promote      # 把「想投遞」從雷達搬到追蹤中
docker compose run --rm process      # 封存 + promote + 產生求職信 context
docker compose run --rm refresh      # 重算天數 + 排序 + 自動封存
docker compose run --rm gmail-watch  # 掃 Gmail 的 104 通知信
docker compose run --rm cover-letter # 產生求職信 context 檔案
```

## 地區代碼

config 裡 `areas` 欄位用的。空字串 = 全區。

| 地區 | 代碼 |
|------|------|
| 全區 | `""` |
| 台北市 | `6001001000` |
| 新北市 | `6001002000` |
| 台中市 | `6001008000` |
| 高雄市 | `6001014000` |

## 專案結構

```
kc_job_radar/
├── src/
│   ├── __init__.py
│   ├── radar.py        # 主程式入口：搜尋 + 篩選 + 去重 + 寫入雷達
│   ├── scout.py        # 職缺評估（規則評分）
│   ├── promote.py      # 雷達 → 追蹤中搬移
│   ├── process.py      # archive + promote + cover_letter 整合
│   ├── cover_letter.py # 求職信 context 產生器
│   ├── gmail_watch.py  # Gmail 監聽 104 通知信
│   ├── refresh.py      # 狀態碼分類 + 天數計算 + 自動封存
│   ├── sort_radar.py   # 雷達排序
│   ├── notify.py       # Telegram 通知
│   ├── config.py       # config 載入
│   ├── fetcher.py      # 104 API 搜尋
│   ├── filter.py       # 篩選引擎
│   ├── dedup.py        # 去重邏輯
│   ├── writer.py       # Sheet 寫入 / CLI 輸出
│   ├── scorer.py       # 評分引擎
│   ├── detail.py       # 職缺詳情抓取
│   ├── archive.py      # 封存邏輯
│   ├── models.py       # 資料模型
│   └── cache.py        # 快取機制
├── scripts/
│   └── run_radar.sh    # Cron 入口腳本
├── docs/
│   └── DESIGN.md       # 設計文件
├── specs/              # Spec-driven 開發文件
├── docker-compose.yml  # Docker 服務定義
├── Dockerfile          # 主 image
├── Dockerfile.cron     # Cron 排程 image
├── config.sample.yaml  # 設定範例
├── crontab             # Cron 排程設定
├── requirements.txt
├── LICENSE
└── README.md
```

## 系統需求

- Python 3.10+
- httpx, PyYAML
- gspread, google-auth（選填，Google Sheet 功能用）
- google-api-python-client, google-auth-oauthlib（選填，Gmail 監聽用）
- Docker + Docker Compose（Phase B 部署用）

## 免責與安全聲明

這是一個**個人求職輔助工具**。不做爬蟲、不繞驗證、不快取 session。所有 104 資料都透過公開 API endpoint 取得，帶標準 rate limiting -- 跟你用瀏覽器搜工作發的是同樣的 request。

幾件事要注意：

- `config.yaml` 裡有 API token 和 credentials -- 已經 gitignore 了，但別手賤 commit 它
- Gmail OAuth token 存在本地的 `gmail_token.json` -- 當密碼看待
- 104 API 呼叫使用標準 HTTP + rate limiting，沒有繞過驗證或暴力爬取
- Telegram 通知用的是你自己的 Bot API token -- 訊息只會送到你的私人對話
- 所有 credentials 都是執行時 volume mount 進 Docker 容器，不會 bake 進 image

發現安全問題請到 GitHub 開 issue。

## 授權

MIT
