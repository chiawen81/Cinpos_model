"""
預測模型介面
說明: 封裝機器學習模型，提供預測功能
"""

import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys

# 加入特徵工程模組路徑
# Path: models/prediction.py -> models/ -> app/ -> web/ -> src/
src_root = Path(__file__).parent.parent.parent.parent
ml_boxoffice_path = src_root / "ml" / "boxoffice"
sys.path.insert(0, str(src_root))
sys.path.insert(0, str(ml_boxoffice_path))

from ml.boxoffice.common.feature_engineering import BoxOfficeFeatureEngineer
from ..utils.box_office_utils import calculate_decline_rate

class BoxOfficePredictionModel:
    """票房預測模型封裝（使用完整特徵工程）"""

    def __init__(self, model_path: Optional[Path] = None):
        """
        初始化預測模型

        Args:
            model_path: 模型檔案路徑
        """
        self.model = None
        self.feature_columns = None

        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: Path):
        """
        載入預先訓練的線性迴歸模型

        Args:
            model_path: 模型檔案所在目錄
        """
        try:
            # 載入線性迴歸模型（模型是以 tuple 形式儲存：(model, feature_columns)）
            lr_path = model_path / 'model_linear_regression.pkl'
            if lr_path.exists():
                self.model, self.feature_columns = joblib.load(lr_path)
                print(f"[OK] 已載入線性迴歸模型: {lr_path}")
                print(f"[OK] 已載入特徵欄位，共 {len(self.feature_columns)} 個特徵")
            else:
                print(f"[WARNING] 找不到線性迴歸模型: {lr_path}")
                raise FileNotFoundError(f"模型檔案不存在: {lr_path}")

        except Exception as e:
            print(f"[ERROR] 載入模型時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def predict_single_week(self, features: Dict) -> float:
        """
        預測單週票房

        Args:
            features: 特徵字典（由 BoxOfficeFeatureEngineer 產生）

        Returns:
            預測的票房金額
        """
        if self.model is None:
            raise RuntimeError("模型尚未載入")

        # 將特徵字典轉換為 DataFrame
        feature_df = pd.DataFrame([features])

        # 確保特徵順序與模型訓練時一致
        if self.feature_columns:
            feature_df = feature_df[self.feature_columns]

        # 使用線性迴歸預測
        predicted_boxoffice = self.model.predict(feature_df)[0]

        # 確保預測值為正數
        return max(0, predicted_boxoffice)
    
    def predict_multi_week(self, initial_data: Dict, weeks: int = 3) -> List[Dict]:
        """
        預測多週票房（使用完整特徵工程）

        Args:
            initial_data: 初始電影資料（從 movie_service.get_current_week_data 取得）
            weeks: 預測週數

        Returns:
            預測結果列表
        """
        # 將 initial_data 轉換為 week_data 格式（供 BoxOfficeFeatureEngineer 使用）
        week_data = self._convert_to_week_data_format(initial_data)

        # 準備 movie_info（包含所有需要的電影資訊）
        movie_info = {
            'release_date': f"{initial_data.get('release_year', 2025)}-{initial_data.get('release_month', 1):02d}-01",
            'film_length': initial_data.get('film_length', 120),
            'is_restricted': initial_data.get('is_restricted', 0),
            'open_week1_days': initial_data.get('open_week1_days', 7),
            'open_week1_boxoffice': initial_data.get('open_week1_boxoffice', 0),
            'open_week1_boxoffice_daily_avg': initial_data.get('open_week1_boxoffice_daily_avg', 0),
            'open_week2_boxoffice': initial_data.get('open_week2_boxoffice', 0),
        }

        # 預測結果
        predictions = []
        current_week_idx = initial_data.get('current_week', len(week_data))

        for i in range(weeks):
            target_week = current_week_idx + i + 1

            # 使用 BoxOfficeFeatureEngineer 建立特徵
            features = BoxOfficeFeatureEngineer.build_prediction_features(
                week_data=week_data,
                movie_info=movie_info,
                target_week=target_week,
                use_predictions=(i > 0),
                predictions=predictions if i > 0 else None
            )

            # 進行預測
            predicted_boxoffice = self.predict_single_week(features)

            # 計算衰退率
            if len(week_data) > 0:
                prev_boxoffice = week_data[-1].get('boxoffice', predicted_boxoffice)
            else:
                prev_boxoffice = predicted_boxoffice
            decline_rate = calculate_decline_rate(predicted_boxoffice, prev_boxoffice)

            # 估算觀影人次和場次數
            predicted_audience = int(predicted_boxoffice / 300)  # 假設平均票價 300 元
            prev_screens = week_data[-1].get('screens', 100) if week_data else 100
            predicted_screens = max(int(prev_screens * 0.9), 20)  # 院線數衰退 10%

            # 計算信心區間（簡化版本）
            confidence_margin = predicted_boxoffice * 0.15  # 15% 誤差範圍
            confidence_lower = max(0, predicted_boxoffice - confidence_margin)
            confidence_upper = predicted_boxoffice + confidence_margin

            # 儲存預測結果
            prediction = {
                'week': target_week,
                'predicted_boxoffice': predicted_boxoffice,
                'predicted_audience': predicted_audience,
                'predicted_screens': predicted_screens,
                'confidence_lower': confidence_lower,
                'confidence_upper': confidence_upper,
                'decline_rate': decline_rate
            }
            predictions.append(prediction)

            # 將預測結果加入 week_data，供下一輪預測使用
            week_data.append({
                'week': target_week,
                'boxoffice': predicted_boxoffice,
                'audience': predicted_audience,
                'screens': predicted_screens
            })

        return predictions

    def _convert_to_week_data_format(self, initial_data: Dict) -> List[Dict]:
        """
        將 get_current_week_data 的格式轉換為 week_data 格式

        Args:
            initial_data: 從 movie_service.get_current_week_data 取得的資料

        Returns:
            week_data 格式的列表（包含從第1週到當前週的所有資料）
        """
        current_week = initial_data.get('current_week', 2)

        # 構建完整的歷史週次資料（從第1週開始）
        week_data = []

        # 第 1 週（開片週）
        week_data.append({
            'week': 1,
            'boxoffice': initial_data.get('open_week1_boxoffice', 0),
            'audience': 0,  # 如果沒有資料，設為 0
            'screens': 0
        })

        # 第 2 週
        if current_week >= 2:
            week_data.append({
                'week': 2,
                'boxoffice': initial_data.get('open_week2_boxoffice', 0),
                'audience': 0,
                'screens': 0
            })

        # 如果當前週 > 2，需要補充中間週次的資料
        # 但由於 initial_data 只有最近兩週的資料，我們只能使用這些資料
        if current_week > 2:
            # 使用 boxoffice_week_2 作為 current_week - 1 的資料
            week_data.append({
                'week': current_week - 1,
                'boxoffice': initial_data.get('boxoffice_week_2', 0),
                'audience': initial_data.get('audience_week_2', 0),
                'screens': initial_data.get('screens_week_2', 0)
            })

        # 當前週
        week_data.append({
            'week': current_week,
            'boxoffice': initial_data.get('boxoffice_week_1', 0),
            'audience': initial_data.get('audience_week_1', 0),
            'screens': initial_data.get('screens_week_1', 0)
        })

        return week_data

    def predict_multi_week_from_history(
        self,
        week_data: List[Dict],
        movie_info: Dict,
        predict_weeks: int = 3
    ) -> List[Dict]:
        """
        從完整歷史資料預測多週票房（與預測頁使用相同的邏輯）

        Args:
            week_data: 完整的歷史週次資料列表 [{week: 1, boxoffice: xxx, audience: xxx, screens: xxx}, ...]
            movie_info: 電影基本資訊 {release_date, film_length, is_restricted, ...}
            predict_weeks: 預測週數

        Returns:
            預測結果列表
        """
        if len(week_data) < 2:
            raise ValueError("至少需要 2 週的歷史資料")

        # 排序週次資料
        week_data = sorted(week_data, key=lambda x: x['week'])

        # 預測結果
        predictions = []
        current_week_idx = len(week_data)

        for i in range(predict_weeks):
            target_week = current_week_idx + i + 1

            # 使用 BoxOfficeFeatureEngineer 建立特徵
            features = BoxOfficeFeatureEngineer.build_prediction_features(
                week_data=week_data,
                movie_info=movie_info,
                target_week=target_week,
                use_predictions=(i > 0),
                predictions=predictions if i > 0 else None
            )

            # 進行預測
            predicted_boxoffice = self.predict_single_week(features)

            # 計算衰退率
            prev_boxoffice = week_data[-1].get('boxoffice', predicted_boxoffice)
            decline_rate = calculate_decline_rate(predicted_boxoffice, prev_boxoffice)

            # 估算觀影人次和場次數
            predicted_audience = int(predicted_boxoffice / 300)  # 假設平均票價 300 元
            prev_screens = week_data[-1].get('screens', 100)
            predicted_screens = max(int(prev_screens * 0.9), 20)  # 院線數衰退 10%

            # 計算信心區間（簡化版本）
            confidence_margin = predicted_boxoffice * 0.15  # 15% 誤差範圍
            confidence_lower = max(0, predicted_boxoffice - confidence_margin)
            confidence_upper = predicted_boxoffice + confidence_margin

            # 儲存預測結果
            prediction = {
                'week': target_week,
                'predicted_boxoffice': predicted_boxoffice,
                'predicted_audience': predicted_audience,
                'predicted_screens': predicted_screens,
                'confidence_lower': confidence_lower,
                'confidence_upper': confidence_upper,
                'decline_rate': decline_rate
            }
            predictions.append(prediction)

            # 將預測結果加入 week_data，供下一輪預測使用
            week_data.append({
                'week': target_week,
                'boxoffice': predicted_boxoffice,
                'audience': predicted_audience,
                'screens': predicted_screens
            })

        return predictions

class AudiencePredictionModel:
    """觀影人數預測模型"""
    
    def __init__(self, model_path: Optional[Path] = None):
        """初始化觀影人數預測模型"""
        self.model = None
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: Path):
        """載入模型"""
        model_file = model_path / 'audience_model.pkl'
        if model_file.exists():
            with open(model_file, 'rb') as f:
                self.model = pickle.load(f)
    
    def predict(self, boxoffice: float, avg_ticket_price: float = 300) -> int:
        """
        根據票房預測觀影人數
        
        Args:
            boxoffice: 票房金額
            avg_ticket_price: 平均票價
            
        Returns:
            預測的觀影人數
        """
        if self.model:
            # 使用模型預測
            features = pd.DataFrame({'boxoffice': [boxoffice]})
            return int(self.model.predict(features)[0])
        else:
            # 簡單估算
            return int(boxoffice / avg_ticket_price)
