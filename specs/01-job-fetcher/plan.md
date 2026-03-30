# 實作計畫

> **English summary:** Implement a config-driven 104 job search client with pagination, rate limiting, and deduplication across keyword groups.

## 做法

用 httpx 打 104 公開搜尋 API，讀 config.yaml 的搜尋條件，逐組 keyword 分頁抓取，合併去重後輸出結構化資料。入口點 `src/radar.py` 提供 CLI 驗證。

## 關鍵決策

| 決策 | 選擇 | 理由 |
|------|------|------|
| HTTP client | httpx (sync) | Phase A 不需要 async，sync 簡單直接 |
| 資料結構 | dataclass `Job` | 型別明確，後續 filter/writer 好消費 |
| config 載入 | 獨立 `config.py` 模組 | 全專案共用，02/03 spec 也會用 |
| 去重策略 | job_id (104 的短 ID) | 比公司名+職稱精確，從 job link 解析 |

## 風險

| 風險 | 對策 |
|------|------|
| 104 API 回傳格式變動 | 解析層獨立，改一個地方就好 |
| 被 rate limit / 封 IP | sleep 3-8s + UA 輪換，Phase A 量小不太會觸發 |
| config.yaml 不存在 | 啟動時檢查，報錯提示複製 sample |

## 實作順序

1. config 模組 — 載入 yaml、驗證必要欄位
2. Job dataclass — 定義資料結構
3. fetcher 模組 — 打 API、解析回應、分頁、rate limit
4. radar.py 入口 — 串起來，CLI 輸出驗證
