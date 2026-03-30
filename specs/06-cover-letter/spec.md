# Cover Letter — 求職信 Context 準備器

> **English summary:** Generate self-contained context files (resume + JD + prompt instructions) for each "🆕 雷達推薦" job, enabling any Claude session to produce tailored cover letters.

## 背景

promote 把職缺搬到追蹤中後，需要為每個「🆕 雷達推薦」的職缺寫求職信。腳本負責準備自帶指令的 context 檔，任何 Claude Code session 讀到都能直接產出求職信。

## 驗收條件

- [ ] AC-1: 讀取追蹤中 tab，找出判定為「🆕 雷達推薦」的列
- [ ] AC-2: 從備註欄用 regex 抽出 104 URL，打詳情 API 取得 JD
- [ ] AC-3: 讀取 `data/resume.md`，若不存在則報錯提示並停止
- [ ] AC-4: 對每筆職缺，產出 `data/context/{公司}_{職缺}.md`，內容為自帶 prompt 的 context 檔（格式見下方）
- [ ] AC-5: 支援 `--dry-run`，印出會處理的職缺但不抓 JD 不產檔
- [ ] AC-6: CLI 入口 `python3 -m src.cover_letter`
- [ ] AC-7: `data/` 加進 `.gitignore`

## Context 檔格式

```markdown
# 求職信產生指令

請根據以下履歷和職缺資訊，產生一封求職信。

## 規則
- 繁體中文
- 簡潔，不超過 300 字
- 開頭「您好：」直接切入，不要寒暄
- 誠實列出匹配的技能，沒有的不要灌水
- 強項是「把 AI 能力整合進既有系統架構」，不是純模型研究
- 結尾附上 GitHub（github.com/KerberosClaw）
- 輸出為純文字
- 寫完後存到：{output_path}
- 存完後執行：更新 Google Sheet「追蹤中」tab 第 {row_num} 行判定為「📝 待投遞」

## 履歷
{resume.md 內容}

## 職缺資訊
- 公司：{company}
- 職位：{title}
- 產業：{industry}
- 員工數：{employees}
- 薪資：{salary}
- 經歷要求：{work_exp}
- 技能需求：{specialties}
- 工作內容：
{description}
```

## 使用方式

```bash
# 1. 準備 context
python3 -m src.cover_letter

# 2. 任何 Claude Code session
讀 data/context/ 裡的檔案，照指令做
```

## 不做的事

- 不做 LLM 呼叫
- 不做自動投遞
- 不改追蹤中 tab 的欄位結構（更新狀態由 Claude 執行，寫在 prompt 裡）

## 依賴

- 04-scout 的 detail.py（104 詳情 API）
- Google Sheet（追蹤中 tab）
- data/resume.md（使用者提供）
