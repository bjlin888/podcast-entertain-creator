# Podcast Entertainment Creator — 實作計畫

## 背景

打造一個 LINE Bot，協助 Podcast 主持人透過 AI 產製內容。Bot 引導使用者完成主題設定、標題生成、腳本撰寫、TTS 語音示範、以及迭代優化。目前專案只有空的骨架（空的 `main.py`、無任何依賴套件）。規格書（v4）定義了 10 項功能（F01-F10）、8 張資料表、9 個狀態的狀態機、以及 8 個 Sprint 的開發排程。

**核心精神**：Simple first — 輕量、好維護、好部署。

---

## 輸出檔案

`docs/implementation_plan.md` — 完整實作計畫（台灣慣用語）

---

## Sprint 1：基礎建設（Webhook、SQLite、狀態機框架）

### 要建立的檔案：
| 檔案 | 用途 |
|------|------|
| `app/__init__.py` | 套件標記 |
| `app/main.py` | FastAPI 應用、`/callback` webhook、`/health`、lifespan 初始化 DB |
| `app/config.py` | `pydantic-settings` 的 Settings 類別，載入 `.env` |
| `app/db.py` | 全部 8 張資料表的 DDL、`init_db()`、users/sessions 的 CRUD |
| `app/models.py` | `BotState` 列舉（9 個狀態）、`CollectInfoStep` 列舉 |
| `app/state_machine.py` | `@register(state, event_type)` 裝飾器、`process_event()` 分派器 |
| `app/handlers/__init__.py` | 匯入所有 handler 模組以觸發註冊 |
| `app/handlers/onboarding.py` | IDLE / SELECT_LLM handler（歡迎訊息、LLM Quick Reply） |
| `app/line_helpers.py` | `build_llm_select_quick_reply()`、`build_welcome_message()` |
| `.env.example` | 環境變數範本 |
| `Dockerfile` | Python 3.13-slim + uv |
| `tests/conftest.py` | 記憶體 DB fixture、mock LINE API fixture |
| `tests/test_db.py` | 建表、user/session CRUD 測試 |
| `tests/test_state_machine.py` | 分派、fallback、狀態持久化測試 |
| `tests/test_webhook.py` | `/callback` 簽章驗證、`/health` 測試 |

### 要修改的檔案：
- `pyproject.toml` — 新增依賴：`fastapi`、`uvicorn[standard]`、`line-bot-sdk>=3.14`、`aiosqlite`、`pydantic-settings`、`python-dotenv`；開發依賴：`pytest`、`pytest-asyncio`、`httpx`
- `.gitignore` — 加入 `data/`、`.env`
- 刪除根目錄的 `main.py`（進入點移至 `app/main.py`）

### 設計決策：
- 用 **`aiosqlite`** 取代原生 `sqlite3`，與 FastAPI 的 async 模式相容（零原生依賴，同樣輕量）
- 採用 **`WebhookParser`**（非裝飾器風格的 `WebhookHandler`），遵循 LINE SDK v3 FastAPI 官方範例的顯式 async 事件分派
- **狀態機用分派表**實作：`dict[(BotState, event_type)] -> handler_func`，每個 handler 回傳下一個狀態
- **Sprint 1 就建好全部 8 張表**，確保 schema 從一開始就穩定
- **處理 LLM 回應慢的問題**：先用 reply token 回覆「處理中...」，再用 `push_message()` 推送實際結果（reply token 30 秒過期）

### 資料庫 Schema（全部 8 張表）：
`users`、`projects`、`titles`、`scripts`、`script_segments`、`feedbacks`、`sessions`、`voice_samples` — 欄位依照規格書 5.1/5.2 節

### 驗證方式：
```bash
uv sync && uv run uvicorn app.main:app --reload  # 伺服器啟動
uv run pytest tests/                               # 全部測試通過
curl http://localhost:8000/health                   # 回傳 {"status": "ok"}
```

---

## Sprint 2：LLM 抽象層

### 要建立的檔案：
| 檔案 | 用途 |
|------|------|
| `app/llm/__init__.py` | 套件標記 |
| `app/llm/base.py` | 抽象 `LLMProvider`，含 `async complete()`、`LLMError` |
| `app/llm/claude_provider.py` | Anthropic SDK，JSON 柵欄移除解析器 |
| `app/llm/gemini_provider.py` | Google GenAI SDK，`response_mime_type="application/json"` |
| `app/llm/factory.py` | `get_provider(name)` — 延遲建立的單例模式 |
| `app/llm/prompt_builder.py` | 載入 `prompts/*.txt`，帶入變數格式化 |
| `prompts/system.txt` | 系統提示詞（繁體中文 Podcast 專家、JSON 輸出） |
| `prompts/title_generation.txt` | 5 組標題，含 `{topic}`、`{audience}`、`{style}` |
| `prompts/script_generation.txt` | 分段腳本，含 `{selected_title}`、`{duration_min}`、`{host_count}` |
| `prompts/script_refinement.txt` | 迭代優化，含 `{segment_id}`、`{feedback}`、`{scores}` |
| `tests/test_llm_providers.py` | Mock API 呼叫、JSON 解析、錯誤處理測試 |
| `tests/test_prompt_builder.py` | 範本載入與變數替換測試 |

### 要修改：`pyproject.toml` — 加入 `anthropic>=0.42`、`google-generativeai>=0.8`

### Provider 介面：
```python
class LLMProvider(ABC):
    async def complete(self, system_prompt: str, user_message: str, task: str) -> dict: ...
```
- 回傳已解析的 `dict`，不是原始文字
- Claude：在 prompt 中要求 JSON 輸出，解析時移除 markdown 柵欄
- Gemini：原生 `response_mime_type="application/json"` 結構化輸出

---

## Sprint 3：主題收集 + 標題生成（F01 + F02 + F08）

### 流程：SELECT_LLM -> COLLECT_INFO -> TITLE_REVIEW

- 擴充 `app/handlers/onboarding.py` — COLLECT_INFO 子步驟透過 `session.context["collect_step"]` 管理：主題 -> 聽眾 -> 時長（Quick Reply）-> 風格（Quick Reply）-> 主持人人數
- 建立 `app/handlers/title.py` — TITLE_REVIEW：選擇標題（postback）、重新生成（文字指令）
- 擴充 `app/line_helpers.py` — `build_title_flex_messages()`（5 張泡泡卡片）、`build_info_quick_reply()`
- 擴充 `app/db.py` — projects 與 titles 的 CRUD

---

## Sprint 4：腳本生成（F03）

### 流程：TITLE_REVIEW -> SCRIPT_REVIEW

- 建立 `app/handlers/script.py` — 透過 LLM 生成腳本，逐段以 Flex Message 卡片發送，每段附「修改這段」與「🔊 生成示範音檔」按鈕
- 擴充 `app/line_helpers.py` — `build_segment_flex()`、`build_script_summary_flex()`
- 擴充 `app/db.py` — scripts 與 script_segments 的 CRUD

---

## Sprint 5：TTS 聲音示範（F09）

### 流程：SCRIPT_REVIEW -> TTS_CONFIG -> TTS_GENERATING -> SCRIPT_REVIEW

- 建立 `app/tts/ssml_builder.py` — 依規格書表 4.3 將 cue 轉換為 SSML
- 建立 `app/tts/tts_service.py` — Google Cloud TTS 封裝（`TextToSpeechAsyncClient`、zh-TW Wavenet）
- 建立 `app/tts/audio_storage.py` — 本地（`data/audio/`）/ GCS 儲存抽象層
- 建立 `app/handlers/tts.py` — TTS_CONFIG（聲音/語速/語調 Quick Reply）、TTS_GENERATING（合成 + 發送 AudioMessage）
- 修改 `app/main.py` — 掛載 `/audio` 靜態檔案路由（本地儲存模式）
- 修改 `pyproject.toml` — 加入 `google-cloud-texttospeech>=2.22`

---

## Sprint 6：主持人錄音上傳（F10）

- 擴充 `app/handlers/tts.py` — 處理音訊訊息事件：透過 LINE Blob API 下載、儲存、更新 `voice_samples.host_audio_url`
- 擴充 `app/line_helpers.py` — `build_voice_comparison_flex()`（TTS 與主持人錄音並排對照）

---

## Sprint 7：回饋與迭代（F05 + F06）

### 流程：SCRIPT_REVIEW -> FEEDBACK_LOOP -> SCRIPT_REVIEW

- 建立 `app/handlers/feedback.py` — 評分 Flex（3 個面向 x 1-5 分）、文字回饋收集、LLM 迭代優化呼叫、產生新版腳本
- 擴充 `app/line_helpers.py` — `build_scoring_flex()`
- 擴充 `app/db.py` — 回饋 CRUD、腳本版本管理

---

## Sprint 8：範本庫 + 歷史查詢 + 匯出（F04 + F07）

- 建立 `app/handlers/export.py` — 彙整全部段落為純文字、音檔清單附 TTS 下載連結
- 擴充 `app/handlers/onboarding.py` — IDLE 狀態下支援「歷史」/「範本」指令
- 擴充 `app/db.py` — 歷史查詢、templates 資料表（第 9 張表）、範本 CRUD

---

## 目錄結構

```
podcast-entertain-creator/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 應用、webhook、lifespan
│   ├── config.py                # pydantic-settings 設定
│   ├── db.py                    # SQLite schema + CRUD
│   ├── models.py                # Pydantic 資料模型
│   ├── state_machine.py         # 狀態列舉、分派表、process_event()
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── onboarding.py        # IDLE -> SELECT_LLM -> COLLECT_INFO
│   │   ├── title.py             # TITLE_REVIEW
│   │   ├── script.py            # SCRIPT_REVIEW
│   │   ├── tts.py               # TTS_CONFIG、TTS_GENERATING
│   │   ├── feedback.py          # FEEDBACK_LOOP
│   │   └── export.py            # EXPORT
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py              # 抽象 LLMProvider
│   │   ├── claude_provider.py   # Anthropic 實作
│   │   ├── gemini_provider.py   # Google Gemini 實作
│   │   ├── factory.py           # get_provider()
│   │   └── prompt_builder.py    # 提示詞範本載入與格式化
│   ├── tts/
│   │   ├── __init__.py
│   │   ├── tts_service.py       # Google TTS 封裝
│   │   ├── ssml_builder.py      # cue -> SSML 前處理
│   │   └── audio_storage.py     # 音檔上傳（local / GCS）
│   └── line_helpers.py          # Flex Message、Quick Reply 建構工具
├── prompts/
│   ├── system.txt
│   ├── title_generation.txt
│   ├── script_generation.txt
│   └── script_refinement.txt
├── data/                        # 執行期資料（gitignore）
│   └── audio/
├── tests/
│   ├── conftest.py
│   ├── test_db.py
│   ├── test_state_machine.py
│   ├── test_llm_providers.py
│   ├── test_prompt_builder.py
│   ├── test_ssml_builder.py
│   └── test_webhook.py
├── docs/
│   ├── podcast_spec_v4.docx
│   └── implementation_plan.md   # 本文件
├── .env.example
├── .gitignore
├── pyproject.toml
├── Dockerfile
└── README.md
```

---

## 端對端驗證

每個 Sprint 完成後：
1. `uv sync && uv run pytest tests/` — 全部測試通過
2. `uv run uvicorn app.main:app --reload` — 伺服器正常啟動
3. 透過 ngrok 部署進行 LINE Bot 手動測試
4. Sprint 8 完成後跑完整流程：IDLE -> SELECT_LLM -> COLLECT_INFO -> TITLE_REVIEW -> SCRIPT_REVIEW -> TTS -> FEEDBACK -> EXPORT -> IDLE
