# Sheet Writer — 寫入 Google Sheet + CLI 整合

> **English summary:** Write filtered & deduplicated jobs to Google Sheet "追蹤中" tab, or output as CLI table when Sheet is not configured. Complete Phase A integration.

## 背景

01 抓職缺、02 篩選去重都完成了。最後一步：把結果寫進 Google Sheet 或印在終端機。完成後 Phase A 結案。

## 驗收條件

- [ ] AC-1: 有 google_sheet config 時，新職缺 append 到「追蹤中」tab，欄位對應：日期、判定（🆕 雷達）、優先級（空）、公司、地點、職務、薪水、面試狀況（空）、備註（104 URL）
- [ ] AC-2: 不覆蓋既有資料，只 append 新列
- [ ] AC-3: 沒有 google_sheet config 時，結果寫到本地 `radar.csv`
- [ ] AC-4: 加上 --dry-run flag，印出會寫入的內容但不實際寫入 Sheet
- [ ] AC-5: 完整 pipeline 跑一次成功：fetch → filter → dedup → write，印出總結

## 不做的事

- 不做通知（Phase B）
- 不做 LLM 評估（Phase B）
- 不更新既有列的狀態

## 依賴

- 01-job-fetcher, 02-filter-dedup
- gspread（選填）
