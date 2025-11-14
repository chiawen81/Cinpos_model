"""
M1 新電影預測模組
說明: 提供新電影票房預測功能，可用於 API 或命令列介面
"""

import joblib
import pandas as pd
from pathlib import Path
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys

# 加入共用模組路徑
sys.path.append(str(Path(__file__).parent.parent))
from common.feature_engineering import BoxOfficeFeatureEngineer


class M1NewMoviePredictor:
    """M1 新電影預測器"""

    def __init__(self, model_path: Optional[Path] = None, lazy_load: bool = False):
        """
        初始化預測器

        Args:
            model_path: 模型檔案路徑，若為 None 則使用預設路徑
            lazy_load: 是否延遲載入模型（預設 False）
        """
        if model_path is None:
            # 使用專案根目錄的相對路徑
            project_root = Path(__file__).parent.parent.parent.parent
            model_path = project_root / "data" / "ML_boxoffice" / "phase4_models" / "M1" / "M1_20251110_015910" / "model_linear_regression.pkl"

        self.model_path = model_path
        self.model = None
        self.feature_names = None
        self.model_loaded = False

        # 只有非延遲載入模式才立即載入模型
        if not lazy_load:
            self._load_model()

    def _load_model(self):
        """載入模型"""
        if self.model_loaded:
            return  # 已經載入過了

        try:
            self.model, self.feature_names = joblib.load(self.model_path)
            self.model_loaded = True
            print(f"[OK] 已載入模型: {self.model_path}")
        except Exception as e:
            print(f"[ERROR] 載入模型失敗: {e}")
            raise

    def _ensure_model_loaded(self):
        """確保模型已載入，如果未載入則嘗試載入"""
        if not self.model_loaded:
            self._load_model()

    def predict_single_week(self, movie_data: Dict) -> float:
        """
        預測單一週次的票房

        Args:
            movie_data: 電影資料字典，包含所有必要特徵

        Returns:
            預測的票房金額
        """
        # 確保模型已載入
        self._ensure_model_loaded()

        # 使用共用的特徵工程模組計算 sin/cos 特徵
        if "release_month" in movie_data and "release_month_sin" not in movie_data:
            sin_val, cos_val = BoxOfficeFeatureEngineer.encode_month_cyclical(movie_data["release_month"])
            movie_data["release_month_sin"] = sin_val
            movie_data["release_month_cos"] = cos_val

        # 建立 DataFrame
        X_new = pd.DataFrame([movie_data])

        # 使用模型內建的欄位順序
        X_new = X_new[self.feature_names]

        # 預測
        prediction = self.model.predict(X_new)[0]

        return prediction

    def predict_multi_weeks(self,
                           week_data: List[Dict],
                           movie_info: Dict,
                           predict_weeks: int = 3) -> List[Dict]:
        """
        根據已知週次資料預測未來多週票房

        Args:
            week_data: 已知的週次資料列表 [{week: 1, boxoffice: xxx, audience: xxx, screens: xxx}, ...]
            movie_info: 電影基本資訊 {film_length, is_restricted, release_date, ...}
            predict_weeks: 要預測的週數

        Returns:
            預測結果列表
        """
        # 確保模型已載入
        self._ensure_model_loaded()

        # 檢查輸入資料（對應訓練時的篩選條件）
        if len(week_data) < 2:
            raise ValueError("至少需要 2 週的歷史資料")

        # 排序週次資料
        week_data = sorted(week_data, key=lambda x: x['week'])

        # 驗證前兩週必須有票房（對應訓練時的 boxoffice_week_1 > 0 and boxoffice_week_2 > 0）
        if len(week_data) >= 2:
            if week_data[-1].get('boxoffice', 0) <= 0:
                raise ValueError("最近一週的票房必須大於 0（對應訓練資料的 boxoffice_week_1 > 0 條件）")
            if week_data[-2].get('boxoffice', 0) <= 0:
                raise ValueError("第二近的一週票房必須大於 0（對應訓練資料的 boxoffice_week_2 > 0 條件）")

        # 使用共用模組解析上映日期
        release_date = BoxOfficeFeatureEngineer.parse_release_date(movie_info.get('release_date'))

        # 使用共用模組計算首週實力指標
        opening_strength = BoxOfficeFeatureEngineer.calculate_opening_strength(week_data, release_date)

        # 預測結果
        predictions = []
        current_week_idx = len(week_data)

        for i in range(predict_weeks):
            # 準備特徵資料
            target_week = current_week_idx + i + 1

            # 使用共用模組計算 Lag Features
            lag_features = BoxOfficeFeatureEngineer.calculate_lag_features(
                week_data=week_data,
                target_week=target_week,
                use_predictions=(i > 0),  # 第一次預測不使用，之後使用
                predictions=predictions if i > 0 else None
            )

            # 使用共用模組建立完整特徵字典
            features = BoxOfficeFeatureEngineer.build_prediction_features(
                week_data=week_data,
                movie_info=movie_info,
                target_week=target_week,
                use_predictions=(i > 0),
                predictions=predictions if i > 0 else None
            )

            # 進行預測
            predicted_boxoffice = self.predict_single_week(features)

            # 估算其他數值（觀影人數、院線數）
            predicted_audience = int(predicted_boxoffice / 300)  # 假設平均票價 300 元

            # 取得前一週的院線數
            prev_screens = lag_features.get('screens_week_1', 100)
            predicted_screens = max(int(prev_screens * 0.9), 20)  # 院線數衰退 10%

            # 計算衰退率
            prev_boxoffice = lag_features.get('boxoffice_week_1', 0)
            decline_rate = (predicted_boxoffice - prev_boxoffice) / prev_boxoffice if prev_boxoffice > 0 else 0

            predictions.append({
                'week': target_week,
                'predicted_boxoffice': max(predicted_boxoffice, 0),  # 確保非負
                'predicted_audience': predicted_audience,
                'predicted_screens': predicted_screens,
                'decline_rate': decline_rate
            })

        return predictions



def main():
    """命令列介面"""
    print("=" * 50)
    print("M1 新電影票房預測系統")
    print("=" * 50)

    # 初始化預測器
    predictor = M1NewMoviePredictor()

    # 輸入電影資訊
    print("\n請輸入電影資訊:")
    movie_data = {
        "round_idx": 1,
        "current_week_active_idx": int(input("要預測第幾週: ")),
        "boxoffice_week_1": float(input("上週票房: ")),
        "boxoffice_week_2": float(input("兩週前票房: ")),
        "audience_week_1": float(input("上週觀影人數: ")),
        "audience_week_2": float(input("兩週前觀影人數: ")),
        "screens_week_1": int(input("上週院線數: ")),
        "screens_week_2": int(input("兩週前院線數: ")),
        "open_week1_boxoffice": float(input("首週票房: ")),
        "open_week1_boxoffice_daily_avg": float(input("首週日均票房: ")),
        "film_length": int(input("片長(分鐘): ")),
        "is_restricted": int(input("是否限制級(0/1): ")),
        "gap_real_week_2to1": 0,
        "gap_real_week_1tocurrent": 0,
        "open_week1_days": float(input("首周放映天數: ")),
        "open_week2_boxoffice": float(input("上映第二周的票房: ")),
        "release_year": float(input("上映年份: ")),
        "release_month": float(input("上映月份: ")),
    }

    # 預測
    prediction = predictor.predict_single_week(movie_data)

    print(f"\n=== 預測結果 ===")
    print(f"第 {movie_data['current_week_active_idx']} 週票房: {prediction:,.0f} 元")


if __name__ == "__main__":
    main()
