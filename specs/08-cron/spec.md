# Cron 排程 — B2

> **English summary:** Add cron scheduling inside Docker container to run radar pipeline twice daily on Mac Mini, with logging.

## 背景

B1 Docker 容器化完成，目前是手動 `docker compose run`。需要改成常駐容器 + 內建 cron，每天自動跑兩次 radar。

## 驗收條件

- [ ] AC-1: docker-compose.yml 新增 `cron` service，常駐運行
- [ ] AC-2: 容器內 cron 每天跑兩次 radar（建議 09:00 和 18:00）
- [ ] AC-3: 執行日誌寫到 `data/logs/`，含時間戳和結果摘要
- [ ] AC-4: cron 執行的是完整 pipeline：封存「沒興趣」→ fetch → filter → dedup → 寫入雷達
- [ ] AC-5: 手動 service（radar, scout, promote, cover-letter）保留，可獨立執行
- [ ] AC-6: Mac Mini 上 `docker compose up -d cron` 啟動常駐，驗證 cron 有執行

## 不做的事

- 不做 Telegram 通知（B3）
- 不做 Gmail 監聽（B4）
- 不做 OrbStack 開機自動啟動

## 依賴

- B1 Docker 容器化（07-docker）
