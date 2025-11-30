"""
資料模型模組
"""

from .movie import Movie, BoxOfficeRecord, BoxOfficePrediction
from .prediction import BoxOfficePredictionModel, AudiencePredictionModel

__all__ = [
    'Movie',
    'BoxOfficeRecord', 
    'BoxOfficePrediction',
    'BoxOfficePredictionModel',
    'AudiencePredictionModel'
]
