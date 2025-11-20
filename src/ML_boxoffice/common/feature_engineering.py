"""
特徵工程共用模組
說明: 提供訓練和預測階段共用的特徵計算邏輯，確保一致性
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class BoxOfficeFeatureEngineer:
    """票房特徵工程器 - 提供訓練和預測階段共用的特徵計算方法"""

    @staticmethod
    def encode_month_cyclical(month: int) -> Tuple[float, float]:
        """
        月份週期性編碼（sin/cos）

        Args:
            month: 月份 (1-12)

        Returns:
            (sin_value, cos_value)
        """
        sin_value = np.sin(2 * np.pi * month / 12)
        cos_value = np.cos(2 * np.pi * month / 12)
        return sin_value, cos_value

    @staticmethod
    def parse_release_date(release_date) -> datetime:
        """
        解析上映日期

        Args:
            release_date: 可能是 datetime、字串或其他格式

        Returns:
            datetime 物件
        """
        if isinstance(release_date, datetime):
            return release_date
        elif isinstance(release_date, str):
            # 嘗試多種日期格式
            for fmt in ["%Y-%m-%d", "%Y/%m/%d"]:
                try:
                    return datetime.strptime(release_date, fmt)
                except ValueError:
                    continue
            # 如果都失敗，使用當前日期
            print(f"⚠️ 無法解析日期 '{release_date}'，使用當前日期")
            return datetime.now()
        else:
            return datetime.now()

    @staticmethod
    def calculate_opening_strength(
        week_data: List[Dict],
        release_date: datetime
    ) -> Dict[str, float]:
        """
        計算首週實力指標

        Args:
            week_data: 週次資料列表 [{week: 1, boxoffice: xxx, audience: xxx, screens: xxx, week_range: xxx}, ...]
            release_date: 上映日期

        Returns:
            包含首週實力指標的字典：
            - open_week1_boxoffice: 首週票房
            - open_week1_days: 首週放映天數
            - open_week1_boxoffice_daily_avg: 首週日均票房
            - open_week2_boxoffice: 第二週票房
        """
        if len(week_data) == 0:
            return {
                'open_week1_boxoffice': np.nan,
                'open_week1_days': np.nan,
                'open_week1_boxoffice_daily_avg': np.nan,
                'open_week2_boxoffice': np.nan,
            }

        # 排序確保順序正確
        sorted_weeks = sorted(week_data, key=lambda x: x.get('week', 0))

        # 首週資料
        first_week = sorted_weeks[0]
        open_week1_boxoffice = first_week.get('boxoffice', 0)

        # 計算首週放映天數
        open_week1_days = 7  # 預設值
        if 'week_range' in first_week and first_week['week_range']:
            try:
                # 解析週次區間 "YYYY-MM-DD~YYYY-MM-DD"
                week_end_str = first_week['week_range'].split('~')[1].strip()
                week_end = datetime.strptime(week_end_str, "%Y-%m-%d")
                open_week1_days = (week_end - release_date).days + 1
                # 確保天數為正數（最小為 1 天）
                if open_week1_days < 1:
                    print(f"⚠️ 計算首週天數為 {open_week1_days}，使用預設值 7 天")
                    open_week1_days = 7
            except Exception as e:
                print(f"⚠️ 無法計算首週天數: {e}，使用預設值 7 天")

        # 首週日均票房
        open_week1_boxoffice_daily_avg = open_week1_boxoffice / open_week1_days if open_week1_days > 0 else 0

        # 第二週票房
        open_week2_boxoffice = sorted_weeks[1].get('boxoffice', 0) if len(sorted_weeks) >= 2 else np.nan

        return {
            'open_week1_boxoffice': open_week1_boxoffice,
            'open_week1_days': open_week1_days,
            'open_week1_boxoffice_daily_avg': open_week1_boxoffice_daily_avg,
            'open_week2_boxoffice': open_week2_boxoffice,
        }

    @staticmethod
    def calculate_lag_features(
        week_data: List[Dict],
        target_week: int,
        use_predictions: bool = False,
        predictions: Optional[List[Dict]] = None
    ) -> Dict[str, float]:
        """
        計算 Lag Features（前1週、前2週的票房/觀眾/院線數）

        Args:
            week_data: 實際週次資料列表
            target_week: 目標週次（要預測的週次）
            use_predictions: 是否使用預測資料（用於多步預測）
            predictions: 之前的預測結果列表

        Returns:
            包含 lag features 的字典：
            - boxoffice_week_1, boxoffice_week_2
            - audience_week_1, audience_week_2
            - screens_week_1, screens_week_2
        """
        # 排序並合併資料
        all_data = sorted(week_data, key=lambda x: x.get('week', 0))

        if use_predictions and predictions:
            # 將預測資料轉換為相同格式
            pred_data = [
                {
                    'week': p.get('week'),
                    'boxoffice': p.get('predicted_boxoffice', p.get('boxoffice', 0)),
                    'audience': p.get('predicted_audience', p.get('audience', 0)),
                    'screens': p.get('predicted_screens', p.get('screens', 0)),
                }
                for p in predictions
            ]
            all_data.extend(pred_data)
            all_data = sorted(all_data, key=lambda x: x.get('week', 0))

        # 找到前1週和前2週的資料
        week_1_data = None
        week_2_data = None

        for i, data in enumerate(all_data):
            if data.get('week') == target_week - 1:
                week_1_data = data
            if data.get('week') == target_week - 2:
                week_2_data = data

        # 如果找不到，嘗試用最近的兩週資料
        if week_1_data is None or week_2_data is None:
            # 找出小於 target_week 的所有週次
            previous_weeks = [d for d in all_data if d.get('week', 0) < target_week]
            if len(previous_weeks) >= 1:
                week_1_data = previous_weeks[-1]  # 最近一週
            if len(previous_weeks) >= 2:
                week_2_data = previous_weeks[-2]  # 第二近的一週

        # 提取特徵
        def get_value(data, key, default=0):
            if data is None:
                return default
            value = data.get(key, default)
            # 處理 None 值（避免 NaN 傳入模型）
            if value is None:
                if key == 'audience':
                    return data.get('boxoffice', 0) / 300  # 假設平均票價 300 元
                elif key == 'screens':
                    return 100  # 預設院線數
                else:
                    return default
            # 如果是 audience 或 screens 為 0，用票房估算
            if key == 'audience' and value == 0:
                return data.get('boxoffice', 0) / 300  # 假設平均票價 300 元
            if key == 'screens' and value == 0:
                return 100  # 預設院線數
            return value

        return {
            'boxoffice_week_1': get_value(week_1_data, 'boxoffice', 0),
            'boxoffice_week_2': get_value(week_2_data, 'boxoffice', 0),
            'audience_week_1': get_value(week_1_data, 'audience', 0),
            'audience_week_2': get_value(week_2_data, 'audience', 0),
            'screens_week_1': get_value(week_1_data, 'screens', 100),
            'screens_week_2': get_value(week_2_data, 'screens', 100),
        }

    @staticmethod
    def calculate_gap_features(
        week_data: List[Dict],
        target_week: int
    ) -> Dict[str, int]:
        """
        計算跳週數（基於活躍週次）

        Args:
            week_data: 週次資料列表
            target_week: 目標週次

        Returns:
            包含跳週數的字典：
            - gap_real_week_2to1: 前2週到前1週之間跳過的週數
            - gap_real_week_1tocurrent: 前1週到當前週之間跳過的週數
        """
        # 排序並只保留有票房的週次
        active_weeks = sorted(
            [w for w in week_data if w.get('boxoffice', 0) > 0],
            key=lambda x: x.get('week', 0)
        )

        # 預設值
        gap_2to1 = 0
        gap_1tocurrent = 0

        # 找出前1週和前2週（活躍週次）
        if len(active_weeks) >= 1:
            week_1 = active_weeks[-1].get('week', 0)
            gap_1tocurrent = target_week - week_1 - 1

        if len(active_weeks) >= 2:
            week_1 = active_weeks[-1].get('week', 0)
            week_2 = active_weeks[-2].get('week', 0)
            gap_2to1 = week_1 - week_2 - 1

        return {
            'gap_real_week_2to1': max(0, gap_2to1),
            'gap_real_week_1tocurrent': max(0, gap_1tocurrent),
        }

    @classmethod
    def build_prediction_features(
        cls,
        week_data: List[Dict],
        movie_info: Dict,
        target_week: int,
        use_predictions: bool = False,
        predictions: Optional[List[Dict]] = None
    ) -> Dict[str, float]:
        """
        建立模型預測所需的完整特徵字典

        Args:
            week_data: 已知的週次資料列表
            movie_info: 電影基本資訊 {name, release_date, film_length, is_restricted, ...}
            target_week: 要預測的週次
            use_predictions: 是否使用之前的預測結果
            predictions: 之前的預測結果列表

        Returns:
            包含所有特徵的字典
        """
        # 解析上映日期
        release_date = cls.parse_release_date(movie_info.get('release_date'))
        release_year = release_date.year
        release_month = release_date.month

        # 月份週期性編碼
        month_sin, month_cos = cls.encode_month_cyclical(release_month)

        # 計算首週實力指標
        opening_strength = cls.calculate_opening_strength(week_data, release_date)

        # 計算 Lag Features
        lag_features = cls.calculate_lag_features(
            week_data, target_week, use_predictions, predictions
        )

        # 計算跳週數
        gap_features = cls.calculate_gap_features(week_data, target_week)

        # 組合所有特徵
        features = {
            # 輪次與週次
            "round_idx": 1,  # 新電影預測固定為第1輪
            "current_week_active_idx": target_week,

            # Lag Features
            **lag_features,

            # 首週實力
            **opening_strength,

            # 電影基本資訊
            "film_length": movie_info.get('film_length', 120),
            "is_restricted": movie_info.get('is_restricted', 0),

            # 跳週數
            **gap_features,

            # 時間特徵
            "release_year": release_year,
            "release_month": release_month,
            "release_month_sin": month_sin,
            "release_month_cos": month_cos,
        }

        return features

    @classmethod
    def add_features_to_dataframe(
        cls,
        df: pd.DataFrame,
        group_by_col: str = 'gov_id'
    ) -> pd.DataFrame:
        """
        為訓練資料集批量添加特徵（用於訓練階段）

        Args:
            df: 包含基礎資料的 DataFrame
            group_by_col: 分組欄位（通常是 gov_id）

        Returns:
            添加特徵後的 DataFrame

        Note:
            這個方法用於訓練階段，輸入的 df 應該已經經過 flatten_timeseries.py 處理
            本方法主要用於添加月份編碼等額外特徵
        """
        df = df.copy()

        # 添加月份週期性編碼
        if 'release_month' in df.columns:
            df['release_month_sin'] = df['release_month'].apply(
                lambda m: cls.encode_month_cyclical(m)[0]
            )
            df['release_month_cos'] = df['release_month'].apply(
                lambda m: cls.encode_month_cyclical(m)[1]
            )

        return df


# ===================================================================
# 向後相容：提供獨立函數介面
# ===================================================================

def encode_month_cyclical(month: int) -> Tuple[float, float]:
    """月份週期性編碼 - 向後相容的函數介面"""
    return BoxOfficeFeatureEngineer.encode_month_cyclical(month)


def parse_release_date(release_date) -> datetime:
    """解析上映日期 - 向後相容的函數介面"""
    return BoxOfficeFeatureEngineer.parse_release_date(release_date)


def calculate_opening_strength(week_data: List[Dict], release_date: datetime) -> Dict[str, float]:
    """計算首週實力指標 - 向後相容的函數介面"""
    return BoxOfficeFeatureEngineer.calculate_opening_strength(week_data, release_date)


def calculate_lag_features(
    week_data: List[Dict],
    target_week: int,
    use_predictions: bool = False,
    predictions: Optional[List[Dict]] = None
) -> Dict[str, float]:
    """計算 Lag Features - 向後相容的函數介面"""
    return BoxOfficeFeatureEngineer.calculate_lag_features(
        week_data, target_week, use_predictions, predictions
    )


def build_prediction_features(
    week_data: List[Dict],
    movie_info: Dict,
    target_week: int,
    use_predictions: bool = False,
    predictions: Optional[List[Dict]] = None
) -> Dict[str, float]:
    """建立完整特徵字典 - 向後相容的函數介面"""
    return BoxOfficeFeatureEngineer.build_prediction_features(
        week_data, movie_info, target_week, use_predictions, predictions
    )
