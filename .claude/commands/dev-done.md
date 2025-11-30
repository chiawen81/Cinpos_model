---
description: 開發後檢查 - 提醒更新相關文件和記錄變更
---

# ✅ 開發後文件更新檢查

我已完成開發。請幫我檢查：

## 1. 程式碼變更分析

請分析我剛才的變更，告訴我：
- 修改了哪些功能？
- 新增了哪些內容？
- 是否影響現有規格？

## 2. 必須更新的文件（🔴 Blocking）

根據我的變更，檢查是否需要更新以下文件：

### 資料結構變更
- [ ] 新增/刪除/修改欄位？ → 更新 `docs/model/data_資料欄位定義.md`
- [ ] 修改欄位定義？ → 更新 `docs/model/ml_特徵配置.yaml`

### API 變更
- [ ] 新增/修改/刪除 API？ → 更新 `docs/spec_web_api.md`
- [ ] 修改參數或回應格式？ → 更新 `docs/spec_web_api.md`

### Pipeline 變更
- [ ] 修改 Pipeline 流程？ → 更新 `docs/model/data_資料處理流程.md`
- [ ] 修改處理規則？ → 更新 `docs/model/data_資料處理規則.md`

### 核心功能變更
- [ ] 新增/修改主要功能？ → 更新對應的 `docs/spec_*.md`

## 3. 建議更新的文件（🟡 Recommended）

- [ ] 是否為重要功能？ → 更新 `docs/WORK_LOG.md` 的「近期更新」
- [ ] 是否有重要決策？ → 更新 `docs/WORK_LOG.md` 的「重要決策記錄」
- [ ] 是否為模型優化？ → 更新 `docs/work_log/` 下的相關文件

## 4. 提交前確認

- [ ] 程式碼已完成並測試
- [ ] 相關文件已更新
- [ ] 版本號和日期已更新（如需要）
- [ ] commit message 清楚描述變更

## 5. 建議的 commit message

請根據我的變更，建議一個清楚的 commit message。

---

**請現在告訴我：**
1. 我需要更新哪些文件？
2. 每個文件應該更新什麼內容？
3. 建議的 commit message 是什麼？
