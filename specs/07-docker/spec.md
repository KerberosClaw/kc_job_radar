# Docker 容器化 — B1

> **English summary:** Containerize kc_job_radar with Docker, deploy to Mac Mini via OrbStack, verify all CLI commands work inside the container.

## 背景

Phase A 的所有 CLI 指令在本機（MacBook Pro）驗證通過。現在要包成 Docker image 部署到 Mac Mini，為後續 B2 cron 排程做準備。

## 驗收條件

- [ ] AC-1: Dockerfile 能成功 build image（基於 python:3.12-slim，arm64 相容）
- [ ] AC-2: docker-compose.yml 定義服務，config.yaml 和 credentials 用 volume mount
- [ ] AC-3: `docker compose run radar` 能正常執行 radar pipeline（fetch → filter → dedup → 寫入 Sheet）
- [ ] AC-4: `docker compose run scout` 能正常執行 scout
- [ ] AC-5: `docker compose run promote` 能正常執行 promote
- [ ] AC-6: `docker compose run cover-letter` 能正常執行 cover_letter
- [ ] AC-7: .cache/ 用 volume 持久化（container 重啟不丟 cache）
- [ ] AC-8: 在 Mac Mini 上 clone repo + 設定 config → build → run 驗證通過

## 目錄結構（Mac Mini 上）

```
~/Developer/kc_job_radar/
├── docker-compose.yml
├── Dockerfile
├── data/
│   ├── config.yaml          # volume mount
│   ├── credentials.json     # volume mount
│   └── resume.md
├── .cache/                   # volume, 持久化
└── src/                      # image 裡
```

## 不做的事

- 不做 cron（B2 的事）
- 不做 Telegram（B3 的事）
- 不做 Gmail（B4 的事）
- 不做 OrbStack 開機自動啟動設定（手動啟動就好）

## 依賴

- Mac Mini: OrbStack 已安裝，Docker 路徑 ~/.orbstack/bin/docker
- Google Sheet credentials
- config.yaml
