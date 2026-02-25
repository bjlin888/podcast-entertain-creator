# GCP Cloud Run 部署指南

本文件說明如何將 Podcast 創作助手部署到 Google Cloud Run。

---

## 目錄

- [架構總覽](#架構總覽)
- [前置需求](#前置需求)
- [快速部署（3 步驟）](#快速部署3-步驟)
- [詳細步驟](#詳細步驟)
  - [Step 1：建立 GCP 專案](#step-1建立-gcp-專案)
  - [Step 2：準備環境變數](#step-2準備環境變數)
  - [Step 3：執行一次性設定](#step-3執行一次性設定)
  - [Step 4：手動部署](#step-4手動部署)
  - [Step 5：設定 CI/CD 自動部署](#step-5設定-cicd-自動部署)
- [架構詳解](#架構詳解)
  - [Docker 多階段建置](#docker-多階段建置)
  - [資料持久化（Cloud Storage FUSE）](#資料持久化cloud-storage-fuse)
  - [Secret Manager 整合](#secret-manager-整合)
  - [IAM 權限說明](#iam-權限說明)
- [環境變數參考](#環境變數參考)
- [維運操作](#維運操作)
- [費用估算](#費用估算)
- [疑難排解](#疑難排解)

---

## 架構總覽

```
GitHub repo (push to main)
    │
    ▼
Cloud Build ──build──▶ Artifact Registry (Docker image)
    │                         │
    │                         ▼
    └──deploy──▶ Cloud Run ◄── Secret Manager (API keys)
                    │              │
                    │              ▼
                    │         Cloud Storage (FUSE mount → /app/data)
                    │              ├── podcast.db (SQLite)
                    │              └── audio/ (TTS 音檔)
                    │
                    ├── /          → Vue 3 SPA (frontend)
                    ├── /api/v1/   → FastAPI REST API
                    └── /health    → Health check
```

**使用的 GCP 服務：**

| 服務 | 用途 |
|------|------|
| Cloud Run | 執行 Docker container（serverless, gen2） |
| Cloud Build | 建置 Docker image（CI/CD） |
| Artifact Registry | 儲存 Docker image |
| Secret Manager | 安全儲存 API keys |
| Cloud Storage | 資料持久化（FUSE mount） |

---

## 前置需求

### 工具安裝

```bash
# Google Cloud SDK
brew install google-cloud-sdk    # macOS
# 或參考 https://cloud.google.com/sdk/docs/install

# GitHub CLI（選用，用於自動建立 repo）
brew install gh

# 驗證登入
gcloud auth login
gcloud auth application-default login
```

### API Keys

| Key | 取得方式 | 必要性 |
|-----|----------|--------|
| Gemini API Key | [Google AI Studio](https://aistudio.google.com/apikey) | 必要（LLM + TTS） |
| Anthropic API Key | [Anthropic Console](https://console.anthropic.com/) | 選用（Claude LLM） |
| Encryption Key | 自動產生（見下方） | 必要（加密使用者 API keys） |

---

## 快速部署（3 步驟）

如果你已經有 GCP 專案和 API keys：

```bash
# 1. 設定環境變數
export GCP_PROJECT_ID=your-project-id
export GEMINI_API_KEY=AIza...
export GITHUB_OWNER=your-github-username

# 2. 一次性基礎建設
bash scripts/gcp-setup.sh

# 3. 部署
bash scripts/gcp-deploy.sh
```

部署完成後會印出 Cloud Run URL，例如：
```
=== Deploy complete ===
  URL: https://podcast-creator-xxxxx.asia-east1.run.app
  Health: https://podcast-creator-xxxxx.asia-east1.run.app/health
```

---

## 詳細步驟

### Step 1：建立 GCP 專案

1. 前往 [GCP Console](https://console.cloud.google.com/) 建立新專案
2. 記下 Project ID（例如 `my-podcast-app`）
3. 確認已啟用 billing（Cloud Run 有免費額度，但需要 billing account）

### Step 2：準備環境變數

建立 `.env.gcp` 檔案（已被 `.gitignore` 排除）：

```bash
# .env.gcp
export GCP_PROJECT_ID=my-podcast-app
export GEMINI_API_KEY=AIzaSy...
# export ANTHROPIC_API_KEY=sk-ant-...  # 選用
export GITHUB_OWNER=your-github-username
export GITHUB_REPO=podcast-entertain-creator
export GCP_REGION=asia-east1
export GCP_REPO=podcast-creator
export GCP_SERVICE=podcast-creator
```

載入環境變數：

```bash
source .env.gcp
```

### Step 3：執行一次性設定

```bash
bash scripts/gcp-setup.sh
```

此腳本會依序執行：

| 步驟 | 動作 | 說明 |
|------|------|------|
| 1 | 啟用 GCP APIs | Cloud Run, Cloud Build, Artifact Registry, Secret Manager |
| 2 | 建立 Artifact Registry | Docker image 儲存庫 |
| 3 | 建立 Secret Manager secrets | `gemini-api-key`, `anthropic-api-key`（選用） |
| 4 | 設定 IAM 權限 | Compute default SA 取得必要角色 |
| 5 | 建立 Cloud Storage bucket | 資料持久化（SQLite + 音檔） |
| 6 | 檢查/建立 GitHub repo | 確保程式碼已推送 |
| 7 | 建立 Cloud Build trigger | push to main 自動部署（需先在 Console 連接 GitHub） |

> **ENCRYPTION_KEY** 需要手動建立（一次性）：
> ```bash
> # 產生 Fernet 加密金鑰
> ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
>
> # 存入 Secret Manager
> echo -n "$ENCRYPTION_KEY" | gcloud secrets create encryption-key --data-file=-
> ```

### Step 4：手動部署

```bash
bash scripts/gcp-deploy.sh
```

此腳本會：

1. **Cloud Build 建置** — 上傳原始碼到 GCS，在 GCP 上建置 Docker image
2. **推送到 Artifact Registry** — 儲存建置好的 image
3. **部署到 Cloud Run** — 建立/更新 service，掛載 secrets + Cloud Storage FUSE volume
4. **自動偵測 CORS** — 從現有 service URL 取得，設為允許的 origin

整個過程約 1-2 分鐘。

### Step 5：設定 CI/CD 自動部署

Cloud Build 2nd-gen trigger 需要在 Console 手動連接 GitHub App：

1. 前往 [Cloud Build > Repositories](https://console.cloud.google.com/cloud-build/repositories/2nd-gen)
2. 點擊「Link a repository」
3. 安裝 Google Cloud Build GitHub App
4. 選擇你的 repository
5. 重新執行 `bash scripts/gcp-setup.sh`（會自動偵測已連結的 repo 並建立 trigger）

連結完成後，每次 push 到 `main` 分支會自動觸發部署。

`cloudbuild.yaml` 定義了自動部署的步驟：
```
docker build → docker push → gcloud run deploy
```

---

## 架構詳解

### Docker 多階段建置

```dockerfile
# Stage 1: 建置 Vue 3 前端
FROM node:22-slim AS frontend
# npm ci → vite build → 產出 dist/

# Stage 2: Python 後端
FROM python:3.13-slim
# uv sync → 安裝 Python 依賴
# COPY frontend/dist → 嵌入前端靜態檔
# uvicorn 啟動 FastAPI
```

最終 image 約 200MB，包含前端 + 後端。

### 資料持久化（Cloud Storage FUSE）

Cloud Run container 是 ephemeral（短暫的），重新部署後本地檔案會重置。為了保留 SQLite 資料庫和 TTS 音檔，使用 Cloud Storage FUSE 將 GCS bucket 掛載到 `/app/data`。

```
Cloud Run container
  └── /app/data  ←── Cloud Storage FUSE mount
        ├── podcast.db     (SQLite 資料庫)
        └── audio/         (TTS 音檔)
```

**關鍵配置：**

| 設定 | 值 | 原因 |
|------|-----|------|
| `max-instances` | `1` | SQLite 不支援多 writer，限制單一 instance |
| `execution-environment` | `gen2` | FUSE mount 需要第二代執行環境 |
| `journal_mode` | `DELETE` | FUSE 不支援 shared memory（WAL 模式需要） |
| `busy_timeout` | `5000` ms | 處理短暫的 lock contention |
| `synchronous` | `NORMAL` | 平衡寫入效能與資料安全 |

> 詳細說明見 [docs/data-persistence.md](data-persistence.md)

### Secret Manager 整合

Cloud Run 透過 `--set-secrets` 將 Secret Manager secrets 掛載為環境變數：

| Secret 名稱 | 環境變數 | 用途 |
|-------------|---------|------|
| `gemini-api-key` | `GEMINI_API_KEY` | 伺服器預設 Gemini API key |
| `encryption-key` | `ENCRYPTION_KEY` | Fernet 加密金鑰（加密使用者 API keys） |
| `anthropic-api-key` | `ANTHROPIC_API_KEY` | 伺服器預設 Anthropic API key（選用） |

使用者也可以在前端 AI 設定頁面輸入自己的 API key（BYOK），會加密後儲存在 SQLite 資料庫中。

### IAM 權限說明

Compute default SA（Cloud Build 和 Cloud Run 共用）需要的角色：

| 角色 | 用途 |
|------|------|
| `roles/run.admin` | 部署 Cloud Run services |
| `roles/secretmanager.secretAccessor` | 讀取 Secret Manager secrets |
| `roles/iam.serviceAccountUser` | 允許 Cloud Run 使用 SA |
| `roles/storage.objectAdmin` | Cloud Build 上傳原始碼到 GCS |
| `roles/artifactregistry.writer` | 推送 Docker image 到 AR |
| `roles/logging.logWriter` | Cloud Build 寫入建置日誌 |

---

## 環境變數參考

### gcp-setup.sh

| 變數 | 必填 | 預設值 | 說明 |
|------|------|--------|------|
| `GCP_PROJECT_ID` | Yes | — | GCP 專案 ID |
| `GEMINI_API_KEY` | Yes | — | Gemini API key（存入 Secret Manager） |
| `GITHUB_OWNER` | Yes | — | GitHub 帳號/組織 |
| `ANTHROPIC_API_KEY` | No | — | Anthropic API key（存入 Secret Manager） |
| `GCP_REGION` | No | `asia-east1` | GCP 區域 |
| `GCP_REPO` | No | `podcast-creator` | Artifact Registry repo 名稱 |
| `GCP_SERVICE` | No | `podcast-creator` | Cloud Run service 名稱 |
| `GITHUB_REPO` | No | `podcast-entertain-creator` | GitHub repo 名稱 |
| `GCS_BUCKET` | No | `${GCP_PROJECT_ID}-podcast-data` | Cloud Storage bucket 名稱 |

### gcp-deploy.sh

| 變數 | 必填 | 預設值 | 說明 |
|------|------|--------|------|
| `GCP_PROJECT_ID` | Yes | — | GCP 專案 ID |
| `GCP_REGION` | No | `asia-east1` | GCP 區域 |
| `GCP_REPO` | No | `podcast-creator` | Artifact Registry repo 名稱 |
| `GCP_SERVICE` | No | `podcast-creator` | Cloud Run service 名稱 |
| `CORS_ORIGINS` | No | 自動偵測 | 允許的 CORS origins（逗號分隔） |
| `IMAGE_TAG` | No | git short SHA | Docker image tag |
| `GCS_BUCKET` | No | `${GCP_PROJECT_ID}-podcast-data` | Cloud Storage bucket 名稱 |

### 應用程式環境變數（Cloud Run runtime）

| 變數 | 來源 | 說明 |
|------|------|------|
| `GEMINI_API_KEY` | Secret Manager | Gemini API key |
| `ANTHROPIC_API_KEY` | Secret Manager | Anthropic API key |
| `ENCRYPTION_KEY` | Secret Manager | Fernet 加密金鑰 |
| `CORS_ORIGINS` | 環境變數 | 允許的 CORS origins |
| `PORT` | Cloud Run 自動設定 | HTTP 監聽 port（預設 8080） |

---

## 維運操作

### 查看日誌

```bash
# 即時日誌
gcloud run services logs read podcast-creator --region=asia-east1 --limit=50

# 或在 Console
# https://console.cloud.google.com/run/detail/asia-east1/podcast-creator/logs
```

### 查看目前版本

```bash
gcloud run revisions list --service=podcast-creator --region=asia-east1
```

### 回滾到前一版本

```bash
# 列出所有 revision
gcloud run revisions list --service=podcast-creator --region=asia-east1

# 將流量導向指定 revision
gcloud run services update-traffic podcast-creator \
  --to-revisions=podcast-creator-00003-fst=100 \
  --region=asia-east1
```

### 更新 Secret

```bash
# 更新 Gemini API key
echo -n "NEW_KEY_VALUE" | gcloud secrets versions add gemini-api-key --data-file=-

# 重新部署（讓 Cloud Run 載入新的 secret version）
bash scripts/gcp-deploy.sh
```

### 刪除服務

```bash
gcloud run services delete podcast-creator --region=asia-east1
gcloud artifacts repositories delete podcast-creator --location=asia-east1
```

---

## 費用估算

此專案設計在 GCP 免費額度內運行：

| 服務 | 免費額度 | 本專案預估用量 |
|------|----------|---------------|
| Cloud Run | 2M requests/月, 360K GB·s | 低（個人使用） |
| Cloud Build | 120 build-min/天 | 每次建置約 1 分鐘 |
| Artifact Registry | 500MB | 單一 image 約 200MB |
| Secret Manager | 6 active secrets, 10K access | 3 secrets |
| Cloud Storage | 5GB（限 US region） | 資料持久化 + 建置暫存 |

**注意事項：**
- Cloud Run `min-instances=0` 表示無流量時不計費（冷啟動約 3-5 秒）
- `max-instances=1` 限制單一 instance（SQLite 單 writer 限制）
- Cloud Storage 免費額度僅限 US region，asia-east1 的 bucket 會有少量費用（個人使用量極低）

---

## 疑難排解

### 問題：Cloud Build 權限不足

```
Permission 'artifactregistry.repositories.uploadArtifacts' denied
```

**解決方案：** 確認 Compute default SA 有 `artifactregistry.writer` 角色：

```bash
PROJECT_NUMBER=$(gcloud projects describe $GCP_PROJECT_ID --format='value(projectNumber)')
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer" \
  --condition=None --quiet
```

### 問題：Cloud Run 無法存取 Secret

```
Permission denied on secret: projects/.../secrets/gemini-api-key
```

**解決方案：** 確認 Compute default SA 有 `secretmanager.secretAccessor`：

```bash
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None --quiet
```

### 問題：CORS 錯誤

前端無法呼叫 API，瀏覽器顯示 CORS error。

**解決方案：** 確認 `CORS_ORIGINS` 環境變數包含前端 URL：

```bash
export CORS_ORIGINS=https://podcast-creator-xxxxx.asia-east1.run.app
bash scripts/gcp-deploy.sh
```

### 問題：Gemini API Key IP 限制

如果你的 Gemini API key 設定了 IP 限制，Cloud Run 的動態 IP 會被拒絕。

**解決方案（推薦）：** 使用 BYOK 功能讓使用者自帶 API key：
1. 在 Google Cloud Console > APIs & Services > Credentials 移除伺服器 key 的 IP 限制
2. 改為 API 限制（只允許 Generative Language API）
3. 使用者在前端 AI 設定頁面輸入自己的 key

### 問題：/health 返回 404

**原因：** 靜態檔案 catch-all mount 攔截了 `/health` 路由。

**解決方案：** 確認 `app/main.py` 中 `@app.get("/health")` 在 `app.mount("/", StaticFiles(...))` 之前。

### 問題：資料遺失（重新部署後）

**已解決：** 專案已整合 Cloud Storage FUSE，`/app/data` 目錄（包含 SQLite 和音檔）會自動掛載到 GCS bucket。

如果仍遇到資料遺失，確認：
1. GCS bucket 存在：`gcloud storage buckets describe gs://${GCP_PROJECT_ID}-podcast-data`
2. 部署指令包含 `--add-volume` 和 `--add-volume-mount`（`gcp-deploy.sh` 已自動處理）
3. `max-instances=1`（SQLite 不支援多 writer）

### 問題：Cloud Storage FUSE mount 失敗

```
Volume mount failed: failed to mount volume "data-vol"
```

**解決方案：** 確認 Compute default SA 有 `storage.objectAdmin` 角色，且 bucket 存在：

```bash
# 確認 bucket 存在
gcloud storage buckets describe gs://${GCP_PROJECT_ID}-podcast-data

# 如果不存在，建立
gcloud storage buckets create gs://${GCP_PROJECT_ID}-podcast-data --location=asia-east1
```
