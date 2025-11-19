"""
衰退率統計服務
用於計算歷史訓練資料的衰退率統計，提供分位數基準
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional
import json


class DeclineStatistics:
    """衰退率統計類別"""

    def __init__(self, training_data_path: Optional[Path] = None):
        """
        初始化衰退率統計服務

        Args:
            training_data_path: 訓練資料路徑（preprocessed_full.csv）
        """
        self.training_data_path = training_data_path
        self.statistics = None
        self.cache_file = Path(__file__).parent / "decline_statistics_cache.json"

        # 嘗試載入快取
        if self.cache_file.exists():
            self._load_cache()

    def calculate_statistics(self, force_recalculate: bool = False) -> Dict:
        """
        計算或載入衰退率統計資料

        Args:
            force_recalculate: 是否強制重新計算

        Returns:
            統計資料字典
        """
        if self.statistics is not None and not force_recalculate:
            return self.statistics

        if not force_recalculate and self.cache_file.exists():
            self._load_cache()
            return self.statistics

        # 需要重新計算
        if self.training_data_path is None or not self.training_data_path.exists():
            # 使用預設路徑（最新的訓練資料）
            self.training_data_path = self._find_latest_training_data()

        if self.training_data_path is None:
            raise FileNotFoundError("找不到訓練資料檔案")

        # 讀取訓練資料
        df = pd.read_csv(self.training_data_path)

        # 計算統計資料
        self.statistics = self._compute_statistics(df)

        # 儲存快取
        self._save_cache()

        return self.statistics

    def _compute_statistics(self, df: pd.DataFrame) -> Dict:
        """
        計算衰退率統計資料

        計算邏輯：
        1. 計算前兩周日均票房（作為電影量級的指標）
        2. 計算分位數（P25, P75, P90）
        3. 為每部電影分配量級
        4. 計算每個量級在每一週的平均衰退率

        Args:
            df: 訓練資料 DataFrame

        Returns:
            統計資料字典
        """
        # 1. 計算前兩周日均票房
        df['opening_strength'] = (
            df['open_week1_boxoffice_daily_avg'] + df['open_week2_boxoffice']
        ) / 2

        # 2. 計算分位數（根據每部電影的首次記錄）
        first_records = df.groupby('gov_id').first().reset_index()
        percentiles = {
            'P25': first_records['opening_strength'].quantile(0.25),
            'P75': first_records['opening_strength'].quantile(0.75),
            'P90': first_records['opening_strength'].quantile(0.90),
        }

        # 3. 為每一筆資料分配量級
        def assign_tier(strength):
            if strength < percentiles['P25']:
                return 'tier_1'  # < P25
            elif strength < percentiles['P75']:
                return 'tier_2'  # P25-P75
            elif strength < percentiles['P90']:
                return 'tier_3'  # P75-P90
            else:
                return 'tier_4'  # > P90

        df['tier'] = df['opening_strength'].apply(assign_tier)

        # 4. 計算每一週的衰退率
        # 衰退率 = (當週票房 - 上週票房) / 上週票房
        df['decline_rate'] = (df['amount'] - df['boxoffice_week_1']) / df['boxoffice_week_1']

        # 5. 計算每個量級在每一週的平均衰退率
        tier_statistics = {}

        for tier in ['tier_1', 'tier_2', 'tier_3', 'tier_4']:
            tier_data = df[df['tier'] == tier]

            # 按週次統計
            week_stats = {}
            for week in sorted(tier_data['current_week_active_idx'].unique()):
                week_data = tier_data[tier_data['current_week_active_idx'] == week]

                if len(week_data) > 0:
                    week_stats[int(week)] = {
                        'mean_decline_rate': float(week_data['decline_rate'].mean()),
                        'median_decline_rate': float(week_data['decline_rate'].median()),
                        'std_decline_rate': float(week_data['decline_rate'].std()),
                        'count': int(len(week_data)),
                    }

            tier_statistics[tier] = week_stats

        # 組合結果
        statistics = {
            'percentiles': {k: float(v) for k, v in percentiles.items()},
            'tier_statistics': tier_statistics,
            'total_movies': int(df['gov_id'].nunique()),
            'total_records': int(len(df)),
        }

        return statistics

    def _find_latest_training_data(self) -> Optional[Path]:
        """
        尋找最新的訓練資料檔案

        Returns:
            訓練資料路徑，如果找不到則返回 None
        """
        # 從當前檔案位置往上找到專案根目錄
        current_file = Path(__file__)
        # 往上 6 層：services -> detail -> business -> web -> src -> project_root
        project_root = current_file.parent.parent.parent.parent.parent.parent

        # 尋找最新的 M1 模型資料
        data_dir = project_root / "data" / "ML_boxoffice" / "phase4_models" / "M1"

        if not data_dir.exists():
            return None

        # 尋找所有 prepared_data 目錄下的 preprocessed_full.csv
        csv_files = list(data_dir.glob("*/prepared_data/preprocessed_full.csv"))

        if not csv_files:
            return None

        # 按修改時間排序，取最新的
        csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return csv_files[0]

    def _save_cache(self):
        """儲存快取到檔案"""
        if self.statistics is None:
            return

        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.statistics, f, ensure_ascii=False, indent=2)

    def _load_cache(self):
        """從檔案載入快取"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                self.statistics = json.load(f)
        except Exception:
            self.statistics = None

    def get_tier_for_strength(self, opening_strength: float) -> str:
        """
        根據開片實力判斷量級

        Args:
            opening_strength: 前兩周日均票房

        Returns:
            量級代號 (tier_1, tier_2, tier_3, tier_4)
        """
        if self.statistics is None:
            self.calculate_statistics()

        percentiles = self.statistics['percentiles']

        if opening_strength < percentiles['P25']:
            return 'tier_1'
        elif opening_strength < percentiles['P75']:
            return 'tier_2'
        elif opening_strength < percentiles['P90']:
            return 'tier_3'
        else:
            return 'tier_4'

    def get_average_decline_rate(self, tier: str, week: int) -> Optional[float]:
        """
        取得特定量級和週次的平均衰退率

        Args:
            tier: 量級代號
            week: 週次

        Returns:
            平均衰退率，如果沒有資料則返回 None
        """
        if self.statistics is None:
            self.calculate_statistics()

        tier_stats = self.statistics['tier_statistics'].get(tier, {})
        week_stats = tier_stats.get(str(week), None)

        if week_stats is None:
            return None

        return week_stats['mean_decline_rate']


# 單例模式，避免重複計算
_instance = None


def get_decline_statistics() -> DeclineStatistics:
    """
    取得衰退率統計服務單例

    Returns:
        DeclineStatistics 實例
    """
    global _instance
    if _instance is None:
        _instance = DeclineStatistics()
    return _instance
