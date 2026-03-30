# Filter & Dedup — 篩選 + Google Sheet 去重

> **English summary:** Filter fetched jobs by salary threshold, exclude keywords, and deduplicate against existing Google Sheet records to produce a list of new, relevant jobs.

## 背景

01-job-fetcher 抓回 458 筆原始職缺，但裡面有大量不符條件的（薪資太低、博弈、已投過的）。需要篩選 + 去重，只留下值得關注的新職缺。（對應 DESIGN.md Pipeline 第 2、3 步）

## 驗收條件

- [ ] AC-1: 薪資篩選 — 年薪 >= min_salary_annual 或「面議」（accept_negotiable=true 時）通過，其餘過濾
- [ ] AC-2: 排除關鍵字 — 職位名稱或公司名稱含 exclude_keywords 任一項的，過濾掉
- [ ] AC-3: Google Sheet 去重 — 有設定 google_sheet 時，讀取「追蹤中」+「封存」兩個 tab，比對公司名+職位名稱，排除已存在的
- [ ] AC-4: Google Sheet 未設定時 — 跳過去重，只做篩選
- [ ] AC-5: 串接 radar.py — 在 fetcher 之後執行 filter + dedup，印出篩選前後的數量變化（如「458 → 篩選後 120 → 去重後 85」）

## 不做的事

- 不做寫入 Google Sheet（那是 03-sheet-writer 的事）
- 不做職缺詳情抓取
- 不做 LLM 評分

## 依賴

- 01-job-fetcher（Job dataclass + fetcher）
- gspread + google-auth（Google Sheet 去重用，選填）
- config.yaml 的 filter + google_sheet 區塊
