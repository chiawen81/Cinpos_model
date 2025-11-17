"""
Blueprint 模組
整合所有路由 Blueprint
"""

from .web_routes import web_bp
from .prediction_api import prediction_api_bp
from .movie_api import movie_api_bp

__all__ = ['web_bp', 'prediction_api_bp', 'movie_api_bp']
