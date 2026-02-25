# 資料持久化報告 — Cloud Storage FUSE

本文件說明 Podcast 創作助手如何透過 Cloud Storage FUSE 實現 Cloud Run 上的資料持久化。

---

## 目錄

- [問題背景](#問題背景)
- [解決方案](#解決方案)
- [技術實作](#技術實作)
  - [GCS Bucket 建立](#gcs-bucket-建立)
  - [Cloud Run Volume Mount](#cloud-run-volume-mount)
  - [SQLite FUSE 相容設定](#sqlite-fuse-相容設定)
  - [部署腳本變更](#部署腳本變更)
- [限制與取捨](#限制與取捨)
- [變更清單](#變更清單)
- [驗證方式](#驗證方式)
- [未來升級路徑](#未來升級路徑)

---

## 問題背景

Cloud Run container 是 **ephemeral**（短暫的）：

- 每次部署新 revision 時，container 重建，本地檔案全部重置
- 即使不重新部署，Cloud Run 也可能因為 scale-to-zero 後冷啟動而重建 container
- 這表示寫在 container 檔案系統的 SQLite 資料庫和 TTS 音檔都會遺失

**受影響的資料：**

| 檔案 | 路徑 | 內容 |
|------|------|------|
| SQLite 資料庫 | `data/podcast.db` | 使用者、專案、腳本、BYOK API keys |
| TTS 音檔 | `data/audio/*.mp3` | 語音合成輸出 |

**BYOK（Bring Your Own Key）功能尤其受影響：** 使用者在前端設定的加密 API keys 儲存在 SQLite 中，每次部署後遺失意味著使用者必須重新輸入。

---

## 解決方案

使用 **Cloud Storage FUSE** 將 GCS bucket 掛載為 Cloud Run 的本地目錄。

```
Cloud Run container (gen2)
  └── /app/data  ←── Cloud Storage FUSE ←── gs://{PROJECT_ID}-podcast-data
        ├── podcast.db     (SQLite 資料庫)
        └── audio/         (TTS 音檔)
```

Cloud Storage FUSE 提供 POSIX-like 的檔案系統介面，讓應用程式可以用標準的檔案讀寫操作存取 GCS 物件，無需修改應用程式碼。

**為什麼選 FUSE 而非其他方案：**

| 方案 | 優點 | 缺點 | 適合度 |
|------|------|------|--------|
| Cloud Storage FUSE | 零程式碼修改、GCP 原生 | 效能較低、需 gen2 | 最適合（個人使用、低流量） |
| Cloud SQL (PostgreSQL) | 正式資料庫、多 writer | 費用高（最低 ~$7/月）、需大改 | 過度 |
| Firestore | Serverless、自動擴展 | 需重寫所有 DB 操作 | 大改動 |
| GCS API 直接呼叫 | 精確控制 | 需改所有 I/O 程式碼 | 大改動 |

---

## 技術實作

### GCS Bucket 建立

`scripts/gcp-setup.sh` 新增 step 5：

```bash
DATA_BUCKET="${GCS_BUCKET:-${GCP_PROJECT_ID}-podcast-data}"
gcloud storage buckets create "gs://${DATA_BUCKET}" \
  --location="${REGION}" \
  --uniform-bucket-level-access
```

- Bucket 命名慣例：`{PROJECT_ID}-podcast-data`
- 可透過 `GCS_BUCKET` 環境變數覆蓋
- `uniform-bucket-level-access` 簡化 IAM 權限管理

### Cloud Run Volume Mount

`scripts/gcp-deploy.sh` 的 `gcloud run deploy` 新增：

```bash
--execution-environment=gen2 \
--max-instances=1 \
--add-volume=name=data-vol,type=cloud-storage,bucket="${DATA_BUCKET}" \
--add-volume-mount=volume=data-vol,mount-path=/app/data
```

| 參數 | 說明 |
|------|------|
| `--execution-environment=gen2` | FUSE mount 需要第二代執行環境 |
| `--max-instances=1` | SQLite 單 writer 限制 |
| `--add-volume` | 定義 Cloud Storage volume |
| `--add-volume-mount` | 掛載到 `/app/data`（覆蓋 container 的 `data/` 目錄） |

### SQLite FUSE 相容設定

`app/db.py` 的 `get_db()` 新增 PRAGMA：

```python
await db.execute("PRAGMA journal_mode=DELETE")
await db.execute("PRAGMA busy_timeout=5000")
await db.execute("PRAGMA synchronous=NORMAL")
```

| PRAGMA | 值 | 原因 |
|--------|-----|------|
| `journal_mode` | `DELETE` | FUSE 不支援 `mmap`/shared memory，WAL 模式會失敗 |
| `busy_timeout` | `5000` ms | FUSE I/O 延遲較高，給予充足的等待時間 |
| `synchronous` | `NORMAL` | `FULL` 在 FUSE 上每次 fsync 都觸發 GCS upload，太慢 |

> `foreign_keys=ON` 保持不變。

### 部署腳本變更

**`cloudbuild.yaml`（CI/CD 自動部署）：**
- Deploy step 改用 `bash` entrypoint，支援動態 bucket 名稱
- 新增 `_DATA_BUCKET` substitution（預設為空，自動 fallback 到 `$PROJECT_ID-podcast-data`）
- `max-instances` 從 `2` 改為 `1`
- 新增 `--execution-environment=gen2`
- 新增 `--add-volume` 和 `--add-volume-mount`

**`scripts/gcp-deploy.sh`（手動部署）：**
- 新增 `DATA_BUCKET` 變數（預設 `${GCP_PROJECT_ID}-podcast-data`）
- 新增 `GCS_BUCKET` env var 文件
- 同上 volume mount 和 instance 限制變更

---

## 限制與取捨

### max-instances=1

SQLite 使用檔案級別的 locking，不支援多個 process 同時寫入同一個資料庫。Cloud Storage FUSE 的 advisory locking 更進一步限制了並行存取。因此 `max-instances` 必須設為 `1`。

**影響：**
- 所有請求由單一 container instance 處理
- 高並行場景可能有延遲（請求排隊）
- 對個人使用/低流量場景完全足夠

### FUSE 效能

Cloud Storage FUSE 的每次讀寫都經過 FUSE → GCS 路徑：

| 操作 | 預估延遲 |
|------|----------|
| SQLite 小查詢 | ~10-50ms（vs 本地 <1ms） |
| 寫入一筆記錄 | ~50-200ms |
| 讀取音檔 | 首次 ~100-500ms，後續有 kernel cache |

對於此應用場景（個人 podcast 創作工具），這些延遲完全可接受。

### 資料一致性

- `max-instances=1` 確保單一 writer，沒有並行寫入衝突
- `journal_mode=DELETE` 確保 crash recovery 不依賴 shared memory
- `synchronous=NORMAL` 在 OS crash 時可能遺失最近一次 transaction（可接受）

### 冷啟動

- `min-instances=0` + FUSE mount 會增加冷啟動時間約 2-3 秒（FUSE 初始化）
- 總冷啟動時間約 5-8 秒
- 可考慮 `min-instances=1` 來消除冷啟動（但會增加費用）

---

## 變更清單

| 檔案 | 變更 |
|------|------|
| `app/db.py` | 新增 PRAGMA：`journal_mode=DELETE`, `busy_timeout=5000`, `synchronous=NORMAL` |
| `scripts/gcp-setup.sh` | 新增 step 5：建立 GCS bucket；新增 `GCS_BUCKET` env var |
| `scripts/gcp-deploy.sh` | 新增 volume mount；`max-instances=2` → `1`；新增 `gen2`；新增 `GCS_BUCKET` env var |
| `cloudbuild.yaml` | Deploy step 改用 bash；新增 volume mount、gen2、`_DATA_BUCKET` substitution；`max-instances` → `1` |
| `docs/gcp-deployment.md` | 更新架構圖、setup 步驟、env var 表、費用估算、疑難排解 |

---

## 驗證方式

### 部署前

```bash
# 1. 確認 bucket 存在
gcloud storage buckets describe gs://${GCP_PROJECT_ID}-podcast-data

# 2. 確認 SA 有 storage 權限
gcloud projects get-iam-policy ${GCP_PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:compute@developer.gserviceaccount.com AND bindings.role:roles/storage.objectAdmin" \
  --format="value(bindings.role)"
```

### 部署後

```bash
# 1. 確認 volume mount
gcloud run services describe podcast-creator --region=asia-east1 \
  --format="yaml(spec.template.spec.volumes, spec.template.spec.containers[0].volumeMounts)"

# 2. 確認 max-instances
gcloud run services describe podcast-creator --region=asia-east1 \
  --format="value(spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale')"
# 預期輸出: 1

# 3. 確認 gen2
gcloud run services describe podcast-creator --region=asia-east1 \
  --format="value(spec.template.metadata.annotations.'run.googleapis.com/execution-environment')"
# 預期輸出: gen2

# 4. 功能測試：建立專案、設定 BYOK key、重新部署後確認資料仍在
```

### 資料確認

```bash
# 查看 bucket 內容
gcloud storage ls gs://${GCP_PROJECT_ID}-podcast-data/
# 預期看到: podcast.db, audio/ 目錄
```

---

## 未來升級路徑

如果應用成長超出 SQLite + FUSE 的能力，可考慮以下升級路徑：

| 階段 | 觸發條件 | 方案 |
|------|----------|------|
| 現在 | 個人使用、低流量 | Cloud Storage FUSE + SQLite（當前） |
| 中期 | 多使用者、需要多 instance | Cloud SQL for PostgreSQL + GCS API（音檔） |
| 長期 | 高流量、全球分布 | Firestore/Spanner + Cloud CDN |

遷移 SQLite → PostgreSQL 的主要工作：
1. 替換 `aiosqlite` → `asyncpg`
2. 將 SQLite DDL 轉為 PostgreSQL syntax
3. 音檔改用 GCS API 直接上傳/下載（移除 FUSE 依賴）
4. 解除 `max-instances=1` 限制
