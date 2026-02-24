# Podcast 創作助手 — Web UI Redesign Plan

> **Version** v1.1 · **Date** 2026-02-24

---

## Context

The podcast-entertain-creator is currently a **pure LINE Bot application** — all user interaction happens through LINE Flex Messages and Quick Replies. There is **no web frontend**.

The goal is to **completely replace the LINE Bot interface** with a full Web UI based on the "Warm Creative Studio" design system (`docs/designtoken/podcast-creator-design-system.md`), using the reference HTML (`docs/designtoken/index_v1.html`) as the visual/behavioral blueprint.

**What stays**: LLM providers (`app/llm/`), TTS service (`app/tts/`), prompt templates (`prompts/`), database layer (`app/db.py`)
**What goes**: All LINE Bot code, webhook handler, state machine, LINE SDK dependency

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend** | Vue 3 (Composition API) + Vite | ES6 modules, SFC components |
| **Backend** | FastAPI + Python 3.13 | REST API, serves built frontend in production |
| **Database** | SQLite (aiosqlite) | Existing, add columns |
| **LLM** | Anthropic Claude / Google Gemini | Existing, keep as-is |
| **TTS** | Google Cloud Text-to-Speech | Existing, keep as-is |
| **Build** | Vite → `frontend/dist/` | FastAPI serves static in production |
| **Dev** | Vite dev server (port 5173) + FastAPI (port 8900) | Vite proxies `/api` to FastAPI |

---

## Architecture

### Current → Target

| Aspect | Current (LINE Bot) | Target (Web UI) |
|--------|-------------------|-----------------|
| Frontend | LINE Flex Messages | Vue 3 SPA (Vite) |
| Communication | LINE webhook → `/callback` | REST API → `/api/v1/*` |
| Session | LINE `user_id` | UUID in localStorage + `X-User-Id` header |
| Navigation | Bot state machine (9 states) | Vue Router (3 pages) + screen state |
| State | Server-side `BotState` enum | Pinia stores + server persistence |

### Target Project Structure

```
podcast-entertain-creator/
├── app/                           # Python backend
│   ├── main.py                    # REWRITE: FastAPI + API routers + static serving
│   ├── config.py                  # MODIFY: remove LINE config
│   ├── db.py                      # MODIFY: add columns, new queries
│   ├── models.py                  # REWRITE: Pydantic request/response schemas
│   ├── api/                       # NEW: REST API endpoints
│   │   ├── __init__.py
│   │   ├── deps.py                # Shared dependencies (db, user_id extraction)
│   │   ├── projects.py            # CRUD for projects (episodes)
│   │   ├── titles.py              # Title generation & selection
│   │   ├── scripts.py             # Script generation, segment editing
│   │   ├── tts.py                 # TTS generation, audio upload
│   │   ├── feedback.py            # Feedback & script refinement
│   │   └── export.py              # Script/audio export
│   ├── llm/                       # KEEP AS-IS
│   └── tts/                       # KEEP AS-IS
├── frontend/                      # Vue 3 + Vite frontend
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html                 # Vite entry point
│   ├── src/
│   │   ├── main.js                # Vue app bootstrap
│   │   ├── App.vue                # Root component (TopBar + router-view)
│   │   ├── router/
│   │   │   └── index.js           # Vue Router: /, /flow/:id, /settings
│   │   ├── stores/                # Pinia stores
│   │   │   ├── episodes.js        # Episode list, CRUD, filters
│   │   │   ├── flow.js            # Flow wizard state (steps, titles, segments)
│   │   │   └── settings.js        # App settings (localStorage + optional API)
│   │   ├── composables/           # Shared logic
│   │   │   ├── useApi.js          # API client (fetch wrapper + user ID)
│   │   │   └── useToast.js        # Toast notification system
│   │   ├── assets/
│   │   │   └── styles/
│   │   │       ├── variables.css   # Design tokens (colors, radii, shadows)
│   │   │       ├── base.css        # Reset, typography, global styles
│   │   │       ├── animations.css  # Keyframes (riseIn, bobble, dotpulse, etc.)
│   │   │       └── components.css  # Shared component styles
│   │   ├── components/
│   │   │   ├── TopBar.vue
│   │   │   ├── BottomBar.vue       # Flow navigation (back/next)
│   │   │   ├── LoadingOverlay.vue
│   │   │   ├── ToastNotification.vue
│   │   │   ├── dashboard/
│   │   │   │   ├── DashHero.vue
│   │   │   │   ├── StatsRow.vue
│   │   │   │   ├── SectionToolbar.vue  # Search, sort, filter
│   │   │   │   └── EpisodeCard.vue
│   │   │   ├── flow/
│   │   │   │   ├── FlowProgress.vue    # Dots + progress bar
│   │   │   │   ├── StepTopic.vue       # Step 1: topic input
│   │   │   │   ├── StepTitles.vue      # Step 2: title selection
│   │   │   │   ├── StepScript.vue      # Step 3: script review
│   │   │   │   ├── StepFeedback.vue    # Step 4: rating + feedback
│   │   │   │   ├── StepExport.vue      # Step 5: final export
│   │   │   │   ├── SegmentCard.vue     # Expandable script segment
│   │   │   │   ├── TitleCard.vue       # Selectable title option
│   │   │   │   ├── StarRating.vue      # Interactive star rating
│   │   │   │   └── OptionButton.vue    # Multi/single select button
│   │   │   ├── modals/
│   │   │   │   ├── VoiceModal.vue      # TTS voice config (bottom sheet)
│   │   │   │   ├── EditModal.vue       # Segment edit (center modal)
│   │   │   │   ├── DeleteModal.vue     # Delete confirmation
│   │   │   │   └── PublishModal.vue    # 3-step publish flow
│   │   │   └── settings/
│   │   │       ├── ShowInfoCard.vue
│   │   │       ├── PlatformCard.vue    # Google / Apple config
│   │   │       ├── AiConfigCard.vue
│   │   │       └── ToggleSwitch.vue
│   │   └── views/
│   │       ├── DashboardView.vue
│   │       ├── FlowView.vue
│   │       └── SettingsView.vue
│   └── dist/                      # Built output (gitignored, served by FastAPI)
├── prompts/                       # KEEP AS-IS
├── tests/                         # Backend tests
└── data/                          # Runtime data
```

### Files to DELETE

- `app/line_helpers.py` — LINE Flex Message builders
- `app/reply_utils.py` — LINE reply/push wrappers
- `app/state_machine.py` — Event dispatch (replaced by REST endpoints)
- `app/handlers/` — Entire directory (logic moves to `app/api/`)
- `tests/test_webhook.py` — LINE webhook tests
- `tests/test_state_machine.py` — State machine tests

---

## REST API Design

All endpoints under `/api/v1/`. User identified by `X-User-Id` header (UUID).

### Projects (Episodes)

```
GET    /api/v1/projects                                   # List all projects
POST   /api/v1/projects                                   # Create new project
GET    /api/v1/projects/{project_id}                      # Get project detail
PATCH  /api/v1/projects/{project_id}                      # Update project
DELETE /api/v1/projects/{project_id}                      # Delete project
```

### Titles

```
POST   /api/v1/projects/{project_id}/titles/generate      # Generate 5 titles via LLM
GET    /api/v1/projects/{project_id}/titles                # List titles
POST   /api/v1/projects/{project_id}/titles/{id}/select   # Select a title
```

### Scripts

```
POST   /api/v1/projects/{project_id}/scripts/generate     # Generate script via LLM
GET    /api/v1/projects/{project_id}/scripts/current       # Get current script + segments
PATCH  /api/v1/scripts/segments/{segment_id}               # Edit segment content
POST   /api/v1/scripts/segments/{segment_id}/refine        # LLM-powered refinement
```

### TTS

```
POST   /api/v1/scripts/segments/{segment_id}/tts           # Generate TTS audio
POST   /api/v1/voice-samples/{sample_id}/host-audio        # Upload host recording
```

### Feedback & Export

```
POST   /api/v1/projects/{project_id}/feedback              # Submit feedback + trigger regen
GET    /api/v1/projects/{project_id}/export/script         # Export full script text
GET    /api/v1/projects/{project_id}/export/audio          # Export audio file list
```

---

## Pydantic Models (replace `app/models.py`)

```python
class CreateProjectRequest(BaseModel):
    topic: str
    audience: str
    duration_min: int = 30
    style: str = "輕鬆閒聊"
    host_count: int = 1
    llm_provider: str = "gemini"
    cover_index: int = 0

class UpdateProjectRequest(BaseModel):
    topic: str | None = None
    audience: str | None = None
    duration_min: int | None = None
    style: str | None = None
    host_count: int | None = None
    status: str | None = None
    step: int | None = None
    progress: int | None = None

class TTSRequest(BaseModel):
    voice: str = "cmn-TW-Wavenet-A"
    speed: float = 1.0
    pitch: float = 0.0

class FeedbackRequest(BaseModel):
    score_content: int | None = None
    score_engagement: int | None = None
    score_structure: int | None = None
    text_feedback: str | None = None

class SegmentEditRequest(BaseModel):
    content: str
```

---

## Database Changes (`app/db.py`)

Add columns to `projects` table:

```sql
status      TEXT    DEFAULT 'draft'   -- 'draft' | 'done'
step        INTEGER DEFAULT 1         -- current flow step (1-5)
progress    INTEGER DEFAULT 0         -- 0-100 progress percentage
cover_index INTEGER DEFAULT 0         -- cover gradient index (0-5)
```

New query functions:
- `get_projects_by_user(db, user_id)` — list with status/step/progress
- `update_project(db, project_id, **fields)` — partial update
- `delete_project_cascade(db, project_id)` — delete with all related data
- `get_user_or_create(db, user_id)` — auto-create user from UUID

---

## Vue Frontend Architecture

### Design Token CSS (`frontend/src/assets/styles/variables.css`)

Extract from the design system document — all CSS custom properties:

```css
:root {
  --orange: #F4631E;
  --orange-pale: #FFE8D6;
  --teal: #1A8F8A;
  --teal-light: #D8F3F1;
  --teal-pale: #EAF9F8;
  --gold: #D4A017;
  --gold-pale: #FFF8E0;
  --ink: #0F0E0C;
  --ink-soft: #1C1A17;
  --cream: #FDF6EC;
  --warm-white: #FFFBF5;
  --gray-mid: #7A7060;
  --gray-light: #EAE2D6;
  --gray-pale: #F6EFE6;
  --shadow-card: 0 2px 20px rgba(0,0,0,.08);
  --radius: 20px;
  --radius-sm: 12px;
  --radius-xs: 8px;
}
```

### Vue Router (`frontend/src/router/index.js`)

```javascript
const routes = [
  { path: '/',            name: 'dashboard', component: DashboardView },
  { path: '/flow/:id',    name: 'flow',      component: FlowView },
  { path: '/settings',    name: 'settings',   component: SettingsView },
]
```

### Pinia Stores

**episodes store** — Dashboard data:
- `episodes[]`, `filter`, `searchQuery`, `sortBy`
- Actions: `fetchEpisodes()`, `createEpisode()`, `deleteEpisode(id)`

**flow store** — 5-step wizard state:
- `activeId`, `curScreen`, `topic`, `titles[]`, `selTitle`, `segments[]`, `version`, `ratings`, `voiceConfig`
- Actions: `loadProject(id)`, `saveProject()`, `generateTitles()`, `selectTitle()`, `generateScript()`, `submitFeedback()`

**settings store** — Config (backed by localStorage):
- All CFG fields from design system (show info, platforms, AI config)
- Actions: `loadSettings()`, `saveSettings()`, `savePlatform(plat)`

### API Composable (`frontend/src/composables/useApi.js`)

```javascript
const API_BASE = import.meta.env.DEV ? '' : '';  // Vite proxy handles /api in dev

let userId = localStorage.getItem('pc_user_id');
if (!userId) {
  userId = crypto.randomUUID();
  localStorage.setItem('pc_user_id', userId);
}

export function useApi() {
  async function api(method, path, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
    };
    if (body) opts.body = JSON.stringify(body);
    const resp = await fetch(`/api/v1${path}`, opts);
    if (!resp.ok) throw new Error(`API ${resp.status}`);
    return resp.json();
  }
  return { api, userId };
}
```

### Vite Config (`frontend/vite.config.js`)

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8900',
      '/audio': 'http://localhost:8900',
    },
  },
  build: {
    outDir: 'dist',
  },
})
```

### Component Mapping (reference HTML → Vue components)

| HTML Section | Vue Component | Key Props/Events |
|---|---|---|
| `.topbar` | `TopBar.vue` | `page`, `flowStep`, nav events |
| `.bot-bar` | `BottomBar.vue` | `canNext`, `@next`, `@back` |
| `.dash-hero` | `DashHero.vue` | `episodeCount`, `@newEpisode` |
| `.stats-row > .stat-card` | `StatsRow.vue` | `total`, `done`, `draft` |
| `.section-toolbar` | `SectionToolbar.vue` | `v-model:search`, `v-model:sort`, `v-model:filter` |
| `.ep-card` | `EpisodeCard.vue` | `episode`, `@continue`, `@delete`, `@publish` |
| `.flow-dots` | `FlowProgress.vue` | `currentStep`, `completedSteps` |
| Screen 1 form | `StepTopic.vue` | `v-model:topic`, audience/dur/style/host selects |
| `.title-card` | `TitleCard.vue` | `title`, `index`, `selected`, `@select` |
| `.seg-card` | `SegmentCard.vue` | `segment`, `expanded`, `@toggle`, `@edit`, `@voice` |
| Star rating | `StarRating.vue` | `v-model`, `label` |
| `.opt-btn` | `OptionButton.vue` | `label`, `icon`, `selected`, `@click` |
| Voice bottom sheet | `VoiceModal.vue` | `segmentId`, `@generate` |
| Edit center modal | `EditModal.vue` | `segment`, `@save` |
| Delete confirm | `DeleteModal.vue` | `episodeTitle`, `@confirm` |
| Publish 3-step | `PublishModal.vue` | `episode`, `@complete` |
| `.set-card` (platform) | `PlatformCard.vue` | `platform`, config fields |
| Toggle switch | `ToggleSwitch.vue` | `v-model` |

---

## Handler Logic Migration Map

| Source (handlers/) | Business Logic | Target (api/) |
|---|---|---|
| `onboarding.py::_finish_collect()` | Create project + gen titles | `api/projects.py` + `api/titles.py` |
| `title.py::handle_title_postback()` | Select title | `api/titles.py::select_title()` |
| `title.py::_regenerate_titles()` | Regen titles via LLM | `api/titles.py::generate_titles()` |
| `script.py::generate_script_for_project()` | LLM script gen | `api/scripts.py::generate_script()` |
| `script.py::_handle_segment_edit()` | LLM segment refine | `api/scripts.py::refine_segment()` |
| `tts.py::_start_tts_generation()` | TTS synthesis | `api/tts.py::generate_tts()` |
| `feedback.py::handle_feedback_*` | Scores + regen | `api/feedback.py::submit_feedback()` |
| `export.py::_export_script()` | Build text export | `api/export.py::export_script()` |

---

## Implementation Phases

### Phase 1: Backend API

1. **config.py** — Remove LINE config, keep API keys
2. **models.py** — Replace BotState with Pydantic request/response schemas
3. **db.py** — Add new columns (`status`, `step`, `progress`, `cover_index`), new query functions
4. **app/api/deps.py** — Shared dependencies (db connection, user_id from header)
5. **app/api/projects.py** — CRUD endpoints
6. **app/api/titles.py** — Generation + selection (extract from `onboarding.py` + `title.py`)
7. **app/api/scripts.py** — Generation + editing (extract from `script.py`)
8. **app/api/tts.py** — TTS generation (extract from `tts.py` handler)
9. **app/api/feedback.py** — Feedback + regen (extract from `feedback.py`)
10. **app/api/export.py** — Export endpoints (extract from `export.py`)
11. **main.py** — Rewrite: mount API routers, serve `frontend/dist/` in production, CORS for dev

### Phase 2: Vue Frontend Setup

1. Initialize Vite + Vue 3 project in `frontend/`
2. Set up `vite.config.js` with proxy to FastAPI
3. Create CSS design tokens from design system (`variables.css`, `base.css`, `animations.css`)
4. Create `useApi` composable and `useToast` composable
5. Set up Vue Router (3 routes)
6. Set up Pinia stores (episodes, flow, settings)

### Phase 3: Vue Components — Dashboard

1. `App.vue` + `TopBar.vue` — Shell and navigation
2. `DashboardView.vue` — Page layout
3. `DashHero.vue` — Hero section with CTA
4. `StatsRow.vue` — Statistics cards
5. `SectionToolbar.vue` — Search, sort, filter
6. `EpisodeCard.vue` — Episode grid cards with hover effects
7. `DeleteModal.vue` — Delete confirmation

### Phase 4: Vue Components — Flow (5-step wizard)

1. `FlowView.vue` — Wrapper with `BottomBar.vue` + `FlowProgress.vue`
2. `StepTopic.vue` + `OptionButton.vue` — Step 1 form
3. `StepTitles.vue` + `TitleCard.vue` — Step 2 selection
4. `StepScript.vue` + `SegmentCard.vue` — Step 3 review
5. `VoiceModal.vue` — TTS config bottom sheet
6. `EditModal.vue` — Segment editing modal
7. `StepFeedback.vue` + `StarRating.vue` — Step 4 rating
8. `StepExport.vue` — Step 5 final export
9. `LoadingOverlay.vue` — Loading state during LLM/TTS calls

### Phase 5: Vue Components — Settings & Publish

1. `SettingsView.vue` — Settings page layout
2. `ShowInfoCard.vue` — Show info form
3. `PlatformCard.vue` + `ToggleSwitch.vue` — Google/Apple config
4. `AiConfigCard.vue` — LLM/TTS config
5. `PublishModal.vue` — 3-step publish flow

### Phase 6: Cleanup & Testing

1. Delete LINE-specific files (line_helpers, reply_utils, state_machine, handlers/)
2. Delete LINE-specific tests (test_webhook, test_state_machine)
3. Update `pyproject.toml` — remove `line-bot-sdk`, add `python-multipart`
4. Update `.env.example` — remove LINE env vars
5. Update `Dockerfile` — multi-stage build (npm build + Python)
6. Write new backend API tests
7. Update `tests/conftest.py` — replace LINE mock with httpx AsyncClient

---

## Dependency Changes

### Backend (`pyproject.toml`)

```diff
 dependencies = [
     "fastapi>=0.115",
     "uvicorn[standard]>=0.34",
-    "line-bot-sdk>=3.14",
+    "python-multipart>=0.0.9",
     "aiosqlite>=0.20",
     "pydantic-settings>=2.7",
     "python-dotenv>=1.0",
     "anthropic>=0.42",
     "google-genai>=1.0",
     "google-cloud-texttospeech>=2.22",
     "aiohttp>=3.10",
 ]
```

### Frontend (`frontend/package.json`)

```json
{
  "dependencies": {
    "vue": "^3.5",
    "vue-router": "^4.5",
    "pinia": "^3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2",
    "vite": "^6.1"
  }
}
```

### Dockerfile (multi-stage)

```dockerfile
# Stage 1: Build frontend
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python backend
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev
COPY . .
COPY --from=frontend /frontend/dist ./frontend/dist
EXPOSE 8900
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8900"]
```

---

## Verification

1. **Backend API**: `pytest` — all API tests pass with mocked LLM/TTS
2. **Frontend dev**: `cd frontend && npm run dev` — Vite dev server at :5173, API proxied to :8900
3. **Full Flow**: Create episode → generate titles → select → generate script → edit segment → generate TTS → give feedback → export
4. **Settings**: Configure LLM/TTS keys → verify persistence
5. **CRUD**: Create, edit, delete episodes from dashboard
6. **Production build**: `cd frontend && npm run build` → `uvicorn app.main:app` serves everything at :8900
7. **No LINE traces**: `grep -r "line_bot\|linebot\|line-bot" app/` returns nothing

---

## Files Unchanged (zero modifications needed)

- `app/llm/base.py`, `claude_provider.py`, `gemini_provider.py`, `factory.py`, `prompt_builder.py`
- `app/tts/tts_service.py`, `ssml_builder.py`, `audio_storage.py`
- `prompts/system.txt`, `title_generation.txt`, `script_generation.txt`, `script_refinement.txt`
- `tests/test_db.py` (extend only), `test_llm_providers.py`, `test_prompt_builder.py`, `test_ssml_builder.py`
