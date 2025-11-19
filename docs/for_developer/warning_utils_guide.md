# 衰退預警工具使用指南

本文件說明如何使用統一的衰退預警工具函數，避免重複程式碼。

## 概述

為了避免在不同頁面重複實作預警顯示邏輯，我們提供了：
- **後端**：開片實力計算方法（`PredictionService.calculate_opening_strength()`）
- **前端 JavaScript**：預警徽章工具函數（`window.warningUtils`）
- **前端模板**：Jinja2 macro（`warning_badge.html`）

---

## 後端使用

### 開片實力計算

**位置**：`services/prediction_service.py`

**方法**：
```python
@staticmethod
def calculate_opening_strength(
    week_1_boxoffice: float,
    week_2_boxoffice: float,
    week_1_days: int = 7
) -> float:
    """計算開片實力（前兩周日均票房的平均值）"""
    return (week_1_boxoffice / week_1_days + week_2_boxoffice) / 2
```

**使用範例**：
```python
from services.prediction_service import PredictionService

# 靜態方法，可直接呼叫
opening_strength = PredictionService.calculate_opening_strength(
    week_1_boxoffice=12000000,
    week_2_boxoffice=10000000,
    week_1_days=7
)
# 結果：(12000000/7 + 10000000) / 2 ≈ 5857142.86

# 或通過實例呼叫
prediction_service = PredictionService()
opening_strength = prediction_service.calculate_opening_strength(
    week_1_boxoffice,
    week_2_boxoffice
)
```

---

## 前端 JavaScript 使用

### 工具函數

**位置**：`static/js/common/warning-utils.js`

**全域物件**：`window.warningUtils`

### 1. 根據預警物件生成徽章

```javascript
// 預警物件來自 API 回應
const warning = {
    level: '嚴重',
    message: '預測衰退率 -80.0%，比歷史平均快 100%'
};

// 生成徽章 HTML
const badgeHTML = window.warningUtils.getWarningBadge(warning);
// 結果：<span class="badge badge-danger">嚴重</span>

// 加入圖示
const badgeWithIcon = window.warningUtils.getWarningBadge(warning, { showIcon: true });
// 結果：<span class="badge badge-danger">🚨 嚴重</span>
```

### 2. 根據預警等級字串生成徽章

```javascript
const level = '注意';
const badgeHTML = window.warningUtils.getWarningBadgeHTML(level);
// 結果：<span class="badge badge-warning">注意</span>
```

### 3. 取得預警 CSS class

```javascript
const cssClass = window.warningUtils.getWarningBadgeClass('嚴重');
// 結果：'badge-danger'

const cssClass = window.warningUtils.getWarningBadgeClass('正常');
// 結果：'badge-success'
```

### 4. 取得預警顏色

```javascript
const color = window.warningUtils.getWarningColor('注意');
// 結果：'#ffc107' (warning yellow)
```

### 使用範例（predict.js）

**Before（重複邏輯）**：
```javascript
const warning = result.warnings.find(w => w.week === item.week);
let warningBadge = '<span class="badge badge-success">正常</span>';

if (warning) {
    if (warning.level === '嚴重') {
        warningBadge = '<span class="badge badge-danger">嚴重</span>';
    } else if (warning.level === '注意') {
        warningBadge = '<span class="badge badge-warning">注意</span>';
    }
}
```

**After（使用工具函數）**：
```javascript
const warning = result.warnings.find(w => w.week === item.week);
const warningBadge = window.warningUtils.getWarningBadge(warning);
```

---

## 前端模板使用（Jinja2）

### 模板 Macro

**位置**：`templates/macros/warning_badge.html`

### 1. 匯入 Macro

在模板開頭加入：
```jinja2
{% from "macros/warning_badge.html" import warning_badge, warning_alert %}
```

### 2. 顯示預警徽章

```jinja2
{# 根據預警物件顯示徽章 #}
{{ warning_badge(pred.warning) }}

{# 加入圖示 #}
{{ warning_badge(pred.warning, show_icon=true) }}

{# 如果沒有預警物件，會自動顯示「正常」 #}
{{ warning_badge(None) }}
```

### 3. 顯示預警提示框

```jinja2
{# 根據預警等級自動選擇樣式（注意/嚴重） #}
{{ warning_alert(warning) }}

{# 如果是「正常」等級，不會顯示任何內容 #}
```

### 使用範例（movie_detail.html）

**Before（重複邏輯）**：
```jinja2
{% if warning.level == '嚴重' %}
<div class="alert alert-danger">
    <span class="alert-icon">🚨</span>
    <div class="alert-content">
        <div class="alert-title">【嚴重】衰退預警</div>
        <div class="alert-message">{{ warning.message }}</div>
    </div>
</div>
{% elif warning.level == '注意' %}
<div class="alert alert-warning">
    <span class="alert-icon">⚠</span>
    <div class="alert-content">
        <div class="alert-title">【注意】衰退預警</div>
        <div class="alert-message">{{ warning.message }}</div>
    </div>
</div>
{% endif %}
```

**After（使用 Macro）**：
```jinja2
{{ warning_alert(warning) }}
```

---

## 預警等級對應

| 等級 | CSS Class | 顏色 | 用途 |
|------|-----------|------|------|
| 正常 | `badge-success` | 綠色 (#28a745) | 衰退速度正常 |
| 注意 | `badge-warning` | 黃色 (#ffc107) | 衰退比平均快 30-50% |
| 嚴重 | `badge-danger` | 紅色 (#dc3545) | 衰退比平均快 50% 以上 |

---

## 好處

### ✅ 統一邏輯
- 預警徽章顯示邏輯集中管理
- 修改樣式或判斷邏輯只需改一處

### ✅ 避免重複
- 減少程式碼重複
- 降低維護成本

### ✅ 易於測試
- 工具函數可獨立測試
- 確保所有頁面行為一致

### ✅ 易於擴展
- 未來新增預警等級只需修改工具函數
- 所有頁面自動套用新邏輯

---

## 注意事項

1. **API 回應格式**：確保後端回應的 `warning` 物件包含 `level` 欄位
2. **引入順序**：`warning-utils.js` 必須在使用它的頁面腳本之前載入（已在 `base.html` 中全域引入）
3. **模板引入**：使用模板 macro 前必須先 `{% from ... import ... %}`
4. **預警物件可為空**：工具函數會自動處理 `null` 或 `undefined`，預設顯示「正常」

---

## 相關檔案

### 後端
- `src/web/business/detail/services/prediction_service.py` - 開片實力計算
- `src/web/business/detail/services/decline_warning_service.py` - 預警判斷

### 前端 JavaScript
- `src/web/business/detail/static/js/common/warning-utils.js` - 工具函數
- `src/web/business/detail/static/js/pages/predict.js` - 使用範例

### 前端模板
- `src/web/business/detail/templates/macros/warning_badge.html` - Jinja2 macro
- `src/web/business/detail/templates/movie_detail.html` - 使用範例
- `src/web/business/detail/templates/base.html` - 全域載入

### 文件
- `docs/for_developer/project_spec.md` - 衰退預警系統完整規格
- `docs/for_developer/warning_utils_guide.md` - 本文件
