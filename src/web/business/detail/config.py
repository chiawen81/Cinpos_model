"""
配置文件 - 集中管理應用程式設定
說明: 包含資料路徑、模型路徑、UI設定等配置
"""

import os
from pathlib import Path

# 專案根目錄
BASE_DIR = Path(__file__).resolve().parent

# 資料路徑設定
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "saved_models"
EXPORT_DIR = BASE_DIR / "exports"

# Flask 設定
class Config:
    """Flask應用程式配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # 資料庫設定 (如果需要)
    # DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///movies.db'
    
    # 預測模型設定
    PREDICTION_WEEKS = 3  # 預測未來幾週
    DECLINE_RATE_THRESHOLD = -0.3  # 衰退率預警門檻 (30%)
    
    # UI 色彩設定
    UI_COLORS = {
        'primary_gradient_start': '#9C6DFF',
        'primary_gradient_end': '#71DDFF',
        'background_dark': '#1a1a1a',
        'background_medium': '#2a2a2a',
        'accent': '#DADAFF',
        'text_primary': '#FFFFFF',
        'text_secondary': 'rgba(255, 255, 255, 0.8)',
        'warning': '#FF6B6B',
        'success': '#51CF66',
    }
    
    # 圖表設定
    CHART_CONFIG = {
        'height': 400,
        'responsive': True,
        'dark_theme': True,
    }

# 確保必要目錄存在
for directory in [DATA_DIR, MODEL_DIR, EXPORT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
