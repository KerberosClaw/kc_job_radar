# 實作計畫

> **English summary:** Implement lightweight job evaluator that fetches 104 job details, scores by salary/company/skill-match/red-flags, and writes results back to Google Sheet radar tab.

## 做法

新增 `src/scout.py`，讀雷達 tab 找「需調查」→ 打 104 詳情 API → 四維度評分 → 寫回 Sheet。config 新增 `scout` 區塊放使用者技能和紅旗關鍵字。

## 關鍵決策

| 決策 | 選擇 | 理由 |
|------|------|------|
| 104 詳情 API | `/job/ajax/content/{job_id}` | 公開 API，回傳完整 JD + 公司資訊 |
| job_id 來源 | 從雷達 tab 備註欄的 104 URL 解析 | 寫入時已存 URL |
| 評分引擎 | 獨立函式，每個維度回傳 1-5 | 方便調權重 |
| 一句話摘要 | 程式組合，不用 LLM | Phase A 不依賴 LLM |

## 風險

| 風險 | 對策 |
|------|------|
| 104 詳情 API 格式不同於搜尋 API | 先打一次看結構 |
| 職缺已下架拿不到詳情 | 跳過，判定標「⚠️ 已下架」 |
| 雷達 tab 沒有「評估結果」欄位 | 自動新增 |

## 實作順序

1. config 新增 scout 區塊（my_skills, red_flags）
2. detail_fetcher — 打 104 詳情 API，解析回傳
3. scorer — 四維度評分 + 加權總分 + 一句話摘要
4. scout.py CLI 入口 — 讀 Sheet → fetch → score → 寫回
