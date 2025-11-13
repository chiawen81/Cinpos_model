"""
電影資料服務
說明: 處理電影資料的商業邏輯
"""

import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
from models.movie import Movie, BoxOfficeRecord

class MovieService:
    """電影資料服務類別"""
    
    def __init__(self, data_path: Optional[Path] = None):
        """
        初始化電影服務
        
        Args:
            data_path: 資料檔案路徑
        """
        self.data_path = data_path
        self.movies_cache = {}
        self.boxoffice_cache = {}
        
        if data_path:
            self.load_data()
    
    def load_data(self):
        """載入電影資料"""
        # 這裡應該從實際資料來源載入
        # 目前使用模擬資料
        pass
    
    def get_movie_by_id(self, gov_id: str) -> Optional[Movie]:
        """
        根據政府代號取得電影資訊
        
        Args:
            gov_id: 政府代號
            
        Returns:
            電影物件或 None
        """
        # 檢查快取
        if gov_id in self.movies_cache:
            return self.movies_cache[gov_id]
        
        # 模擬資料（實際應從資料庫或檔案讀取）
        sample_movies = {
            "MOV001": Movie(
                gov_id="MOV001",
                title="科技風暴",
                duration=148,
                director="張導演",
                actors=["李演員", "王演員", "陳演員"],
                country="台灣",
                release_date=datetime(2025, 10, 1),
                distributor="華納兄弟",
                rating="保護級",
                genre=["科幻", "動作"]
            ),
            "MOV002": Movie(
                gov_id="MOV002",
                title="愛在深秋",
                duration=112,
                director="林導演",
                actors=["黃演員", "周演員"],
                country="台灣",
                release_date=datetime(2025, 9, 15),
                distributor="威視電影",
                rating="普遍級",
                genre=["愛情", "劇情"]
            )
        }
        
        movie = sample_movies.get(gov_id)
        if movie:
            self.movies_cache[gov_id] = movie
        
        return movie
    
    def get_boxoffice_history(self, gov_id: str) -> List[BoxOfficeRecord]:
        """
        取得電影歷史票房記錄
        
        Args:
            gov_id: 政府代號
            
        Returns:
            票房記錄列表
        """
        # 檢查快取
        if gov_id in self.boxoffice_cache:
            return self.boxoffice_cache[gov_id]
        
        # 模擬歷史票房資料
        history = []
        base_boxoffice = 50000000  # 首週5000萬
        base_audience = 166667  # 約16.7萬人次
        
        for week in range(1, 9):  # 8週歷史資料
            # 模擬票房衰退
            decay_factor = 0.7 ** (week - 1)
            
            record = BoxOfficeRecord(
                gov_id=gov_id,
                week=week,
                boxoffice=base_boxoffice * decay_factor,
                audience=int(base_audience * decay_factor),
                screens=max(100 - week * 10, 20),  # 廳數遞減
                date=datetime(2025, 10, 1) + timedelta(weeks=week-1)
            )
            history.append(record)
        
        self.boxoffice_cache[gov_id] = history
        return history
    
    def get_current_week_data(self, gov_id: str) -> Dict:
        """
        取得當前週資料（供預測使用）
        
        Args:
            gov_id: 政府代號
            
        Returns:
            包含當前週相關資料的字典
        """
        history = self.get_boxoffice_history(gov_id)
        movie = self.get_movie_by_id(gov_id)
        
        if not history or len(history) < 2:
            return {}
        
        # 取最近兩週的資料
        latest_week = history[-1]
        previous_week = history[-2] if len(history) >= 2 else history[-1]
        
        # 計算開片資訊
        open_week1 = history[0] if history else None
        open_week2 = history[1] if len(history) > 1 else None
        
        return {
            'gov_id': gov_id,
            'current_week': latest_week.week,
            'boxoffice_week_1': latest_week.boxoffice,
            'boxoffice_week_2': previous_week.boxoffice,
            'audience_week_1': latest_week.audience,
            'audience_week_2': previous_week.audience,
            'screens_week_1': latest_week.screens,
            'screens_week_2': previous_week.screens,
            'open_week1_boxoffice': open_week1.boxoffice if open_week1 else 0,
            'open_week1_boxoffice_daily_avg': (open_week1.boxoffice / 7) if open_week1 else 0,
            'open_week2_boxoffice': open_week2.boxoffice if open_week2 else 0,
            'film_length': movie.duration if movie else 120,
            'release_year': movie.release_date.year if movie else 2025,
            'release_month': movie.release_date.month if movie else 1,
            'is_restricted': 1 if movie and movie.rating == "限制級" else 0
        }
    
    def calculate_statistics(self, gov_id: str) -> Dict:
        """
        計算統計資訊

        Args:
            gov_id: 政府代號

        Returns:
            統計資訊字典
        """
        history = self.get_boxoffice_history(gov_id)

        if not history:
            return {}

        # 計算總票房
        total_boxoffice = sum(r.boxoffice for r in history)
        total_audience = sum(r.audience for r in history)

        # 計算平均衰退率
        decline_rates = []
        for i in range(1, len(history)):
            if history[i-1].boxoffice > 0:
                rate = (history[i].boxoffice - history[i-1].boxoffice) / history[i-1].boxoffice
                decline_rates.append(rate)

        avg_decline_rate = sum(decline_rates) / len(decline_rates) if decline_rates else 0

        # 找出最高票房週
        peak_week = max(history, key=lambda r: r.boxoffice)

        # 計算本週衰退率（最新一週的衰退率）====待調整====
        current_decline_rate = 0
        audience_decline_rate = 0
        screens_decline_rate = 0

        if len(history) >= 2:
            latest = history[-1]
            previous = history[-2]

            if previous.boxoffice > 0:
                current_decline_rate = (latest.boxoffice - previous.boxoffice) / previous.boxoffice

            if previous.audience > 0:
                audience_decline_rate = (latest.audience - previous.audience) / previous.audience

            if previous.screens > 0:
                screens_decline_rate = (latest.screens - previous.screens) / previous.screens

        return {
            'total_boxoffice': total_boxoffice,
            'total_audience': total_audience,
            'avg_decline_rate': avg_decline_rate,
            'peak_week': peak_week.week,
            'peak_boxoffice': peak_week.boxoffice,
            'weeks_released': len(history),
            # 新增欄位
            'cross_round_total_boxoffice': total_boxoffice * 1.25,  # 模擬跨輪累計（當輪 * 1.25）
            'cross_round_total_audience': int(total_audience * 1.25),  # 模擬跨輪累計
            'current_decline_rate': current_decline_rate,
            'audience_decline_rate': audience_decline_rate,
            'screens_decline_rate': screens_decline_rate
        }
