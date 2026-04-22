# 設計規範 V2 — 黑灰漸層 Dashboard

> 所有 V2 元件必須遵守本規範。新增元件前先查表，禁止寫死數值或顏色。
> Token 統一定義於 `src/ui_v2/theme_v2.py` 的 `V2Theme` 類別。

---

## 1. 色彩 Token

### 1.1 中性色（背景／文字／邊框）

| Token | 值 | 用途 |
|------|----|------|
| `BG_TOP` / `BG_MID` / `BG_BOTTOM` | `#1f1f24 → #141418 → #08080a` | 主視窗漸層 |
| `BG_SURFACE` | `#1d1d22` | 卡片底（半透明感） |
| `BG_ELEVATED` | `#26262c` | 第二層元件（卡內小區塊、hover）|
| `BG_HOVER` | `#2d2d34` | hover 高亮 |
| `BG_INPUT` | `#1a1a1e` | 輸入框、按鈕底 |
| `BORDER` | `#2a2a30` | 通用邊框（≤ 1px） |
| `BORDER_SOFT` | `#1d1d22` | 區塊內細分隔 |
| `BORDER_HOVER` | `#42424a` | hover 邊框 |
| `TEXT_HI` | `#f1f2f5` | 主標題、數字 |
| `TEXT` | `#a8aab2` | 正文 |
| `TEXT_DIM` | `#6e7079` | 次要標籤、副標 |
| `TEXT_MUTED` | `#454650` | 月份字、年份字、disabled |

### 1.2 強調色（功能色）

| Token | 值 | **唯一用途** |
|------|----|------------|
| `ORANGE` | `#ff8c42` | **主 CTA 按鈕、active 狀態指示**（不准用作裝飾色） |
| `PURPLE` | `#9b6df1` | 「強度／能量」類數據（傷害、暴擊…） |
| `BLUE` | `#5c8df5` | 「資料／訊息」類數據（次數、計數） |
| `CYAN` | `#4dd2e8` | 「速度／時間」類數據（冷卻、頻率） |
| `PINK` | `#f06b9b` | 「特殊／稀有」類數據（限定、成就） |
| `GREEN` | `#56d99a` | **正向 delta、成功狀態** |
| `RED` | `#ef5b6d` | **負向 delta、錯誤、close 按鈕 hover** |
| `YELLOW` | `#fbbf24` | warning 唯一用色 |

**規則：**
- **絕對不准** 同一張卡片用 3 種以上強調色
- 強調色預設用於 icon、數字、active 邊條，**不用於文字段落**
- delta 標籤只能用 `GREEN`（正）或 `RED`（負）

---

## 2. 字級系統

| Token | size | weight | color | 用途 |
|------|------|--------|-------|------|
| `FONT_DISPLAY` | 18 | 700 | `TEXT_HI` | 頁首問候 |
| `FONT_SECTION` | 14 | 700 | `TEXT_HI` | 區塊主標題 |
| `FONT_CARD_TITLE` | 13 | 700 | `TEXT_HI` | 卡片內標題 |
| `FONT_BODY` | 12 | 500 | `TEXT` | 正文 |
| `FONT_CAPTION` | 11 | 500 | `TEXT_DIM` | 副標、說明 |
| `FONT_LABEL` | 10 | 700 | `TEXT_DIM` | 大寫小標（letter-spacing 1px）|
| `FONT_METRIC` | 22 | 700 | `TEXT_HI` | 大數字（KPI） |
| `FONT_METRIC_SM` | 16 | 700 | `TEXT_HI` | 小數字 |
| `FONT_DELTA` | 11 | 700 | GREEN/RED | 變化率 |

**規則：**
- 一張卡內字級不超過 4 種
- 不准在 QSS 直接寫 `font-size: Npx`，一律用 `apply_font(label, FONT_XXX)` 或 token

---

## 3. 間距尺度（4 級）

```
S_XS = 4    S_SM = 8    S_MD = 12   S_LG = 16   S_XL = 20   S_2XL = 24
```

**規則：**
- **禁用** 5/6/7/9/10/11/13/14… 等非倍數值
- 卡片內 padding：`S_LG` (16)
- 卡片之間 gap：`S_MD` (12)
- 區塊（卡片群組）之間 gap：`S_LG` (16)
- 區塊與頁緣：`S_2XL` (24)

---

## 4. 圓角尺度（3 級）

| Token | 值 | 用途 |
|------|----|------|
| `R_SM` | 6 | 小元件（chip、tag、checkbox、按鈕）|
| `R_MD` | 10 | 卡內小區塊、icon 底 |
| `R_LG` | 14 | 主卡片、面板 |

圓形元件使用 `R = width / 2`，不另開 token。

---

## 5. Icon 系統

### 5.1 強制規則
- **完全禁用 emoji** — 系統渲染不一致，會出現彩色花斑
- 一律使用 **monochrome unicode 幾何符號** + `color` 屬性著色
- 所有 icon 容器固定 `36×36`、`R_MD` 圓角、半透明背景 `accent + alpha 33`，icon 本身用 `accent` 純色

### 5.2 慣用字符（隨用隨查）

| 用途 | 字符 |
|------|------|
| 技能 / 主動 | `◆` |
| 怪物 / 威脅 | `✦` |
| 圖片 / 視窗 | `▦` |
| 金錢 / 費用 | `$` |
| 資源 / 收藏 | `◉` |
| 設定 | `⚙` |
| 通知 | `◔` |
| 個人 | `◐` |
| 加 / 新增 | `+` |
| 重置 | `↺` |
| 關閉 | 自繪 X |
| 最大化 | 自繪 □ |
| 最小化 | 自繪 — |

### 5.3 IconBadge 元件
所有 icon 必須包在 `IconBadge(glyph, color, size=36)` 內，不准散裝 QLabel。

---

## 6. 元件配方

### 6.1 Card（基礎容器）
```
背景: BG_SURFACE
邊框: 無
圓角: R_LG (14)
padding: S_LG (16)
內元素 spacing: S_SM (8) 或 S_MD (12)
```

### 6.2 StatCard（KPI 卡）
**固定四段式垂直結構，靠上對齊：**
```
┌─────────────────────┐
│ [IconBadge 36×36]   │ ← 段 1
│                     │
│ LABEL (FONT_LABEL)  │ ← 段 2（小寫大寫小標）
│ 22 (FONT_METRIC)    │ ← 段 3
│ +6.4% (FONT_DELTA)  │ ← 段 4（彩色 chip）
└─────────────────────┘
段間距: S_SM (8)
卡片高度: 固定 160px（避免上下飄）
```

### 6.3 ServiceCard（資訊卡）
```
左：標題 + 副標（垂直）
右：IconBadge
底：金額 + CTA 按鈕（左右對齊）
高度: 固定 120px
```

### 6.4 Chip（標籤）
```
高度: 22
padding: 0 10
圓角: 11 (= height/2)
font: FONT_DELTA
變體: neutral / success / danger / warning / accent
```

### 6.5 Button
| 變體 | 用途 | 規則 |
|------|------|------|
| `primary` | 主 CTA | ORANGE 底白字，**全頁同時最多 1 個** |
| `default` | 次要 | BG_INPUT + BORDER |
| `ghost` | 第三層 | 透明 + dim text，hover 才浮起 |
| `danger` | 危險 | 透明 + RED 文字 |

---

## 7. 互動狀態

| 狀態 | 變化 |
|------|------|
| hover | 背景升一層（SURFACE → ELEVATED → HOVER），邊框升一級 |
| active | accent color 顯示（border-left 3px 或 text color）|
| focus | 邊框 = ORANGE |
| disabled | text → MUTED，bg → SURFACE |

**禁止：** hover 時改變元件大小、位置、字級。

---

## 8. 卡片內部佈局範本

所有 card 必須遵守其中一種佈局：

### A. 垂直堆疊（StatCard、簡單卡）
```
[icon]  ← 頂部
[label]
[metric]
[delta]
```

### B. 左右分區（ServiceCard）
```
[標題群組]  [icon]
[價格]      [CTA]
```

### C. 標題 + 內容（ChartCard）
```
[標題列：左標題、右控件]
[─── 內容 ───]
[底部標籤列]
```

---

## 9. 違規檢查清單

提交前自檢：
- [ ] 沒寫死 `font-size: Npx`，全部用 token
- [ ] 沒寫死顏色 `#xxxxxx`，全部用 `T.XXX`
- [ ] 沒寫死間距 `setSpacing(7)` 等非標準值
- [ ] 沒用 emoji 當 icon
- [ ] 同卡片強調色 ≤ 2
- [ ] 全頁 primary button ≤ 1
- [ ] 圓角只用 6/10/14 三值
