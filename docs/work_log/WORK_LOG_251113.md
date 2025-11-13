# 工作日誌

最後更新：2025-11-13

---

## 📋 待辦事項

### 🎯 專案實作順序

根據初始規劃，完整的實作順序如下：

1. ✅ **首頁調整** - 移除不需要的區塊、更新表格結構
2. ✅ **電影詳細頁調整** - 新增追蹤按鈕、調整關鍵指標、收合功能
3. ✅ **新電影預測頁 UI** - 建立頁面結構、搜尋區塊、表格、模型選擇
4. ⏳ **預測頁核心邏輯** - 實作搜尋功能、表格驗證、預測 API 呼叫
5. ⏳ **後端 API 整合** - 連接真實 API、實作預測邏輯、資料處理
6. ⏳ **測試與部署** - 完整功能測試、效能優化、部署設定

---

### 🎨 前端 UI 重構

#### CSS 模組化拆分（優先）
**目標**: 將現有的 main.css 和 components.css 拆分為模組化架構

**拆分方案**:
```
static/css/
├── variables.css          # CSS 變數（色彩、尺寸、間距）
├── base.css              # 基礎重置、全域樣式
├── layout.css            # 版面配置、側邊欄結構
├── utilities.css         # 工具類別
└── components/
    ├── form-controls.css    # 按鈕 + 表單 + 搜尋
    ├── data-display.css     # 表格 + 卡片 + 統計卡片 + 圖表
    ├── navigation.css       # 側邊欄導航 + 篩選標籤 + 連結
    └── feedback.css         # 警告 + 標籤 + 載入 + 提示
```

**詳細任務**:
- [ ] 1. 建立新的檔案結構（創建 components 資料夾）
- [ ] 2. 拆分 variables.css（從 main.css 提取變數定義）
- [ ] 3. 拆分 base.css（基礎重置 + h1~h6 + a + 捲軸）
- [ ] 4. 拆分 layout.css（gradient-bg, container, main-layout, sidebar 結構）
- [ ] 5. 拆分 utilities.css（spacing, text-align, animations）
- [ ] 6. 拆分 components/form-controls.css（按鈕 + 表單 + 搜尋 + 驗證）
- [ ] 7. 拆分 components/data-display.css（表格 + 卡片 + 統計 + 圖表）
- [ ] 8. 拆分 components/navigation.css（側邊欄導航 + 篩選 + 連結）
- [ ] 9. 拆分 components/feedback.css（警告 + 標籤 + 載入 + 提示）
- [ ] 10. 更新 base.html 的 CSS 引入順序
- [ ] 11. 測試所有頁面確認樣式正常
- [ ] 12. 刪除舊的 main.css 和 components.css
- [ ] 13. 更新 UI_COMPONENTS_AUDIT.md 文件

**預計完成時間**: 2-3 小時

**相關檔案**:
- `src/web/business/detail/static/css/main.css` (待拆分)
- `src/web/business/detail/static/css/components.css` (待拆分)
- `src/web/business/detail/templates/base.html` (需更新引入)
- `src/web/business/detail/UI_COMPONENTS_AUDIT.md` (參考文件)

---

### 🔧 任務 4: 預測頁核心邏輯

**目標**: 實作新電影預測頁的完整互動功能

**詳細任務**:
- [ ] 1. 實作電影搜尋功能
  - [ ] 連接公開 API: `https://boxofficetw.tfai.org.tw/film/sf`
  - [ ] 處理搜尋結果顯示
  - [ ] 處理無結果情況
  - [ ] 自動填入電影基本資訊

- [ ] 2. 表格驗證與操作
  - [ ] 實作新增/刪除週次功能
  - [ ] 驗證必填欄位
  - [ ] 驗證數據格式（整數、範圍）
  - [ ] 確保至少輸入 2 週數據

- [ ] 3. 預測功能
  - [ ] 整合 `M1_predict_new_movie.py`
  - [ ] 呼叫預測 API
  - [ ] 顯示預測結果表格
  - [ ] 顯示票房趨勢圖表
  - [ ] 實作異常警示邏輯

- [ ] 4. 匯出功能
  - [ ] 實作 Excel 匯出
  - [ ] 實作 CSV 匯出

**相關檔案**:
- `src/web/business/detail/static/js/predict.js`
- `src/web/business/detail/templates/predict_new.html`
- `src/ML_boxoffice/M1_predict_new_movie.py`

**預計完成時間**: 4-6 小時

---

### 🔌 任務 5: 後端 API 整合

**目標**: 完整連接後端服務與真實數據源

**詳細任務**:
- [ ] 1. 公開 API 整合
  - [ ] 整合台灣影視聽 API (電影搜尋)
  - [ ] 整合票房數據 API
  - [ ] 錯誤處理與重試機制
  - [ ] API 回應快取機制

- [ ] 2. 預測服務整合
  - [ ] 實作 `/api/predict` 端點
  - [ ] 載入 M1 模型
  - [ ] 處理預測請求
  - [ ] 返回預測結果（JSON）

- [ ] 3. 數據處理
  - [ ] 資料清洗與驗證
  - [ ] 特徵工程處理
  - [ ] 異常值檢測
  - [ ] 結果格式化

- [ ] 4. 資料庫整合（選用）
  - [ ] 儲存預測歷史
  - [ ] 儲存用戶追蹤清單
  - [ ] 快取常用查詢

**相關檔案**:
- `src/web/business/detail/app.py`
- `src/web/business/detail/services/prediction_service.py`
- `src/web/business/detail/services/movie_service.py`
- `src/ML_boxoffice/M1_predict_new_movie.py`

**預計完成時間**: 6-8 小時

---

### 🧪 任務 6: 測試與部署

**目標**: 確保系統穩定運行並準備部署

**詳細任務**:
- [ ] 1. 功能測試
  - [ ] 首頁功能測試（追蹤、篩選）
  - [ ] 電影詳細頁測試（追蹤、收合）
  - [ ] 預測頁完整流程測試
  - [ ] 跨瀏覽器測試

- [ ] 2. RWD 測試
  - [ ] 手機版測試（所有頁面）
  - [ ] 平板版測試
  - [ ] 不同螢幕尺寸測試

- [ ] 3. 效能優化
  - [ ] CSS 壓縮與合併
  - [ ] JavaScript 模組化
  - [ ] 圖片優化
  - [ ] API 回應快取

- [ ] 4. 錯誤處理
  - [ ] API 失敗處理
  - [ ] 網路錯誤處理
  - [ ] 使用者輸入驗證
  - [ ] 錯誤訊息友善化

- [ ] 5. 部署準備
  - [ ] 環境變數設定
  - [ ] 生產環境配置
  - [ ] WSGI 伺服器設定（Gunicorn）
  - [ ] 反向代理設定（Nginx）
  - [ ] SSL 憑證設定

**相關檔案**:
- `src/web/business/detail/app.py`
- `requirements.txt` / `pyproject.toml`
- 部署腳本

**預計完成時間**: 4-6 小時

---

## ✅ 已完成

### 2025-11-13

#### 前端 UI 改善
- ✅ 統一 hover 背景色為 `--hover-bg: rgba(155, 109, 255, 0.11)`
- ✅ 統一按鈕尺寸類別（.btn-size-s → .btn-sm）
- ✅ CSS 變數命名優化（primary-gradient-start/end → brand-primary/secondary）
- ✅ Sidebar 手機版優化（logo 與漢堡按鈕水平對齊，border-radius: 0）
- ✅ Sidebar 手機版 padding 調整（12px 24px）
- ✅ Sidebar 桌面版 copyright 置底

#### 追蹤功能實作
- ✅ 首頁追蹤按鈕功能（localStorage）
- ✅ 電影詳細頁追蹤按鈕功能
- ✅ 篩選標籤功能（所有電影/現正上映/我的追蹤）
- ✅ 電影資訊收合功能

#### 手機版 RWD
- ✅ Sidebar 漢堡選單實作
- ✅ 漢堡動畫（三條線 → X）
- ✅ 選單展開/收合功能

#### 文件整理
- ✅ 建立 UI 元件統整報告（UI_COMPONENTS_AUDIT.md）
- ✅ 分析 117+ 個 UI 元件
- ✅ 識別並修正重複元件問題

---

## 📝 技術筆記

### CSS 變數索引
```css
/* 品牌色 */
--brand-primary: #9C6DFF
--brand-secondary: #71DDFF

/* 互動效果 */
--hover-bg: rgba(155, 109, 255, 0.11)

/* 狀態顏色 */
--success: #51CF66
--warning: #FFA500
--danger-light: #DD6A76
--danger-dark: #36191E
```

### 按鈕系統
- 基底：.btn (height: 42px, radius: 12px)
- 樣式：.btn-primary, .btn-secondary, .btn-danger-dark
- 尺寸：.btn-sm (36px), .btn-lg (全寬)
- 狀態：.btn-disabled

---

## 🐛 已知問題

無

---

## 💡 未來改善方向

1. **後端整合**:
   - 連接真實 API 數據
   - 實作預測邏輯
   - 連接公開票房 API

2. **功能完善**:
   - 實作異常警示邏輯
   - 新增 M2, M3 預測模型
   - 實作匯出功能

3. **效能優化**:
   - CSS 合併壓縮（生產環境）
   - JavaScript 模組化
   - 圖片優化

---

## 📚 相關文件

- [UI 元件審查報告](../src/web/business/detail/UI_COMPONENTS_AUDIT.md)
- [Pipeline 修改指南](shared/pipeline_modification_guide.md)
- [Pipeline 配置說明](shared/pipeline_config_usage.md)
