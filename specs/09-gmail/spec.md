# Gmail 監聽 — B4

> **English summary:** Periodically scan Gmail for 104 notification emails, parse status changes (read, reply, rejection), and auto-update Google Sheet tracking tab.

## 背景

104 會寄通知信到 Gmail（寄件人 `104news@ms1.104.com.tw`），目前已確認「已讀」通知格式。需要 cron 定期掃 Gmail，解析信件自動更新 Google Sheet 追蹤中 tab 的狀態。

## 已確認的信件格式

| 狀態 | Subject 格式 |
|------|------------|
| 已讀 | `您主動應徵{公司}{職位}職務的信函已被讀取` |
| 回覆/感謝函 | 待確認（收到後再補） |

## 驗收條件

- [ ] AC-1: 讀取 Gmail，找出 `from:104news@ms1.104.com.tw` 的未處理信件
- [ ] AC-2: 解析 Subject，抽出公司名和職位名稱
- [ ] AC-3: 比對 Google Sheet 追蹤中 tab，找到對應的列
- [ ] AC-4: 更新判定欄位（如「🟡 等待中」→「🟢 已讀」）和面試狀況欄位（加上日期）
- [ ] AC-5: 記錄已處理的 message ID，避免重複處理（存在 `data/gmail_processed.json`）
- [ ] AC-6: 支援 `--dry-run`，印出會更新的內容但不動 Sheet
- [ ] AC-7: CLI 入口 `python3 -m src.gmail_watch`
- [ ] AC-8: 整合進 cron — run_radar.sh 跑完 radar 後接著跑 gmail_watch
- [ ] AC-9: docker-compose 加 gmail 相關 volume mount（gmail_client_secret.json, gmail_token.json）

## 比對邏輯

Subject「您主動應徵**大成長城企業股份有限公司**AI工程師(台北內湖)職務的信函已被讀取」

→ 公司：大成長城企業股份有限公司
→ 職位：AI工程師(台北內湖)
→ 在追蹤中 tab 找「公司」欄包含「大成長城」且「職務」欄包含「AI工程師」的列
→ 更新判定 + 面試狀況

## config 新增

```yaml
gmail:
  client_secret_path: "gmail_client_secret.json"
  token_path: "gmail_token.json"
  watch_sender: "104news@ms1.104.com.tw"
```

## 不做的事

- 不做 Gmail Push Notification（用 cron 掃就好）
- 不做投遞狀態偵測（104 不寄投遞通知信）
- 不處理未知格式的信（log 警告跳過）

## 依賴

- Gmail API（OAuth token 已取得）
- Google Sheet（追蹤中 tab）
- B2 cron（整合進排程）
