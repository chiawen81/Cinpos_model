"""
預測模型介面
說明: 封裝機器學習模型，提供預測功能
"""

import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import lightgbm as lgb
from sklearn.linear_model import LinearRegression
from utils.box_office_utils import calculate_decline_rate

class BoxOfficePredictionModel:
    """票房預測模型封裝"""
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        初始化預測模型
        
        Args:
            model_path: 模型檔案路徑
        """
        self.lr_model = None
        self.lgb_model = None
        self.feature_columns = None
        
        if model_path:
            self.load_models(model_path)
    
    def load_models(self, model_path: Path):
        """
        載入預先訓練的模型

        Args:
            model_path: 模型檔案所在目錄
        """
        try:
            # 載入線性迴歸模型（模型是以 tuple 形式儲存：(model, feature_columns)）
            lr_path = model_path / 'model_linear_regression.pkl'
            if lr_path.exists():
                lr_model, lr_features = joblib.load(lr_path)
                self.lr_model = lr_model
                # 第一次載入時設定特徵欄位
                if self.feature_columns is None:
                    self.feature_columns = lr_features
                print(f"[OK] 已載入線性迴歸模型: {lr_path}")
            else:
                print(f"[WARNING] 找不到線性迴歸模型: {lr_path}")

            # 載入 LightGBM 模型（模型是以 tuple 形式儲存：(model, feature_columns)）
            lgb_path = model_path / 'model_lightgbm.pkl'
            if lgb_path.exists():
                lgb_model, lgb_features = joblib.load(lgb_path)
                self.lgb_model = lgb_model
                # 第一次載入時設定特徵欄位
                if self.feature_columns is None:
                    self.feature_columns = lgb_features
                print(f"[OK] 已載入 LightGBM 模型: {lgb_path}")
            else:
                print(f"[WARNING] 找不到 LightGBM 模型: {lgb_path}")

            if self.feature_columns:
                print(f"[OK] 已載入特徵欄位，共 {len(self.feature_columns)} 個特徵")

        except Exception as e:
            print(f"[ERROR] 載入模型時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def prepare_features(self, movie_data: Dict) -> pd.DataFrame:
        """
        準備預測所需的特徵

        Args:
            movie_data: 包含電影資訊的字典

        Returns:
            準備好的特徵 DataFrame（按照模型期望的欄位順序）
        """
        # 按照模型訓練時的欄位順序準備特徵
        features = {
            # 1. round_idx - 輪次索引（預設為1）
            'round_idx': movie_data.get('round_idx', 1),

            # 2. current_week_active_idx - 當前週次
            'current_week_active_idx': movie_data.get('current_week', 3),

            # 3. gap_real_week_2to1 - week_2 到 week_1 的週數間隔（通常為1）
            'gap_real_week_2to1': movie_data.get('gap_real_week_2to1', 1),

            # 4. gap_real_week_1tocurrent - week_1 到當前週的週數間隔（通常為1）
            'gap_real_week_1tocurrent': movie_data.get('gap_real_week_1tocurrent', 1),

            # 5-10. 票房、觀影人數、廳數資料
            'boxoffice_week_2': movie_data.get('boxoffice_week_2', 0),
            'boxoffice_week_1': movie_data.get('boxoffice_week_1', 0),
            'audience_week_2': movie_data.get('audience_week_2', 0),
            'audience_week_1': movie_data.get('audience_week_1', 0),
            'screens_week_2': movie_data.get('screens_week_2', 0),
            'screens_week_1': movie_data.get('screens_week_1', 0),

            # 11-14. 開片資訊
            'open_week1_days': movie_data.get('open_week1_days', 7),
            'open_week1_boxoffice': movie_data.get('open_week1_boxoffice', 0),
            'open_week1_boxoffice_daily_avg': movie_data.get('open_week1_boxoffice_daily_avg', 0),
            'open_week2_boxoffice': movie_data.get('open_week2_boxoffice', 0),

            # 15-17. 電影屬性
            'release_year': movie_data.get('release_year', 2025),
            'film_length': movie_data.get('film_length', 120),
            'is_restricted': movie_data.get('is_restricted', 0),
        }

        # 18-19. 加入月份的 sin/cos 編碼
        release_month = movie_data.get('release_month', 1)
        features['release_month_sin'] = np.sin(2 * np.pi * release_month / 12)
        features['release_month_cos'] = np.cos(2 * np.pi * release_month / 12)

        # 建立 DataFrame（確保欄位順序與模型訓練時一致）
        if self.feature_columns:
            # 使用模型載入時的特徵欄位順序
            return pd.DataFrame([features])[self.feature_columns]
        else:
            # 如果沒有載入模型，使用預設順序
            return pd.DataFrame([features])
    
    def predict_single_week(self, features: pd.DataFrame) -> Tuple[float, float, float]:
        """
        預測單週票房
        
        Args:
            features: 特徵 DataFrame
            
        Returns:
            (預測值, 信心區間下界, 信心區間上界)
        """
        if self.lr_model is None and self.lgb_model is None:
            # 如果沒有載入模型，返回模擬數據
            base_value = features['boxoffice_week_1'].values[0] * 0.7
            return base_value, base_value * 0.8, base_value * 1.2
        
        predictions = []
        
        # 使用線性迴歸預測
        if self.lr_model:
            lr_pred = self.lr_model.predict(features)[0]
            predictions.append(lr_pred)
        
        # 使用 LightGBM 預測
        if self.lgb_model:
            lgb_pred = self.lgb_model.predict(features)[0]
            predictions.append(lgb_pred)
        
        # 加權平均（根據之前的討論，LR權重較高）
        if len(predictions) == 2:
            final_pred = 0.7 * predictions[0] + 0.3 * predictions[1]
        else:
            final_pred = predictions[0] if predictions else 0
        
        # 計算信心區間（簡化版本）
        confidence_margin = final_pred * 0.15  # 15% 誤差範圍
        lower_bound = max(0, final_pred - confidence_margin)
        upper_bound = final_pred + confidence_margin
        
        return final_pred, lower_bound, upper_bound
    
    def predict_multi_week(self, initial_data: Dict, weeks: int = 3) -> List[Dict]:
        """
        預測多週票房
        
        Args:
            initial_data: 初始電影資料
            weeks: 預測週數
            
        Returns:
            預測結果列表
        """
        predictions = []
        current_data = initial_data.copy()
        
        for week_ahead in range(1, weeks + 1):
            # 準備特徵
            features = self.prepare_features(current_data)
            
            # 預測
            pred_value, lower, upper = self.predict_single_week(features)

            # 計算衰退率（使用共用工具函數）
            prev_boxoffice = current_data.get('boxoffice_week_1', pred_value)
            decline_rate = calculate_decline_rate(pred_value, prev_boxoffice)
            
            # 儲存預測結果
            predictions.append({
                'week': current_data.get('current_week', 2) + week_ahead,
                'predicted_boxoffice': pred_value,
                'confidence_lower': lower,
                'confidence_upper': upper,
                'decline_rate': decline_rate
            })
            
            # 更新資料供下一週預測使用
            current_data['boxoffice_week_2'] = current_data.get('boxoffice_week_1', 0)
            current_data['boxoffice_week_1'] = pred_value
            current_data['current_week'] = current_data.get('current_week', 2) + 1
            
            # 更新其他特徵（簡化處理）
            current_data['audience_week_2'] = current_data.get('audience_week_1', 0)
            current_data['audience_week_1'] = int(pred_value / 300)  # 假設平均票價300元
            
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
