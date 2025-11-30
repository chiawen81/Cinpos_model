---
description: 文件使用指南 - 快速了解如何使用文件系統
---

# 📖 文件使用指南

## 快速參考

### 文件分類

```
docs/
├── 📌 入口文件（從這裡開始）
│   ├── spec_model.md          → 模型系統
│   ├── spec_web.md            → 網站系統
│   ├── spec_web_api.md        → API 規格
│   └── WORK_LOG.md            → 工作日誌
│
├── 📁 model/ （模型技術文件）
│   ├── data_資料欄位定義.md             ← 欄位定義
│   ├── data_資料處理規則.md       ← 處理規則
│   ├── data_資料處理流程.md                    ← Pipeline 流程
│   ├── data_資料過濾工具.md            ← 工具使用
│   └── ml_模型優化路線圖.md        ← 優化方案
│
├── 📁 web/ （網站技術文件）
├── 📁 shared/ （共用文件）
└── 📁 work_log/ （工作日誌）
```

### 常用命令

- `/dev-start` - 開發前檢查
- `/dev-done` - 開發後檢查
- `/docs-find` - 快速查找文件
- `/docs-update` - 檢查需要更新的文件

### 維護工作

**必須更新（🔴）**：
- 新增/修改欄位 → data_資料欄位定義.md + ml_特徵配置.yaml
- 修改處理規則 → data_資料處理規則.md
- 新增/修改 API → spec_web_api.md
- 修改 Pipeline → data_資料處理流程.md

**建議更新（🟡）**：
- 完成重要功能 → WORK_LOG.md
- 優化實驗 → work_log/WORK_LOG_票房預測模型優化流程.md
- 進度變更 → work_log/WORK_LOG_模型優化進度.md

## 詳細指南

完整的使用指南請查看：
- `docs/如何使用文件系統.md`

---

**需要幫助？**

告訴我你想要：
1. 查找什麼文件？
2. 了解什麼資訊？
3. 更新什麼內容？

我會提供具體的指引！
