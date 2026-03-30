# Job Fetcher — 104 搜尋 API 串接

> **English summary:** Connect to 104.com.tw public search API, fetch job listings by configurable keywords/areas, parse response into structured data, and handle pagination + rate limiting.

## 背景

Phase A 的第一步：確認 104 的公開搜尋 API 能穩定使用，並把回傳資料解析成後續 Filter/Dedup 可以消費的結構。（對應 DESIGN.md Pipeline 第 1 步）

## 驗收條件

- [ ] AC-1: 讀取 config.yaml 的 `search` 區塊（keywords、areas、max_pages），不存在時報錯並提示用戶複製 config.sample.yaml
- [ ] AC-2: 對 `https://www.104.com.tw/jobs/search/list` 發出 GET 請求，帶正確的 query params 和 Referer header，拿到 JSON 回應
- [ ] AC-3: 解析回應的 `data.list` 為 Python dataclass/dict list，至少包含：job_id、職位名稱、公司名稱、地點、薪資描述、104 職缺 URL
- [ ] AC-4: 支援分頁抓取，依 `max_pages` 設定決定最多抓幾頁，遇到空頁提前停止
- [ ] AC-5: 每次請求之間加 random sleep（依 config.yaml 的 `rate_limit`），並輪換 User-Agent
- [ ] AC-6: 多組 keyword 依序搜尋，結果合併後去除重複（同一 job_id 只保留一筆）
- [ ] AC-7: 可以直接 `python3 src/radar.py` 執行，印出抓到的職缺數量和前 5 筆摘要（驗證用）

## 不做的事

- 不做篩選（Filter Engine 是 02-filter-dedup 的事）
- 不做 Google Sheet 串接
- 不做職缺詳情抓取（`/job/ajax/content/{job_id}`），只抓搜尋列表
- 不處理 104 封鎖/驗證碼（遇到就報錯，不繞過）

## 依賴

- Python 3.10+
- httpx
- PyYAML
- config.yaml（從 config.sample.yaml 複製）
