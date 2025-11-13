"""
測試預測功能整合
"""
import sys
from pathlib import Path

# 加入 ML_boxoffice 路徑
sys.path.append(str(Path(__file__).parent / "src" / "ML_boxoffice" / "phase5_apply"))

from M1_predict_new_movie import M1NewMoviePredictor

print("=" * 60)
print("[TEST] M1 New Movie Predictor Integration")
print("=" * 60)

# 準備測試資料
week_data = [
    {'week': 1, 'boxoffice': 15000000, 'audience': 50000, 'screens': 160},
    {'week': 2, 'boxoffice': 12000000, 'audience': 40000, 'screens': 150},
    {'week': 3, 'boxoffice': 9500000, 'audience': 32000, 'screens': 140},
]

movie_info = {
    'name': 'Test Movie',
    'release_date': '2024-11-01',
    'film_length': 130,
    'is_restricted': 0,
}

print("\n[INFO] Testing with sample data:")
print(f"  Movie: {movie_info['name']}")
print(f"  Release Date: {movie_info['release_date']}")
print(f"  Historical Weeks: {len(week_data)}")

try:
    # 初始化預測器
    print("\n[1/3] Initializing predictor...")
    predictor = M1NewMoviePredictor()
    print("  [OK] Predictor initialized successfully")

    # 進行預測
    print("\n[2/3] Predicting next 3 weeks...")
    predictions = predictor.predict_multi_weeks(
        week_data=week_data,
        movie_info=movie_info,
        predict_weeks=3
    )
    print(f"  [OK] Generated {len(predictions)} predictions")

    # 顯示結果
    print("\n[3/3] Prediction Results:")
    print("  " + "-" * 56)
    print(f"  {'Week':<6} {'Boxoffice':>15} {'Audience':>12} {'Screens':>8} {'Decline':>10}")
    print("  " + "-" * 56)

    for pred in predictions:
        week = pred['week']
        boxoffice = pred['predicted_boxoffice']
        audience = pred['predicted_audience']
        screens = pred['predicted_screens']
        decline = pred['decline_rate']

        print(f"  {week:<6} {boxoffice:>15,.0f} {audience:>12,} {screens:>8} {decline:>9.1%}")

    print("  " + "-" * 56)

    print("\n" + "=" * 60)
    print("[SUCCESS] All tests passed!")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("[FAILED] Test encountered errors")
    print("=" * 60)
