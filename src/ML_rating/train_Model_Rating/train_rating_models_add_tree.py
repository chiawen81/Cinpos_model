# uv run src\ML_rating\train_Model_Rating\train_rating_models_add_tree.py
# =====================================================
# 🎬 IMDb Rating 四模型訓練 (Linear / LightGBM / DecisionTree / RandomForest)
# 🧠 自動 OneHot + NaN 補值 + 特徵重要性 + 圖表化
# =====================================================
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from io import StringIO
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor, plot_tree
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import lightgbm as lgb
import joblib
import matplotlib.pyplot as plt

# =====================================================
# 📁 輸出資料夾設定
# =====================================================
output_dir = Path("data/ML_rating/4type_rating_models_PART3")
output_dir.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = output_dir / f"training_log_{timestamp}.txt"
log_buffer = StringIO()

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

print("=" * 60)
print(f"🎬 IMDb Rating 四模型訓練開始 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
print("=" * 60)

# =====================================================
# 📄 資料讀取
# =====================================================
feature_path = Path("data/ML_rating/ML_data_PART2/ML_add_extag/merged_full_dataset_full_extag_add_tree_feature.csv")
target_path  = Path("data/ML_rating/ML_data_PART2/ML_add_extag/merged_full_dataset_extag_add_tree_target.csv")
df_X = pd.read_csv(feature_path)
df_y = pd.read_csv(target_path)

# =====================================================
# 🧹 前處理：移除 ID 欄位
# =====================================================
for col in ["gov_id", "movie_id", "id"]:
    if col in df_X.columns:
        df_X = df_X.drop(columns=[col], errors="ignore")
    if col in df_y.columns:
        df_y = df_y.drop(columns=[col], errors="ignore")

# =====================================================
# 🧠 自動編碼文字類特徵
# =====================================================
categorical_cols = df_X.select_dtypes(include=["object"]).columns.tolist()
if categorical_cols:
    print(f"🔠 偵測到文字欄位 {len(categorical_cols)} 個，執行 OneHot 編碼: {categorical_cols}")
    df_X = pd.get_dummies(df_X, columns=categorical_cols, drop_first=True)
else:
    print("✅ 無文字欄位可編碼")

# =====================================================
# 🔍 缺失值處理
# =====================================================
if df_X.isna().sum().sum() > 0:
    print(f"⚠️ 發現 {df_X.isna().sum().sum()} 個 NaN，已自動以 0 補值")
    df_X = df_X.fillna(0)
if df_y.isna().sum().sum() > 0:
    print(f"⚠️ 目標欄有 {df_y.isna().sum().sum()} 個 NaN，已自動以 0 補值")
    df_y = df_y.fillna(0)

# =====================================================
# 🎯 目標變數
# =====================================================
if "imdb_rating" in df_y.columns:
    y = df_y["imdb_rating"]
else:
    y = df_y.iloc[:, 0]
X = df_X.select_dtypes(include=["number"]).fillna(0)

print(f"📊 清理後資料筆數: X={len(X)}, y={len(y)}")
print(f"✅ 特徵欄位數: {X.shape[1]}")

# =====================================================
# 🔀 訓練 / 測試集切分
# =====================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"\n📚 訓練集: {len(X_train)} 筆, 測試集: {len(X_test)} 筆")

# =====================================================
# 🔵 模型 1: 線性回歸
# =====================================================
print("\n" + "=" * 50)
print("🔵 模型 1: Linear Regression")
print("=" * 50)

lr = LinearRegression()
lr.fit(X_train, y_train)
y_pred_lr = lr.predict(X_test)

mae_lr = mean_absolute_error(y_test, y_pred_lr)
rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr))
r2_lr = r2_score(y_test, y_pred_lr)
print(f"MAE:  {mae_lr:.4f}")
print(f"RMSE: {rmse_lr:.4f}")
print(f"R²:   {r2_lr:.4f}")

# =====================================================
# 🟢 模型 2: LightGBM
# =====================================================
print("\n" + "=" * 50)
print("🟢 模型 2: LightGBM")
print("=" * 50)

lgb_model = lgb.LGBMRegressor(
    n_estimators=400,
    learning_rate=0.05,
    max_depth=10,
    random_state=40,
    verbose=-1
)
lgb_model.fit(X_train, y_train)
y_pred_lgb = lgb_model.predict(X_test)

mae_lgb = mean_absolute_error(y_test, y_pred_lgb)
rmse_lgb = np.sqrt(mean_squared_error(y_test, y_pred_lgb))
r2_lgb = r2_score(y_test, y_pred_lgb)
print(f"MAE:  {mae_lgb:.4f}")
print(f"RMSE: {rmse_lgb:.4f}")
print(f"R²:   {r2_lgb:.4f}")

# =====================================================
# 🌳 模型 3: Decision Tree
# =====================================================
# 

print("\n" + "=" * 50)
print("🌳 模型 3: Decision Tree")
print("=" * 50)

tree = DecisionTreeRegressor(max_depth=8, random_state=80)
tree.fit(X_train, y_train)
y_pred_tree = tree.predict(X_test)

mae_tree = mean_absolute_error(y_test, y_pred_tree)
rmse_tree = np.sqrt(mean_squared_error(y_test, y_pred_tree))
r2_tree = r2_score(y_test, y_pred_tree)
print(f"MAE:  {mae_tree:.4f}")
print(f"RMSE: {rmse_tree:.4f}")
print(f"R²:   {r2_tree:.4f}")
# =====================================================
# 🌳 決策樹圖形可視化（含 MSE、RMSE、samples、value）
# =====================================================
import matplotlib.pyplot as plt
from sklearn.tree import plot_tree
import numpy as np

plt.figure(figsize=(30, 26))
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
plt.rcParams["axes.unicode_minus"] = False

# 先取得樹的內部結構
tree_ = tree.tree_

# 建立自訂節點標籤（包含 RMSE）
node_labels = []
for i in range(tree_.node_count):
    mse = tree_.impurity[i]
    rmse = np.sqrt(mse) if mse > 0 else 0.0  # 防止浮點負值
    samples = tree_.n_node_samples[i]
    value = tree_.value[i][0][0]
    node_labels.append(f"MSE={mse:.3f}\nRMSE={rmse:.3f}\nSamples={samples}\nValue={value:.3f}")

# 使用 plot_tree 並手動套上節點標籤
plot_tree(
    tree,
    feature_names=X.columns,
    filled=True,
    rounded=True,
    fontsize=16,
    impurity=False,
    node_ids=True,
)

# 替每個節點加上自訂文字（含 RMSE 等資訊）
ax = plt.gca()
for t in ax.texts:
    node_text = t.get_text().split('\n')[0]
    node_id = None
    if "node" in node_text:
        node_id = int(node_text.replace("node #", "").strip())
    elif node_text.isdigit():
        node_id = int(node_text)
    if node_id is not None and node_id < len(node_labels):
        t.set_text(node_labels[node_id])

plt.title("Decision Tree with MSE / RMSE / Samples / Value", fontsize=14)
plt.tight_layout()
plt.savefig(output_dir / "decision_tree_with_metrics.png", dpi=300)
plt.close()
print(f"✅ 決策樹圖形（含 MSE、RMSE、samples、value）已輸出：{output_dir / 'decision_tree_with_metrics.png'}")

# =====================================================
# 🌲 模型 4: Random Forest
# =====================================================
print("\n" + "=" * 50)
print("🌲 模型 4: Random Forest")
print("=" * 50)

rf = RandomForestRegressor(
    n_estimators=400,
    max_depth=200,
    random_state=35
)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)

mae_rf = mean_absolute_error(y_test, y_pred_rf)
rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf))
r2_rf = r2_score(y_test, y_pred_rf)
print(f"MAE:  {mae_rf:.4f}")
print(f"RMSE: {rmse_rf:.4f}")
print(f"R²:   {r2_rf:.4f}")

# =====================================================
# 📊 特徵重要性輸出
# =====================================================
feature_importance = pd.DataFrame({
    "feature": X.columns,
    "Linear_Coeff": np.abs(lr.coef_),
    "LightGBM_Importance": lgb_model.feature_importances_,
    "Tree_Importance": tree.feature_importances_,
    "RandomForest_Importance": rf.feature_importances_
}).sort_values("LightGBM_Importance", ascending=False)

feature_importance.to_csv(output_dir / "feature_importance_4model.csv", index=False, encoding="utf-8-sig")
print(f"✅ 特徵重要性已存檔: {output_dir / 'feature_importance_4model.csv'}")

# =====================================================
# 📈 可視化：四模型預測比較
# =====================================================
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
models = [
    ("Linear Regression", y_pred_lr, r2_lr),
    ("LightGBM", y_pred_lgb, r2_lgb),
    ("Decision Tree", y_pred_tree, r2_tree),
    ("Random Forest", y_pred_rf, r2_rf)
]

for ax, (name, pred, r2) in zip(axes.flatten(), models):
    ax.scatter(y_test, pred, alpha=0.6, s=20)
    ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--")
    ax.set_title(f"{name} (R²={r2:.3f})")
    ax.set_xlabel("實際 IMDb 評分")
    ax.set_ylabel("預測 IMDb 評分")
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / "rating_prediction_4models.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"✅ 模型預測比較圖已輸出: {output_dir / 'rating_prediction_4models.png'}")

# =====================================================
# 💾 模型保存
# =====================================================
joblib.dump(lr, output_dir / "model_linear.pkl")
joblib.dump(lgb_model, output_dir / "model_lightgbm.pkl")
joblib.dump(tree, output_dir / "model_decision_tree.pkl")
joblib.dump(rf, output_dir / "model_random_forest.pkl")
print(f"✅ 所有模型已保存至: {output_dir}")

# =====================================================
# 🧾 測試集預測結果
# =====================================================
results = pd.DataFrame({
    "actual": y_test,
    "pred_lr": y_pred_lr,
    "pred_lgb": y_pred_lgb,
    "pred_tree": y_pred_tree,
    "pred_rf": y_pred_rf
})
results.to_csv(output_dir / "test_predictions_4models.csv", index=False, encoding="utf-8-sig")
print(f"✅ 測試集預測結果已存檔: {output_dir / 'test_predictions_4models.csv'}")

# =====================================================
# 📘 Log 儲存
# =====================================================
sys.stdout = sys.stdout.terminal
with open(log_file, "w", encoding="utf-8") as f:
    f.write(log_buffer.getvalue())

print("\n" + "=" * 60)
print(f"🎉 模型訓練完成! Log 已保存於: {log_file}")
print("=" * 60)

