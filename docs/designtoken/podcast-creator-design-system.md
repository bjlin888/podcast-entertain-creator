# Podcast 創作助手 — Design System

> **版本** v1.0 · **產品** Podcast 創作助手 · **最後更新** 2026-02-24

---

## 1. Design Philosophy

### 核心方向：Warm Toy-like Studio

本系統採用「**暖色工作室（Warm Creative Studio）**」美學——在溫暖、手感的底色上，以強烈的橙色為能量核心，搭配沉穩的青色（Teal）形成對比張力。整體視覺語言傳達「**有溫度的創作工具**」，讓非技術背景的 Podcast 創作者感到親切、有活力、值得信賴。

### 四個設計原則

| 原則 | 說明 |
|------|------|
| **溫暖（Warmth）** | 奶油色底、暖棕灰文字，避免冷硬的純白與純黑 |
| **動態（Motion）** | 每個操作都有微動效回饋，讓介面「有生命感」 |
| **層次（Depth）** | 使用陰影、毛玻璃、漸層光暈創造視覺景深 |
| **聚焦（Focus）** | 橙色是唯一的 CTA 顏色，保持行動導引清晰 |

---

## 2. Color System

### 2.1 原色（Primary）

| Token | Hex | 用途 |
|-------|-----|------|
| `--orange` | `#F4631E` | 主要 CTA、強調、進度指示 |
| `--orange-pale` | `#FFE8D6` | 橙色的淺背景、hover 填色 |

### 2.2 強調色（Accent）

| Token | Hex | 用途 |
|-------|-----|------|
| `--teal` | `#1A8F8A` | 完成狀態、次要 CTA、連結色 |
| `--teal-light` | `#D8F3F1` | Teal 淺背景、tag 背景 |
| `--teal-pale` | `#EAF9F8` | Teal 最淺背景、音訊播放器底色 |
| `--gold` | `#D4A017` | 提示框邊線、警示強調 |
| `--gold-pale` | `#FFF8E0` | 提示框背景（tip-box） |

### 2.3 中性色（Neutral）

| Token | Hex | 用途 |
|-------|-----|------|
| `--ink` | `#0F0E0C` | 主要文字色（近黑，帶暖棕） |
| `--ink-soft` | `#1C1A17` | 深色背景（Dashboard Hero、TopBar Dark） |
| `--cream` | `#FDF6EC` | 頁面底色、輸入框背景 |
| `--warm-white` | `#FFFBF5` | 卡片背景、TopBar Light 背景 |
| `--gray-mid` | `#7A7060` | 次要文字、placeholder、label |
| `--gray-light` | `#EAE2D6` | 分隔線、border、進度軌道 |
| `--gray-pale` | `#F6EFE6` | 最淺灰背景、次要按鈕底色 |

### 2.4 語意色（Semantic）

| 語意 | 顏色 | Token / 值 |
|------|------|-----------|
| 成功（Done） | 綠 | `#4ADE80` |
| 進行中（Draft） | 橙 | `--orange` |
| 資訊（Info） | 藍 | `#4285F4`（Google 發布色） |
| 警告（Warning） | 金 | `--gold` |

### 2.5 Hero 漸層光暈（Radial Orbs）

Dashboard Hero 與 Settings Hero 使用雙徑向光暈製造深度：

```css
/* Orb 1：橙，右上角 */
background: radial-gradient(circle, rgba(244,99,30,.24) 0%, transparent 65%);
width: 440px; height: 440px; right: -100px; top: -120px;

/* Orb 2：青，左下角 */
background: radial-gradient(circle, rgba(26,143,138,.17) 0%, transparent 65%);
width: 280px; height: 280px; left: -60px; bottom: -80px;
```

---

## 3. Typography

### 3.1 字型配對

| 角色 | 字型 | 用途 |
|------|------|------|
| **Display** | Playfair Display（Serif） | Hero 標題、統計數字 |
| **Body** | Noto Sans TC（Sans） | 全站 UI 文字、按鈕、標籤 |

```css
font-family: 'Noto Sans TC', sans-serif;
font-family: 'Playfair Display', serif;
```

### 3.2 字型尺度（Type Scale）

| 層級 | 大小 | 粗細 | 用途 |
|------|------|------|------|
| Hero H1 | 40px | 900 | Dashboard / Settings 大標題 |
| Page H1 | 28–30px | 900 | 流程頁標題 |
| Section H2 | 18px | 900 | 區塊標題、卡片標題 |
| Card H3 | 15–17px | 700 | 卡片標頭 |
| Body | 14–15px | 400–500 | 一般段落 |
| Small / Label | 11–13px | 700 | 上標、tag、表單 label |
| Micro | 10–11px | 700–800 | badge、ep-num、date |

### 3.3 Letter Spacing 規範

| 場景 | 值 |
|------|-----|
| UPPERCASE 標籤 / Eyebrow | `.06em`–`.18em` |
| 一般文字 | `0`（預設） |
| Badge / Monospace | `.04em`–`.1em` |

---

## 4. Spacing & Layout

### 4.1 Border Radius

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius` | `20px` | 主要卡片（ep-card、set-card、ctr-box） |
| `--radius-sm` | `12px` | 按鈕、輸入框、segment card |
| `--radius-xs` | `8px` | 小型 badge、btn-to-dash、設定輸入框 |
| 圓形 pill | `99px` | tag、filter button、搜尋框、toast |
| Logo icon | `9px` | 品牌 icon 方塊 |

### 4.2 頁面容器

| 容器 | 最大寬度 | padding |
|------|---------|---------|
| Dashboard（`dash-main`） | 960px | `0 24px 80px` |
| Flow（`flow-main`） | 760px | `36px 24px 120px` |
| Settings（`pgSettings-main`） | 760px | `36px 24px 80px` |

### 4.3 間距慣例

```
Section 間距：28px（margin-bottom）
Card 間距：14–18px
Card 內 padding：24–26px
Grid gap（ep-grid）：18px
Stats row gap：14px
Form field gap：12–14px
```

---

## 5. Component Library

### 5.1 Button

#### Primary Button
```css
background: var(--orange);
color: #fff;
padding: 17px 20px;
border-radius: var(--radius-sm);
font-size: 17px; font-weight: 700;
/* hover */
background: #FF7A3A;
transform: translateY(-2px);
box-shadow: 0 6px 20px rgba(244,99,30,.35);
```

#### Secondary Button
```css
background: transparent;
color: var(--orange);
border: 2px solid var(--orange);
padding: 11px 22px;
/* hover */
background: var(--orange-pale);
transform: translateY(-1px);
```

#### Teal Button
```css
background: var(--teal);
color: #fff;
padding: 11px 22px;
/* hover */
background: #14706C;
box-shadow: 0 4px 14px rgba(26,143,138,.3);
```

#### New Episode Button（Hero CTA）
```css
background: var(--orange);
box-shadow: 0 4px 20px rgba(244,99,30,.42);
padding: 14px 24px;
gap: 10px; /* icon + label */
/* hover */
background: #FF7A3A;
transform: translateY(-2px);
box-shadow: 0 8px 30px rgba(244,99,30,.55);
```

#### Small Button（`btn-sm`）
```css
padding: 7px 14px;
border-radius: 99px;
font-size: 12px; font-weight: 700;
/* bsm-edit */  background: var(--gray-pale);
/* bsm-audio */ background: var(--teal-light); color: var(--teal);
```

#### Settings Button（TopBar）
```css
width: 36px; height: 36px;
border-radius: 9px;
background: rgba(255,255,255,.1);
/* active state */
background: var(--teal) !important;
```

#### Publish Button（Episode Card）
```css
background: linear-gradient(90deg, #4285F4, #34A0F4);
/* hover */
background: linear-gradient(90deg, #2B6FDB, #2090E0);
box-shadow: 0 3px 10px rgba(66,133,244,.3);
```

### 5.2 Form Inputs

#### Standard Input / Textarea
```css
padding: 15px 18px;
border: 2px solid var(--gray-light);
border-radius: var(--radius-sm);
font-size: 15px;
background: var(--cream);
/* focus */
border-color: var(--orange);
box-shadow: 0 0 0 4px rgba(244,99,30,.1);
background: #fff;
```

#### Settings Input
```css
padding: 11px 14px;
border: 2px solid var(--gray-light);
border-radius: var(--radius-xs);
/* focus */
border-color: var(--teal);
box-shadow: 0 0 0 3px rgba(26,143,138,.12);
```

#### Search Input
```css
width: 200px; height: 36px;
border-radius: 99px;
padding-left: 36px; /* icon space */
/* focus */
border-color: var(--orange);
width: 240px; /* expand on focus */
```

### 5.3 Cards

#### Episode Card（`ep-card`）
```
├── ep-cover（118px）
│   ├── ep-cover-em（48px emoji）
│   ├── ep-num（top-left badge）
│   ├── ep-dot（top-right status）
│   └── ep-quick（hover overlay）
└── ep-body
    ├── ep-top-row（badge + date）
    ├── ep-title（2-line clamp）
    ├── ep-tags（🎭 style / ⏱ dur / 📍 step）
    ├── ep-prog-row（label + pct）
    ├── ep-bar-bg → ep-bar-fill
    └── ep-actions（buttons）
```

**Hover 效果：**
```css
transform: translateY(-6px);
box-shadow: 0 18px 48px rgba(0,0,0,.13);
border-color: rgba(244,99,30,.3);
/* cover emoji */
transform: scale(1.14) rotate(5deg);
/* quick actions */
opacity: 0 → 1; transform: translateY(8px) → 0;
```

#### Setting Card（`set-card`）
```
├── set-card-header
│   ├── platform-logo（44px rounded icon）
│   ├── set-card-info（h3 + p）
│   └── toggle（switch）
├── status badge
├── set-field-grid（1fr 1fr）
└── set-actions（test + save）
```

### 5.4 Badges & Tags

#### Episode Badge
```css
/* Done  */ background: var(--teal-light); color: var(--teal);
/* Draft */ background: var(--orange-pale); color: var(--orange);
font-size: 10px; font-weight: 800;
padding: 3px 10px; border-radius: 99px;
```

#### Segment Tag
```css
/* Intro */ background: var(--gold-pale);  color: var(--gold);
/* Seg   */ background: var(--teal-light); color: var(--teal);
/* Outro */ background: var(--orange-pale);color: var(--orange);
font-size: 10px; font-weight: 700; padding: 3px 10px;
```

#### Platform Status Badge
```css
/* Ok      */ background: var(--teal-light); color: var(--teal);
/* Pending */ background: var(--orange-pale);color: var(--orange);
/* None    */ background: var(--gray-pale);  color: var(--gray-mid);
padding: 4px 11px; border-radius: 99px;
```

#### Cue Badge
```css
background: #EEF2FF; color: #5B6CF8;
font-size: 11px; font-weight: 600;
padding: 2px 7px; border-radius: 5px;
```

### 5.5 Status Indicator（ep-dot）

```css
/* Done  */ background: #4ADE80; （靜態）
/* Draft */ background: var(--orange); animation: dotpulse 2s ease infinite;

@keyframes dotpulse {
  0%,100% { box-shadow: 0 0 0 2px rgba(255,255,255,.35); }
  50%      { box-shadow: 0 0 0 6px rgba(244,99,30,.18); }
}
```

### 5.6 Toggle Switch

```css
/* Track：off */ background: var(--gray-light);
/* Track：on  */ background: var(--teal);
/* Thumb */      width: 18px; height: 18px;
                 background: #fff;
                 box-shadow: 0 1px 4px rgba(0,0,0,.18);
/* Transition */ transform: translateX(18px); /* on */
```

### 5.7 Progress Bar（Flow）

```css
background: var(--gray-light);
height: 7px; border-radius: 99px;
/* fill */
background: linear-gradient(90deg, var(--orange), #FF8A50);
transition: width .5s cubic-bezier(.4,0,.2,1);
```

### 5.8 Episode Progress Bar（Card）

```css
height: 5px;
/* draft */ background: linear-gradient(90deg, var(--orange), #FF8A50);
/* done  */ background: linear-gradient(90deg, var(--teal), #24A89F);
transition: width .5s ease;
```

### 5.9 Filter Pills

```css
/* default */ background: var(--warm-white); border: 1.5px solid var(--gray-light);
             color: var(--gray-mid);
/* active  */ background: var(--ink); color: #fff; border-color: var(--ink);
padding: 7px 15px; border-radius: 99px;
```

### 5.10 Option Buttons（`opt-btn`）

```css
padding: 13px 10px;
border: 2.5px solid var(--gray-light);
border-radius: var(--radius-sm);
/* hover */
border-color: #FF8A50; background: var(--orange-pale);
transform: translateY(-2px);
/* selected */
border-color: var(--orange); background: var(--orange-pale);
color: var(--orange); font-weight: 700;
box-shadow: 0 0 0 3px rgba(244,99,30,.14);
```

### 5.11 Modals

#### Sheet（Bottom Sheet / Voice Modal）
```css
border-radius: 26px 26px 0 0;
padding: 22px 22px 38px;
max-width: 760px;
@keyframes slideUp { from{transform:translateY(100%)} to{transform:translateY(0)} }
backdrop: rgba(15,14,12,.52) + blur(3px)
```

#### Center Modal（Edit / Delete / Publish）
```css
border-radius: var(--radius);
padding: 30px 26px 26px;
max-width: 580px; max-height: 90vh;
box-shadow: 0 24px 80px rgba(0,0,0,.2);
@keyframes popIn { from{transform:scale(.93);opacity:0} to{transform:scale(1);opacity:1} }
backdrop: rgba(15,14,12,.55) + blur(3px)
```

---

## 6. Motion & Animation

### 6.1 Keyframe 動畫

| 名稱 | 效果 | 使用場景 |
|------|------|---------|
| `riseIn` | `opacity 0→1` + `translateY 12px→0` | 頁面切換、segment 展開 |
| `bobble` | `translateY 0→-7px→0`，2.4s loop | Flow 頁面大 icon |
| `dotpulse` | box-shadow pulse，2s loop | Episode 進行中狀態點 |
| `spin` | rotate 360deg，0.8s linear | Loading spinner |
| `slideUp` | `translateY 100%→0` | Bottom sheet modal |
| `popIn` | `scale .93→1` + `opacity 0→1` | Center modal |

### 6.2 Transition 規範

| 場景 | 數值 |
|------|------|
| 一般 hover | `all .15s`–`.2s` |
| 卡片 hover（立體感） | `all .24s` |
| 按鈕 hover | `all .18s`–`.22s` |
| TopBar 背景切換 | `background .3s` |
| 搜尋框展開 | `width .2s`（200px→240px） |
| Progress bar 填充 | `width .5s cubic-bezier(.4,0,.2,1)` |
| Segment toggle arrow | `transform .2s` |
| Audio progress | `width .1s` |
| Quick actions reveal | `opacity + translateY .22s` |
| Toggle thumb | `transform .22s` |

### 6.3 微互動原則

- **translateY(-2px) ~ (-6px)**：所有可點擊卡片 hover 向上浮起
- **scale(1.06) ~ (1.2)**：play button、star button hover 放大
- **transform: translateX(3px)**：platform link hover 向右移
- 所有動效不超過 **0.5s**，保持輕快感

---

## 7. Navigation & Pages

### 7.1 TopBar 狀態

| 狀態 | 背景 | 用途 |
|------|------|------|
| `.dark` | `var(--ink-soft)` + 白色邊線 | Dashboard、Settings |
| `.light` | `var(--warm-white)` + 灰色邊線 | 五步流程頁 |

### 7.2 Page 架構

```
App
├── pgDash（Dashboard）
│   ├── dash-hero
│   ├── stats-row
│   ├── section-toolbar（search + sort + filter）
│   └── ep-grid
├── pgFlow（五步流程）
│   ├── s1：填寫主題
│   ├── s2：選標題
│   ├── s3：審閱腳本
│   ├── s4：給意見
│   └── s5：匯出
└── pgSettings（系統設定）
    ├── 節目基本資訊
    ├── Google Podcasts 設定
    ├── Apple Podcasts 設定
    └── AI 模型設定
```

### 7.3 Flow Progress Indicator

```css
/* Dot states */
.flow-dot         → border: gray, bg: transparent  （未到）
.flow-dot.active  → border+bg: var(--orange)        （當前）
.flow-dot.done    → border+bg: var(--teal)          （已完成）

/* Line states */
.flow-line        → background: var(--gray-light)
.flow-line.done   → background: var(--teal)
```

---

## 8. Iconography

### 8.1 使用規範

本系統全面使用 **emoji icon**，不依賴 icon font 或 SVG sprite，確保跨平台一致性且零依賴。

### 8.2 語意 Emoji 對照

| 場景 | Emoji |
|------|-------|
| 品牌 Logo | 🎙️ |
| Dashboard Hero 裝飾 | 🎙（旋轉 -14deg, scaleX(-1)） |
| Settings Hero 裝飾 | ⚙️（旋轉 +12deg） |
| 新增集數 | ＋ |
| 系統設定 | ⚙️ |
| 搜尋 | 🔍 |
| 編輯 | ✏️ |
| 刪除 | 🗑️ |
| 試聽 | 🔊 |
| 發布 | 📡 |
| 已完成 | ✅ |
| 進行中 | ⏳ |
| 警告提示 | ⚠️ |
| 載入 | spin（CSS only） |
| 成功 | 🎉 |
| Google Podcasts | 🎙️ |
| Apple Podcasts | 🍎 |
| RSS Feed | 🔗 |
| API Key | 🔑 |
| Claude / AI | 🤖 |

### 8.3 Platform Logo（色塊）

```css
.pl-google { background: linear-gradient(135deg, #4285F4, #34A0F4); }
.pl-apple  { background: linear-gradient(135deg, #fc3c44, #ff6b8a); }
.pl-show   { background: linear-gradient(135deg, var(--orange), #FF8A50); }
```

---

## 9. Episode Cover System

六組預設封面漸層（`COVERS` array），搭配對應 emoji：

| Index | 漸層 | Emoji |
|-------|------|-------|
| 0 | `#F4631E → #FF8A50`（橙） | 🎯 |
| 1 | `#1A8F8A → #24A89F`（青） | 🌊 |
| 2 | `#6B48FF → #A78BFA`（紫） | ✨ |
| 3 | `#D4A017 → #F6D860`（金） | ⚡ |
| 4 | `#E53E8A → #F472B6`（粉） | 🎵 |
| 5 | `#2D6A4F → #52B788`（綠） | 🌿 |

新集數封面以 `Math.random()` 隨機指派，`ci` 欄位儲存 index。

---

## 10. Responsive Breakpoints

### 10.1 斷點

| 斷點 | 值 |
|------|-----|
| Mobile | `max-width: 640px` |

### 10.2 Mobile 調整清單

```css
.topbar          → padding: 0 14px
.flow-nav        → display: none
.dash-hero       → padding: 28px 20px 32px; border-radius: 0 0 22px 22px
.dash-hero h1    → font-size: 26px
.settings-hero h1→ font-size: 22px
.stats-row       → gap: 9px
.stat-num        → font-size: 28px
.stat-icon       → display: none
.ep-grid         → grid-template-columns: 1fr（單欄）
.set-field-grid  → grid-template-columns: 1fr（單欄）
.search-inp      → width: 160px（focus: 180px）
.dash-main,
.flow-main,
.pgSettings-main → padding-left/right: 14px
```

---

## 11. Shadow System

| 名稱 | 值 | 用途 |
|------|-----|------|
| `--shadow-card` | `0 2px 20px rgba(0,0,0,.08)` | 一般卡片預設陰影 |
| card:hover | `0 18px 48px rgba(0,0,0,.13)` | Episode card hover |
| stat-card:hover | `0 10px 30px rgba(0,0,0,.11)` | Stat card hover |
| ctr-box | `0 24px 80px rgba(0,0,0,.2)` | Center modal |
| btn-new:hover | `0 8px 30px rgba(244,99,30,.55)` | Hero CTA hover |
| success-circle | `0 8px 32px rgba(26,143,138,.3)` | 完成圓形 icon |
| topbar.light | `0 2px 12px rgba(0,0,0,.04)` | 亮色 TopBar |

---

## 12. Keyboard Shortcuts

| 按鍵 | 動作 | 條件 |
|------|------|------|
| `N` | 新增集數 | 在 Dashboard 頁、非 input focus |
| `Ctrl + Enter` | 下一步 | 在 Flow 頁 |
| `Escape` | 關閉所有 Modal | 任何時候 |

---

## 13. State Management（前端）

### 13.1 Global State（`S` object）

```js
S = {
  episodes: [],       // 集數列表
  filter: 'all',      // dashboard filter
  activeId: null,     // 當前編輯的集數 ID
  curScreen: 1,       // 流程當前步驟（1–5）
  topic, titles, selTitle, segments,  // 流程資料
  version: 1,         // 腳本版本號
  vc: { voice, speed, pitch },         // TTS 設定
  voiceSeg, editIdx, delId,            // Modal 狀態
  ratings: { st1:0, st2:0, st3:0 },   // 評分
  _script: '',        // 最終腳本文字
  pubId: null,        // 當前發布的集數 ID
  pubPlats: Set(),    // 選中的發布平台
}
```

### 13.2 Settings Config（`CFG` object）

```js
CFG = {
  // 節目資訊
  'show-name', 'show-desc', 'author', 'email', 'website',
  'category', 'lang', 'explicit',
  // Google Podcasts
  'google-enabled', 'google-rss', 'google-verify', 'google-interval',
  // Apple Podcasts
  'apple-enabled', 'apple-id', 'apple-provider-id', 'apple-key',
  'apple-key-id', 'apple-team-id', 'apple-rss',
  // AI / TTS
  'llm-provider', 'llm-model', 'llm-key',
  'tts-provider', 'tts-key',
}
// 儲存至 localStorage('pc_cfg')
```

---

## 14. Publish Flow

### 發布流程（3 步驟 Modal）

```
Step 1（pubStep1）
├── 平台選擇（pub-plat × 2，可多選）
│   ├── Google Podcasts（RSS）
│   └── Apple Podcasts（Connect API）
├── 集數資訊填寫
│   ├── 標題、摘要、編號、發布日期、音訊 URL
└── 確認前檢查 CFG 設定完整性

Step 2（pubStep2）
└── 逐平台顯示發布進度（模擬 async）

Step 3（pubStep3）
├── 成功訊息
├── 各平台連結
└── 更新 episode.published / publishedAt
```

### 觸發條件

- 僅 **status === 'done'** 的集數可發布
- 顯示位置：Episode card 底部按鈕 + Cover hover 快速操作列

---

## 15. Accessibility Notes

| 項目 | 規範 |
|------|------|
| 互動元素 ID | 所有關鍵元素有明確 ID（`#searchInp`, `#sortSel`, `#epGrid`…） |
| Modal backdrop click | 點擊遮罩可關閉 Modal |
| Escape 鍵 | 關閉所有 Modal |
| 按鈕字體 | 全部顯式指定 `font-family: 'Noto Sans TC', sans-serif`，避免系統字體干擾 |
| 禁用狀態 | `btn-primary:disabled` 有明確視覺回饋（灰色、cursor: not-allowed） |
| Form placeholder | 使用 `#BDB0A2`，對比度符合 AA 要求 |

---

*Design System by Podcast 創作助手 · 依 Warm Creative Studio 美學原則維護*
