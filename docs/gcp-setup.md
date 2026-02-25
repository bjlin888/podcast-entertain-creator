# GCP Cloud Run 部署設定

## 快速開始

### 一次性設定

```bash
export GCP_PROJECT_ID=my-gcp-project
export GEMINI_API_KEY=AIza...
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_OWNER=my-github-user

bash scripts/gcp-setup.sh
```

### 手動部署

```bash
export GCP_PROJECT_ID=my-gcp-project

bash scripts/gcp-deploy.sh
```

後續推送到 `main` 分支會自動觸發 Cloud Build 部署。

---

## 環境變數參考

### gcp-setup.sh

| 變數 | 必填 | 預設值 | 說明 |
|------|------|--------|------|
| `GCP_PROJECT_ID` | Yes | — | GCP 專案 ID |
| `GEMINI_API_KEY` | Yes | — | Gemini API key (存入 Secret Manager) |
| `ANTHROPIC_API_KEY` | Yes | — | Anthropic API key (存入 Secret Manager) |
| `GITHUB_OWNER` | Yes | — | GitHub 帳號/組織 |
| `GCP_REGION` | No | `asia-east1` | GCP 區域 |
| `GCP_REPO` | No | `podcast-creator` | Artifact Registry repo 名稱 |
| `GCP_SERVICE` | No | `podcast-creator` | Cloud Run service 名稱 |
| `GITHUB_REPO` | No | `podcast-entertain-creator` | GitHub repo 名稱 |

### gcp-deploy.sh

| 變數 | 必填 | 預設值 | 說明 |
|------|------|--------|------|
| `GCP_PROJECT_ID` | Yes | — | GCP 專案 ID |
| `GCP_REGION` | No | `asia-east1` | GCP 區域 |
| `GCP_REPO` | No | `podcast-creator` | Artifact Registry repo 名稱 |
| `GCP_SERVICE` | No | `podcast-creator` | Cloud Run service 名稱 |
| `CORS_ORIGINS` | No | 自動偵測 | 允許的 CORS origins (逗號分隔) |
| `IMAGE_TAG` | No | git short SHA | Docker image tag |

---

## Setup 腳本做了什麼

`gcp-setup.sh` 執行以下步驟：

1. **啟用 API** — Cloud Run, Cloud Build, Artifact Registry, Secret Manager
2. **建立 Artifact Registry repo** — Docker image 儲存
3. **建立 Secret Manager secrets** — `gemini-api-key`, `anthropic-api-key`
4. **設定 IAM** — Cloud Build SA 取得 Cloud Run Admin, Secret Accessor, SA User 角色
5. **建立 Cloud Build trigger** — push to `main` 自動部署

## Deploy 腳本做了什麼

`gcp-deploy.sh` 執行以下步驟：

1. **Cloud Build 建置** — 在 GCP 上 build Docker image (使用免費額度)
2. **部署 Cloud Run** — 含 Secret Manager 注入、CORS 設定
3. **自動偵測 CORS** — 若未設定，從現有 service URL 取得

---

## GCP 免費額度參考

| 服務 | 免費額度 | 用途 |
|------|----------|------|
| Cloud Run | 2M requests/月, 360K GB·s | 跑應用 (asia-east1) |
| Cloud Storage | 5GB (限 US region) | 音檔/DB 備份 |
| Artifact Registry | 500MB | Docker image |
| Cloud Build | 120 build-min/天 | CI/CD |
| Secret Manager | 6 active secrets, 10K access | API keys |

## 資料持久化

Cloud Run 是 ephemeral container，目前使用方案 A（接受 ephemeral）。
若需升級至 Cloud Storage FUSE mount：

```bash
gcloud run deploy podcast-creator \
  --add-volume=name=data-vol,type=cloud-storage,bucket=MY_BUCKET \
  --add-volume-mount=volume=data-vol,mount-path=/app/data
```

> **注意**：Cloud Storage 免費額度僅限 US region bucket，跨區至 asia-east1 有些許延遲但功能正常。
