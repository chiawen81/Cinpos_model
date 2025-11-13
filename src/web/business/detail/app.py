"""
Flask 主應用程式
說明: 提供電影票房預測網站的主要路由和API端點
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime
import io

# 自訂模組
from config import Config
from services.movie_service import MovieService
from services.prediction_service import PredictionService
from utils.formatters import (
    format_currency, format_number, format_percentage, 
    format_date, get_decline_color
)
from utils.validators import validate_gov_id, validate_export_format

# 初始化 Flask 應用
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# 初始化服務
movie_service = MovieService()
prediction_service = PredictionService()

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

# ============= 頁面路由 =============
@app.route('/')
def index():
    """首頁 - 總覽儀表板"""
    return render_template('index.html')

@app.route('/movies')
def movies_list():
    """電影列表頁面"""
    # 這裡應該從資料庫取得電影列表
    # 目前使用模擬資料
    movies = [
        {'gov_id': 'MOV001', 'title': '科技風暴', 'release_date': '2025-10-01'},
        {'gov_id': 'MOV002', 'title': '愛在深秋', 'release_date': '2025-09-15'},
    ]
    return render_template('movies_list.html', movies=movies)

@app.route('/movie/<gov_id>')
def movie_detail(gov_id):
    """
    單部電影詳細頁面
    
    Args:
        gov_id: 政府代號
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # 取得電影資料
    movie = movie_service.get_movie_by_id(gov_id)
    if not movie:
        return render_template('404.html', message='電影不存在'), 404
    
    # 取得歷史票房資料
    history = movie_service.get_boxoffice_history(gov_id)
    
    # 取得預測資料
    predictions = prediction_service.predict_movie_boxoffice(gov_id, weeks=3)
    
    # 取得統計資料
    statistics = movie_service.calculate_statistics(gov_id)
    
    # 取得預警資訊
    warning = prediction_service.check_decline_warning(gov_id)
    
    # 準備圖表資料
    chart_data = {
        'history': [record.to_dict() for record in history],
        'predictions': [pred.to_dict() for pred in predictions]
    }
    
    # 準備衰退率圖表資料
    decline_data = prepare_decline_chart_data(history)
    
    return render_template('movie_detail.html',
                         movie=movie,
                         history=history,
                         predictions=predictions,
                         statistics=statistics,
                         warning=warning,
                         chart_data=chart_data,
                         decline_data=decline_data)

@app.route('/predictions')
def predictions():
    """預測分析頁面"""
    return render_template('predictions.html')

@app.route('/predict-new')
def predict_new():
    """新電影預測頁面"""
    return render_template('predict_new.html')

@app.route('/reports')
def reports():
    """報表中心頁面"""
    return render_template('reports.html')

# ============= API 路由 =============
@app.route('/api/movie/<gov_id>')
def api_movie_detail(gov_id):
    """
    API: 取得電影詳細資料
    
    Args:
        gov_id: 政府代號
        
    Returns:
        JSON 格式的電影資料
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # 取得完整資料
    data = prediction_service.generate_combined_data(gov_id)
    
    return jsonify(data)

@app.route('/api/movie/<gov_id>/predict')
def api_predict(gov_id):
    """
    API: 預測電影票房
    
    Args:
        gov_id: 政府代號
        
    Query Parameters:
        weeks: 預測週數（預設3週）
        
    Returns:
        JSON 格式的預測結果
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # 取得預測週數參數
    weeks = request.args.get('weeks', 3, type=int)
    weeks = min(max(weeks, 1), 12)  # 限制在1-12週之間
    
    # 進行預測
    predictions = prediction_service.predict_movie_boxoffice(gov_id, weeks)
    
    # 轉換為 JSON 格式
    result = {
        'gov_id': gov_id,
        'weeks': weeks,
        'predictions': [pred.to_dict() for pred in predictions]
    }
    
    return jsonify(result)

@app.route('/api/movie/<gov_id>/latest')
def api_latest_data(gov_id):
    """
    API: 取得最新資料（用於即時更新）
    
    Args:
        gov_id: 政府代號
        
    Returns:
        JSON 格式的最新資料
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # 取得最新資料
    current_data = movie_service.get_current_week_data(gov_id)
    
    return jsonify(current_data)

@app.route('/api/export/<gov_id>')
def api_export(gov_id):
    """
    API: 匯出報表
    
    Args:
        gov_id: 政府代號
        
    Query Parameters:
        format: 檔案格式 (csv, excel)
        
    Returns:
        檔案下載
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # 取得格式參數
    export_format = request.args.get('format', 'csv')
    
    # 驗證格式
    is_valid, error_msg = validate_export_format(export_format)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    try:
        # 產生報表
        file_content, filename = prediction_service.export_report(gov_id, export_format)
        
        # 設定 MIME 類型
        if export_format == 'excel':
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            mimetype = 'text/csv'
        
        # 返回檔案
        return send_file(
            io.BytesIO(file_content),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/warning/<gov_id>')
def api_warning(gov_id):
    """
    API: 取得預警資訊
    
    Args:
        gov_id: 政府代號
        
    Returns:
        JSON 格式的預警資訊
    """
    # 驗證 gov_id
    is_valid, error_msg = validate_gov_id(gov_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # 取得預警資訊
    warning = prediction_service.check_decline_warning(gov_id)
    
    return jsonify(warning)

# ============= 輔助函數 =============
def prepare_decline_chart_data(history):
    """
    準備衰退率圖表資料
    
    Args:
        history: 歷史票房記錄列表
        
    Returns:
        圖表資料字典
    """
    weeks = []
    decline_rates = []
    
    for i in range(1, len(history)):
        if history[i-1].boxoffice > 0:
            rate = (history[i].boxoffice - history[i-1].boxoffice) / history[i-1].boxoffice
            weeks.append(history[i].week)
            decline_rates.append(rate)
    
    avg_decline_rate = sum(decline_rates) / len(decline_rates) if decline_rates else 0
    
    return {
        'weeks': weeks,
        'decline_rates': decline_rates,
        'avg_decline_rate': avg_decline_rate
    }

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
