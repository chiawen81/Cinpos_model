"""
測試共用特徵工程模組
"""
import sys
from pathlib import Path

# 加入 ML_boxoffice 路徑
sys.path.append(str(Path(__file__).parent / "src" / "ML_boxoffice"))

from common.feature_engineering import BoxOfficeFeatureEngineer
from datetime import datetime

print("=" * 60)
print("測試共用特徵工程模組")
print("=" * 60)

# === 測試 1: 月份週期性編碼 ===
print("\n【測試 1】月份週期性編碼")
for month in [1, 6, 12]:
    sin_val, cos_val = BoxOfficeFeatureEngineer.encode_month_cyclical(month)
    print(f"  月份 {month:2d}: sin={sin_val:7.4f}, cos={cos_val:7.4f}")

# === 測試 2: 日期解析 ===
print("\n【測試 2】日期解析")
test_dates = [
    "2024-11-13",
    "2024/11/13",
    datetime(2024, 11, 13),
]
for date_input in test_dates:
    parsed = BoxOfficeFeatureEngineer.parse_release_date(date_input)
    print(f"  輸入: {date_input} → 解析: {parsed.strftime('%Y-%m-%d')}")

# === 測試 3: 首週實力計算 ===
print("\n【測試 3】首週實力計算")
week_data = [
    {'week': 1, 'boxoffice': 12000000, 'audience': 40000, 'screens': 150, 'week_range': '2024-11-08~2024-11-14'},
    {'week': 2, 'boxoffice': 10200000, 'audience': 34000, 'screens': 140, 'week_range': '2024-11-15~2024-11-21'},
]
release_date = datetime(2024, 11, 8)

opening_strength = BoxOfficeFeatureEngineer.calculate_opening_strength(week_data, release_date)
for key, value in opening_strength.items():
    print(f"  {key}: {value:,.0f}" if not isinstance(value, float) or value == value else f"  {key}: NaN")

# === 測試 4: Lag Features 計算 ===
print("\n【測試 4】Lag Features 計算")
lag_features = BoxOfficeFeatureEngineer.calculate_lag_features(
    week_data=week_data,
    target_week=3
)
for key, value in lag_features.items():
    print(f"  {key}: {value:,.0f}")

# === 測試 5: 完整特徵建立 ===
print("\n【測試 5】完整特徵建立")
movie_info = {
    'name': '測試電影',
    'release_date': '2024-11-08',
    'film_length': 120,
    'is_restricted': 0,
}

features = BoxOfficeFeatureEngineer.build_prediction_features(
    week_data=week_data,
    movie_info=movie_info,
    target_week=3
)

print(f"\n  生成特徵數量: {len(features)}")
print(f"\n  特徵清單:")
for key, value in features.items():
    if isinstance(value, float):
        print(f"    {key:30s}: {value:12.4f}")
    else:
        print(f"    {key:30s}: {value:12}")

print("\n" + "=" * 60)
print("✅ 所有測試完成！")
print("=" * 60)
