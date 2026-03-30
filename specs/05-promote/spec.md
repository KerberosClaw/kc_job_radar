# Promote — 雷達 → 追蹤中搬移

> **English summary:** Move jobs marked "想投遞" from radar tab to active tracking tab, carrying over verdict and evaluation results into the notes field.

## 背景

使用者在雷達 tab 看完 scout 評估結果後，把有興趣的標為「想投遞」。需要工具把這些職缺搬到「追蹤中」tab，帶上判定和評估結果。

工作流最後一步：scout 評完 → 使用者標「想投遞」→ promote 搬到追蹤中

## 驗收條件

- [ ] AC-1: 讀取雷達 tab，找出判定欄位含「想投遞」的列
- [ ] AC-2: 搬到「追蹤中」tab，欄位對應：
  - 日期：今天
  - 判定：🆕 雷達推薦
  - 優先級：空
  - 公司：從雷達帶過來
  - 地點：從雷達帶過來
  - 職務：從雷達帶過來
  - 薪水：從雷達帶過來
  - 面試狀況：空
  - 備註：「{判定} | {評估結果} | {104 URL}」
- [ ] AC-3: 搬完後從雷達 tab 刪除該列
- [ ] AC-4: 支援 --dry-run，印出會搬的內容但不動 Sheet
- [ ] AC-5: CLI 入口 `python3 -m src.promote`

## 不做的事

- 不做評估（那是 04-scout 的事）
- 不做自動投遞

## 依賴

- Google Sheet（雷達 tab + 追蹤中 tab）
