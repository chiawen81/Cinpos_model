import sys
from pathlib import Path

# 將 src 目錄加入 Python 路徑，以便能夠 import common 模組
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

from common.file_utils import ensure_dir
from common.path_utils import PHASE3_PREPARE_DIR, PHASE4_MODELS_DIR
from ML_boxoffice.common.feature_engineering import BoxOfficeFeatureEngineer

# ===================================================================
# 全域設定
# ===================================================================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_model_dir = Path(PHASE4_MODELS_DIR) / "M1" / f"M1_compare_{timestamp}"
ensure_dir(output_model_dir)

# 使用的訓練資料集
input_data_path = Path(PHASE3_PREPARE_DIR) / "M1_train_dataset" / "features_market_2025-11-07.csv"

print("=" * 70)
print(f"[TEST] 特徵刪減方案比較測試")
print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ===================================================================
# 資料預處理
# ===================================================================
print("\n[DATA] 讀取資料...")
df = pd.read_csv(input_data_path)

# 排除指定的電影
exclude_config_path = "config/exclude_movies.csv"
try:
    exclude_df = pd.read_csv(exclude_config_path, comment="#")
    exclude_gov_ids = exclude_df["gov_id"].dropna().astype(int).tolist()
    if len(exclude_gov_ids) > 0:
        print(f"排除 {len(exclude_gov_ids)} 部電影")
        df = df[~df["gov_id"].isin(exclude_gov_ids)].copy()
except:
    pass

# 篩選資料
df = df[df["round_idx"] == 1].copy()
df = df[df["current_week_active_idx"].notna()]
df = df[
    (df["boxoffice_week_1"].notna())
    & (df["boxoffice_week_1"] > 0)
    & (df["boxoffice_week_2"].notna())
    & (df["boxoffice_week_2"] > 0)
]

print(f"資料筆數: {len(df)}")

# 月份週期性編碼
df = BoxOfficeFeatureEngineer.add_features_to_dataframe(df, group_by_col='gov_id')

# 刪除基本不需要的欄位
drop_columns = [
    "tickets",
    "theater_count",
    "official_release_date",
    "week_range",
    "current_week_real_idx",
    "boxoffice_cumsum",
    "boxoffice_round1_cumsum",
    "boxoffice_current_round_cumsum",
    "audience_cumsum",
    "audience_round1_cumsum",
    "audience_current_round_cumsum",
    "rounds_cumsum",
    "ticket_price_avg_current",
    "region",
    "publisher",
    "release_month",
]
df = df.drop(columns=drop_columns)

# ===================================================================
# 定義三個測試方案
# ===================================================================
scenarios = {
    "基準線 (Baseline)": {
        "drop": [],
        "description": "保留所有特徵作為基準比較"
    },
    "方案 A (使用者建議)": {
        "drop": ["audience_week_1", "audience_week_2", "open_week1_days", "screens_week_2"],
        "description": "刪除觀眾數、開片天數、第2週院線數"
    },
    "方案 B (AI 建議)": {
        "drop": ["audience_week_1", "audience_week_2", "open_week1_boxoffice_daily_avg", "screens_week_2"],
        "description": "刪除觀眾數、日均票房、第2週院線數"
    },
    "方案 C (激進方案)": {
        "drop": ["audience_week_1", "audience_week_2", "open_week1_days",
                "open_week1_boxoffice_daily_avg", "screens_week_2"],
        "description": "同時刪除天數和日均票房"
    },
}

# ===================================================================
# 測試每個方案
# ===================================================================
results = []

for scenario_name, config in scenarios.items():
    print("\n" + "=" * 70)
    print(f"[SCENARIO] 測試方案: {scenario_name}")
    print(f"說明: {config['description']}")
    print("=" * 70)

    # 準備資料
    df_test = df.copy()

    # 刪除指定的特徵
    if config['drop']:
        print(f"\n刪除特徵: {config['drop']}")
        df_test = df_test.drop(columns=config['drop'], errors='ignore')

    # 分離特徵與目標
    X = df_test.drop(columns=["amount"])
    y = df_test["amount"]

    print(f"\n特徵數量: {X.shape[1] - 1} (不含 gov_id)")

    # 切分資料集
    splitter = GroupShuffleSplit(test_size=0.2, n_splits=1, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups=X["gov_id"]))

    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    # 移除 gov_id
    X_train_model = X_train.drop(columns=["gov_id"])
    X_test_model = X_test.drop(columns=["gov_id"])

    # 訓練線性回歸模型
    lr_model = LinearRegression()
    lr_model.fit(X_train_model, y_train)
    y_pred = lr_model.predict(X_test_model)

    # 計算評估指標
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mape = mae / y_test.mean() * 100

    # 計算高相關特徵對數量
    correlation_matrix = X_train_model.corr()
    high_corr_count = 0
    for i in range(len(correlation_matrix.columns)):
        for j in range(i + 1, len(correlation_matrix.columns)):
            if abs(correlation_matrix.iloc[i, j]) > 0.8:
                high_corr_count += 1

    # 顯示結果
    print(f"\n[RESULT] 評估結果:")
    print(f"  MAE:  {mae:,.0f} 元")
    print(f"  RMSE: {rmse:,.0f} 元")
    print(f"  R2:   {r2:.4f}")
    print(f"  MAPE: {mape:.2f}%")
    print(f"  高相關特徵對 (|r|>0.8): {high_corr_count} 對")

    # 儲存結果
    results.append({
        "方案": scenario_name,
        "特徵數": X_train_model.shape[1],
        "MAE": mae,
        "RMSE": rmse,
        "R²": r2,
        "MAPE": mape,
        "高相關對數": high_corr_count,
        "刪除特徵": ", ".join(config['drop']) if config['drop'] else "無",
    })

# ===================================================================
# 生成比較報告
# ===================================================================
print("\n" + "=" * 70)
print("[REPORT] 完整比較報告")
print("=" * 70)

results_df = pd.DataFrame(results)
print("\n" + results_df.to_string(index=False))

# 儲存報告
results_df.to_csv(output_model_dir / "comparison_report.csv", index=False, encoding="utf-8-sig")
print(f"\n[SAVED] 報告已儲存: {output_model_dir / 'comparison_report.csv'}")

# ===================================================================
# 視覺化比較
# ===================================================================
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# MAE 比較
ax1 = axes[0, 0]
bars1 = ax1.bar(range(len(results_df)), results_df["MAE"], color=['gray', 'steelblue', 'coral', 'mediumpurple'])
ax1.set_xticks(range(len(results_df)))
ax1.set_xticklabels(results_df["方案"], rotation=15, ha='right')
ax1.set_ylabel("MAE (元)")
ax1.set_title("MAE 比較 (越低越好)")
ax1.grid(axis='y', alpha=0.3)
for i, v in enumerate(results_df["MAE"]):
    ax1.text(i, v, f'{v:,.0f}', ha='center', va='bottom', fontsize=9)

# RMSE 比較
ax2 = axes[0, 1]
bars2 = ax2.bar(range(len(results_df)), results_df["RMSE"], color=['gray', 'steelblue', 'coral', 'mediumpurple'])
ax2.set_xticks(range(len(results_df)))
ax2.set_xticklabels(results_df["方案"], rotation=15, ha='right')
ax2.set_ylabel("RMSE (元)")
ax2.set_title("RMSE 比較 (越低越好)")
ax2.grid(axis='y', alpha=0.3)
for i, v in enumerate(results_df["RMSE"]):
    ax2.text(i, v, f'{v:,.0f}', ha='center', va='bottom', fontsize=9)

# R² 比較
ax3 = axes[1, 0]
bars3 = ax3.bar(range(len(results_df)), results_df["R²"], color=['gray', 'steelblue', 'coral', 'mediumpurple'])
ax3.set_xticks(range(len(results_df)))
ax3.set_xticklabels(results_df["方案"], rotation=15, ha='right')
ax3.set_ylabel("R²")
ax3.set_title("R² 比較 (越高越好)")
ax3.axhline(y=0.9, color='red', linestyle='--', linewidth=1, label='目標門檻 (0.9)')
ax3.grid(axis='y', alpha=0.3)
ax3.legend()
for i, v in enumerate(results_df["R²"]):
    ax3.text(i, v, f'{v:.4f}', ha='center', va='bottom', fontsize=9)

# 高相關對數比較
ax4 = axes[1, 1]
bars4 = ax4.bar(range(len(results_df)), results_df["高相關對數"], color=['gray', 'steelblue', 'coral', 'mediumpurple'])
ax4.set_xticks(range(len(results_df)))
ax4.set_xticklabels(results_df["方案"], rotation=15, ha='right')
ax4.set_ylabel("高相關特徵對數量")
ax4.set_title("共線性比較 (越低越好)")
ax4.grid(axis='y', alpha=0.3)
for i, v in enumerate(results_df["高相關對數"]):
    ax4.text(i, v, f'{int(v)}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig(output_model_dir / "comparison_charts.png", dpi=150, bbox_inches="tight")
print(f"[SAVED] 視覺化圖表已儲存: {output_model_dir / 'comparison_charts.png'}")

# ===================================================================
# 找出最佳方案
# ===================================================================
print("\n" + "=" * 70)
print("[BEST] 最佳方案推薦")
print("=" * 70)

# 過濾 R² >= 0.9 的方案
valid_results = results_df[results_df["R²"] >= 0.9].copy()

if len(valid_results) > 0:
    # 找出 MAE 最低的方案
    best_mae = valid_results.loc[valid_results["MAE"].idxmin()]
    print(f"\n[WINNER-MAE] MAE 最低 (R2 >= 0.9): {best_mae['方案']}")
    print(f"   MAE:  {best_mae['MAE']:,.0f} 元")
    print(f"   RMSE: {best_mae['RMSE']:,.0f} 元")
    print(f"   R2:   {best_mae['R²']:.4f}")
    print(f"   MAPE: {best_mae['MAPE']:.2f}%")

    # 找出 RMSE 最低的方案
    best_rmse = valid_results.loc[valid_results["RMSE"].idxmin()]
    print(f"\n[WINNER-RMSE] RMSE 最低 (R2 >= 0.9): {best_rmse['方案']}")
    print(f"   MAE:  {best_rmse['MAE']:,.0f} 元")
    print(f"   RMSE: {best_rmse['RMSE']:,.0f} 元")
    print(f"   R2:   {best_rmse['R²']:.4f}")

    # 找出共線性最低的方案
    best_corr = valid_results.loc[valid_results["高相關對數"].idxmin()]
    print(f"\n[WINNER-CORR] 共線性最低 (R2 >= 0.9): {best_corr['方案']}")
    print(f"   高相關對數: {int(best_corr['高相關對數'])}")
    print(f"   MAE:  {best_corr['MAE']:,.0f} 元")
    print(f"   R2:   {best_corr['R²']:.4f}")
else:
    print("\n[WARNING] 沒有方案達到 R2 >= 0.9 的目標")

print("\n" + "=" * 70)
print(f"[DONE] 測試完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
