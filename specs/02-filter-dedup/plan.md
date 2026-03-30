# 實作計畫

> **English summary:** Implement filter engine for salary/keyword filtering and optional Google Sheet deduplication.

## 做法

新增 `filter.py` 模組，接收 Job list + Config，依序過薪資篩選 → 排除關鍵字 → Google Sheet 去重。每一步都回報過濾數量。

## 關鍵決策

| 決策 | 選擇 | 理由 |
|------|------|------|
| 薪資解析 | 從 salaryLow/salaryHigh 或 salaryDesc 判斷 | API 回傳兩種格式，都要處理 |
| 去重比對 | 公司名 + 職位名稱 | job_id 在 Sheet 裡沒存，用名稱比對最實際 |
| gspread 依賴 | 動態 import | 沒裝或沒設定就跳過，不影響純篩選功能 |

## 風險

| 風險 | 對策 |
|------|------|
| 薪資格式多變（月薪、年薪、時薪、面議） | 解析函式獨立，不認識的格式當面議處理 |
| Google Sheet API quota | 一次讀全部，不逐筆查 |

## 實作順序

1. filter.py — 薪資篩選 + 排除關鍵字
2. dedup.py — Google Sheet 去重（選填）
3. radar.py 串接 — filter + dedup 整合進 pipeline
