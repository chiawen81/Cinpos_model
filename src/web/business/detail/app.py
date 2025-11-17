"""
Flask 主應用程式
說明: 提供電影票房預測網站的主要應用程式入口
     - 註冊所有 Blueprint
     - 設定模板過濾器
     - 錯誤處理
"""

from flask import Flask, render_template
from flask_cors import CORS
from pathlib import Path

# 自訂模組
from config import Config
from utils.formatters import (
    format_currency, format_number, format_percentage,
    get_decline_color
)

# 初始化 Flask 應用
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# ============= 註冊 Blueprint =============
from blueprints import web_bp, prediction_api_bp, movie_api_bp

app.register_blueprint(web_bp)
app.register_blueprint(prediction_api_bp)
app.register_blueprint(movie_api_bp)


# ============= 自訂過濾器 =============
@app.template_filter('format_currency')
def format_currency_filter(value):
    """格式化貨幣的模板過濾器"""
    return format_currency(value)


@app.template_filter('format_number')
def format_number_filter(value):
    """格式化數字的模板過濾器"""
    return format_number(value)


@app.template_filter('format_percentage')
def format_percentage_filter(value):
    """格式化百分比的模板過濾器"""
    return format_percentage(value)


@app.template_filter('decline_color')
def decline_color_filter(value):
    """根據衰退率返回顏色的模板過濾器"""
    return get_decline_color(value)

# ============= 錯誤處理 =============
@app.errorhandler(404)
def page_not_found(e):
    """404 錯誤處理"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """500 錯誤處理"""
    return render_template('500.html'), 500

# ============= 主程式入口 =============
if __name__ == '__main__':
    # 確保必要目錄存在
    Path('data').mkdir(exist_ok=True)
    Path('saved_models').mkdir(exist_ok=True)
    Path('exports').mkdir(exist_ok=True)

    # 啟動應用
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )