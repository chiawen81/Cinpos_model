# uv run src\ML_rating\train_Model_Rating\train_rating_models_addlog.py
# =====================================================
# 🎬 IMDb Rating 雙模型訓練 (LightGBM + RandomForest)
# Version: v2 - 加強 Log、特徵重要性視覺化
# =====================================================
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from io import StringIO
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import lightgbm as lgb
import matplotlib.pyplot as plt
import joblib

# =====================================================
# 📁 輸出資料夾設定
# =====================================================
output_dir = Path("data/ML_rating/2type_rating_models_v2")
output_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = output_dir / f"training_log_{timestamp}.txt"
log_buffer = StringIO()

# =====================================================
# 🧾 Log 系統設定
# =====================================================
class Logger:
    def __init__(self, log_buffer):
        self.terminal = sys.stdout
        self.log = log_buffer
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        self.terminal.flush()

sys.stdout = Logger(log_buffer)

def log_model_result(model_name, mae, rmse, r2):
    print(f"\n[{model_name}] 評估結果")
    print(f"  MAE : {mae:.4f}")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  R²  : {r2:.4f}")

def log_top_features(model_name, feature_importances, feature_names, top_n=10):
    print(f"\n🔍 {model_name} 前 {top_n} 重要特徵：")
    top_features = sorted(
        zip(feature_names, feature_importances), key=lambda x: x[1], reverse=True
    )[:top_n]
    for i, (feat, imp) in enumerate(top_features, 1):
        print(f"{i:>2}. {feat:<35} {imp:.3f}")

# =====================================================
# 📄 資料讀取
# =====================================================
feature_path = Path("data/ML_rating/ML_data_PART2/ML_add_extag/merged_full_dataset_full_extag_add_tree_feature.csv")
target_path  = Path("data/ML_rating/ML_data_PART2/ML_add_extag/merged_full_dataset_extag_add_tree_target.csv")

print("=" * 60)
print(f"🎬 IMDb Rating 雙模型訓練開始 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
print("=" * 60)
print(f"📥 載入資料：\nFeature: {feature_path}\nTarget : {target_path}")

X = pd.read_csv(feature_path)
y = pd.read_csv(target_path)

if "gov_id" in X.columns: X = X.drop(columns=["gov_id"])
if "gov_id" in y.columns: y = y.drop(columns=["gov_id"])

# OneHot 編碼文字欄位
cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
if len(cat_cols) > 0:
    print(f"🔠 偵測到文字欄位 {len(cat_cols)} 個，執行 OneHot 編碼: {cat_cols}")
    X = pd.get_dummies(X, columns=cat_cols, drop_first=True)

# 填補缺失值
if X.isna().sum().sum() > 0:
    print(f"⚠️ X 有缺失值，已以 0 填補")
    X = X.fillna(0)
if y.isna().sum().sum() > 0:
    print(f"⚠️ y 有缺失值，已以 0 填補")
    y = y.fillna(0)

print(f"✅ 清理後資料: X={len(X)}, y={len(y)}, 特徵數={X.shape[1]}")

# =====================================================
# 🔀 分割訓練/測試集
# =====================================================
y = y.iloc[:, 0]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"📚 訓練集: {len(X_train)} 筆, 測試集: {len(X_test)} 筆")

# =====================================================
# 🟢 模型 1: LightGBM
# =====================================================
print("\n" + "=" * 50)
print("🟢 模型 1: LightGBM")
print("=" * 50)

lgb_model = lgb.LGBMRegressor(
    n_estimators=400, learning_rate=0.05, max_depth=6,
    random_state=42, verbose=-1
)
lgb_model.fit(X_train, y_train)
y_pred_lgb = lgb_model.predict(X_test)

mae_lgb = mean_absolute_error(y_test, y_pred_lgb)
rmse_lgb = np.sqrt(mean_squared_error(y_test, y_pred_lgb))
r2_lgb = r2_score(y_test, y_pred_lgb)
log_model_result("LightGBM", mae_lgb, rmse_lgb, r2_lgb)
log_top_features("LightGBM", lgb_model.feature_importances_, X.columns)

# =====================================================
# 🌲 模型 2: Random Forest
# =====================================================
print("\n" + "=" * 50)
print("🌲 模型 2: Random Forest")
print("=" * 50)

rf = RandomForestRegressor(
    n_estimators=400, max_depth=20,
    min_samples_leaf=2, random_state=80, n_jobs=-1
)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)

mae_rf = mean_absolute_error(y_test, y_pred_rf)
rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf))
r2_rf = r2_score(y_test, y_pred_rf)
log_model_result("RandomForest", mae_rf, rmse_rf, r2_rf)
log_top_features("RandomForest", rf.feature_importances_, X.columns)

# =====================================================
# 📊 特徵重要性輸出
# =====================================================
feature_importance = pd.DataFrame({
    "feature": X.columns,
    "LightGBM_Importance": lgb_model.feature_importances_,
    "RandomForest_Importance": rf.feature_importances_
}).sort_values("LightGBM_Importance", ascending=False)

feature_importance.to_csv(output_dir / "feature_importance_2models.csv", index=False, encoding="utf-8-sig")

top_features = feature_importance.head(15)
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.figure(figsize=(10,6))
plt.barh(top_features["feature"], top_features["LightGBM_Importance"], color='orange')
plt.gca().invert_yaxis()
plt.title("LightGBM 最重要的 15 個特徵")
plt.xlabel("Feature Importance")
plt.tight_layout()
plt.savefig(output_dir / "feature_importance_top15.png", dpi=150)
plt.close()

# =====================================================
# 📈 預測比較圖
# =====================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
models = [("LightGBM", y_pred_lgb, r2_lgb), ("RandomForest", y_pred_rf, r2_rf)]
for ax, (name, pred, r2) in zip(axes, models):
    ax.scatter(y_test, pred, alpha=0.6, s=20)
    ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--")
    ax.set_title(f"{name} (R²={r2:.3f})")
    ax.set_xlabel("實際 IMDb 評分")
    ax.set_ylabel("預測 IMDb 評分")
    ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(output_dir / "rating_prediction_2models.png", dpi=150)
plt.close()

# =====================================================
# 💾 模型保存與測試輸出
# =====================================================
joblib.dump(lgb_model, output_dir / "model_lightgbm.pkl")
joblib.dump(rf, output_dir / "model_randomforest.pkl")
results = pd.DataFrame({
    "actual": y_test,
    "pred_lightgbm": y_pred_lgb,
    "pred_randomforest": y_pred_rf
})
results.to_csv(output_dir / "test_predictions_2models.csv", index=False, encoding="utf-8-sig")

# =====================================================
# 📘 訓練結果摘要
# =====================================================
print("\n" + "=" * 60)
print("📘 模型訓練摘要")
print("=" * 60)
print(f"LightGBM → R²={r2_lgb:.4f}, RMSE={rmse_lgb:.4f}")
print(f"RandomForest → R²={r2_rf:.4f}, RMSE={rmse_rf:.4f}")
print(f"\n📂 模型輸出資料夾: {output_dir}")
print(f"🧾 Log 檔案: {log_file.name}")
print(f"📊 特徵重要性: feature_importance_2models.csv")
print(f"📈 圖像輸出: rating_prediction_2models.png")
print(f"📊 Top15 特徵圖: feature_importance_top15.png")
print(f"📑 測試結果: test_predictions_2models.csv")
print("=" * 60)

# =====================================================
# 🧾 Log 輸出
# =====================================================
sys.stdout = sys.stdout.terminal
with open(log_file, "w", encoding="utf-8") as f:
    f.write(log_buffer.getvalue())
print(f"🎉 模型訓練完成！Log 已保存至: {log_file}")