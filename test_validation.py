"""
測試資料驗證邏輯
"""
import sys
from pathlib import Path

# 加入 ML_boxoffice 路徑
sys.path.append(str(Path(__file__).parent / "src" / "ML_boxoffice" / "phase5_apply"))

from M1_predict_new_movie import M1NewMoviePredictor

print("=" * 60)
print("[TEST] Data Validation Logic")
print("=" * 60)

predictor = M1NewMoviePredictor()

# 測試案例 1：正常資料（應該成功）
print("\n[Test 1] Valid data with 3 weeks of boxoffice > 0")
week_data_valid = [
    {'week': 1, 'boxoffice': 15000000, 'audience': 50000, 'screens': 160},
    {'week': 2, 'boxoffice': 12000000, 'audience': 40000, 'screens': 150},
    {'week': 3, 'boxoffice': 9500000, 'audience': 32000, 'screens': 140},
]
movie_info = {
    'release_date': '2024-11-01',
    'film_length': 130,
    'is_restricted': 0,
}

try:
    predictions = predictor.predict_multi_weeks(week_data_valid, movie_info, 1)
    print(f"  [PASS] Prediction successful: {predictions[0]['predicted_boxoffice']:,.0f}")
except Exception as e:
    print(f"  [FAIL] {e}")

# 測試案例 2：只有 1 週資料（應該失敗）
print("\n[Test 2] Only 1 week of data (should fail)")
week_data_insufficient = [
    {'week': 1, 'boxoffice': 15000000, 'audience': 50000, 'screens': 160},
]

try:
    predictions = predictor.predict_multi_weeks(week_data_insufficient, movie_info, 1)
    print(f"  [FAIL] Should have raised ValueError but didn't")
except ValueError as e:
    print(f"  [PASS] Correctly raised ValueError: {e}")
except Exception as e:
    print(f"  [FAIL] Unexpected error: {e}")

# 測試案例 3：最後一週票房為 0（應該失敗）
print("\n[Test 3] Last week with zero boxoffice (should fail)")
week_data_zero_last = [
    {'week': 1, 'boxoffice': 15000000, 'audience': 50000, 'screens': 160},
    {'week': 2, 'boxoffice': 0, 'audience': 0, 'screens': 0},
]

try:
    predictions = predictor.predict_multi_weeks(week_data_zero_last, movie_info, 1)
    print(f"  [FAIL] Should have raised ValueError but didn't")
except ValueError as e:
    print(f"  [PASS] Correctly raised ValueError: {e}")
except Exception as e:
    print(f"  [FAIL] Unexpected error: {e}")

# 測試案例 4：第二週票房為 0（應該失敗）
print("\n[Test 4] Second-to-last week with zero boxoffice (should fail)")
week_data_zero_second = [
    {'week': 1, 'boxoffice': 0, 'audience': 0, 'screens': 0},
    {'week': 2, 'boxoffice': 12000000, 'audience': 40000, 'screens': 150},
]

try:
    predictions = predictor.predict_multi_weeks(week_data_zero_second, movie_info, 1)
    print(f"  [FAIL] Should have raised ValueError but didn't")
except ValueError as e:
    print(f"  [PASS] Correctly raised ValueError: {e}")
except Exception as e:
    print(f"  [FAIL] Unexpected error: {e}")

print("\n" + "=" * 60)
print("[COMPLETE] Validation tests finished")
print("=" * 60)
