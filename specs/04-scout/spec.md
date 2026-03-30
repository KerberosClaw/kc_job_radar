# Scout — 輕量版職缺評估

> **English summary:** Batch-evaluate jobs marked "需調查" in the radar tab by fetching 104 job detail API, scoring them, and writing results back to Google Sheet.

## 背景

雷達 tab 累積了大量職缺，使用者手動把有興趣的標為「需調查」。需要一個輕量版評估工具，從 104 詳情 API 抓職缺完整資訊，快速評分 + 一句話摘要，寫回 Sheet。

工作流：使用者標「需調查」→ 跑 scout → Sheet 更新判定（紅綠燈+分數）+ 評估結果（一句話）

## 驗收條件

- [ ] AC-1: 讀取雷達 tab，找出判定欄位為「需調查」的列
- [ ] AC-2: 對每筆職缺，打 `GET https://www.104.com.tw/job/ajax/content/{job_id}`，取得詳細資訊（工作內容、條件要求、公司資訊、福利等）
- [ ] AC-3: 依據以下維度評分（1-5 分），產出加權總分：
  - 薪資競爭力（JD 薪資 vs 使用者門檻）
  - 公司規模與穩定度（員工人數、產業、上市櫃）
  - 職缺匹配度（JD 關鍵字 vs 使用者技能）
  - 紅旗快篩（排除關鍵字、異常訊號）
- [ ] AC-4: 寫回 Sheet — 判定欄位更新為紅綠燈+分數（🟢 3.8 / 🟡 2.5 / 🔴 1.5），新增「評估結果」欄位寫一句話摘要
- [ ] AC-5: 雷達 tab 若沒有「評估結果」欄位，自動新增
- [ ] AC-6: 支援 `--dry-run`，印出評估結果但不寫入 Sheet
- [ ] AC-7: CLI 入口 `python3 -m src.scout`

## 評分邏輯（細節）

### 薪資競爭力 (權重 30%)
- 年薪 >= 120 萬 → 5
- 年薪 100-120 萬 → 4
- 面議 → 3（未知，給中間值）
- 年薪 80-100 萬 → 2
- 年薪 < 80 萬 → 1

### 公司規模與穩定度 (權重 20%)
- 上市櫃 or 員工 500+ → 5
- 員工 100-500 → 4
- 員工 30-100 → 3
- 員工 10-30 → 2
- 員工 < 10 or 查無資料 → 1

### 職缺匹配度 (權重 30%)
- JD 中出現使用者技能關鍵字的數量（從 config 讀取）
- 5+ 命中 → 5
- 3-4 命中 → 4
- 2 命中 → 3
- 1 命中 → 2
- 0 命中 → 1

### 紅旗快篩 (權重 20%)
- 無紅旗 → 5
- 每命中一個紅旗 -1（最低 1）
- 紅旗：排除關鍵字出現在 JD 內文、薪資異常低、「抗壓」「自我驅動」過多、無明確技術棧

## config 新增

```yaml
scout:
  my_skills:
    - "Python"
    - "Java"
    - "Docker"
    - "AI"
    - "LLM"
    - "RAG"
    - "MCP"
    - "IoT"
    - "MQTT"
    - "微服務"
  red_flags:
    - "抗壓"
    - "自我驅動"
    - "責任制"
    - "彈性工時"
```

## 不做的事

- 不做外部搜尋（不打 Google、PTT、salary.tw）
- 不做完整 Job Scout 報告
- 不搬移資料（那是 05-promote 的事）
- 沒有 google_sheet config 時不執行（scout 依賴 Sheet）

## 依賴

- 104 職缺詳情 API
- Google Sheet（雷達 tab）
- config.yaml 的 scout 區塊
