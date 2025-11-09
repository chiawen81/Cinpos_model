"""
電影資料模型
說明: 定義電影的基本資料結構和相關方法
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict

@dataclass
class Movie:
    """電影基本資訊"""
    gov_id: str  # 政府代號
    title: str  # 片名
    duration: int  # 片長（分鐘）
    director: str  # 導演
    actors: List[str]  # 演員列表
    country: str  # 發行國家
    release_date: datetime  # 上映日期
    distributor: Optional[str] = None  # 發行商
    rating: Optional[str] = None  # 分級
    genre: Optional[List[str]] = None  # 類型
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            'gov_id': self.gov_id,
            'title': self.title,
            'duration': self.duration,
            'director': self.director,
            'actors': self.actors,
            'country': self.country,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'distributor': self.distributor,
            'rating': self.rating,
            'genre': self.genre
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Movie':
        """從字典創建實例"""
        if isinstance(data.get('release_date'), str):
            data['release_date'] = datetime.fromisoformat(data['release_date'])
        return cls(**data)

@dataclass
class BoxOfficeRecord:
    """票房記錄"""
    gov_id: str
    week: int  # 第幾週
    boxoffice: float  # 票房金額
    audience: int  # 觀影人數
    screens: int  # 廳數
    date: datetime  # 記錄日期
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            'gov_id': self.gov_id,
            'week': self.week,
            'boxoffice': self.boxoffice,
            'audience': self.audience,
            'screens': self.screens,
            'date': self.date.isoformat() if self.date else None
        }

@dataclass 
class BoxOfficePrediction:
    """票房預測結果"""
    gov_id: str
    week: int
    predicted_boxoffice: float
    confidence_lower: float  # 信心區間下界
    confidence_upper: float  # 信心區間上界
    decline_rate: float  # 衰退率
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            'gov_id': self.gov_id,
            'week': self.week,
            'predicted_boxoffice': self.predicted_boxoffice,
            'confidence_lower': self.confidence_lower,
            'confidence_upper': self.confidence_upper,
            'decline_rate': self.decline_rate
        }
    
    def is_declining_fast(self, threshold: float = -0.3) -> bool:
        """檢查是否衰退過快"""
        return self.decline_rate < threshold
