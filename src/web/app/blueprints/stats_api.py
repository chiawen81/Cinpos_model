"""
統計資料 API Blueprint
處理首頁統計卡片的 API 端點
"""

from flask import Blueprint, jsonify
from ..services.stats_service import StatsService

# 建立 Blueprint
stats_api_bp = Blueprint('stats_api', __name__, url_prefix='/api/stats')

# 初始化服務
stats_service = StatsService()


@stats_api_bp.route('/recent-movies', methods=['GET'])
def get_recent_movies():
    """
    API: 取得近期上映電影統計

    Returns:
        JSON 格式的統計資料，包含：
        - recent_count: 近期上映電影數量（1-4週內上映）
        - change_from_last_week: 較上週的變化數量
        - last_week_count: 上週的近期上映電影數量
    """
    try:
        stats = stats_service.get_recent_movies_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'取得統計資料失敗: {str(e)}'
        }), 500


@stats_api_bp.route('/all', methods=['GET', 'POST'])
def get_all_stats():
    """
    API: 取得所有統計資料

    Query Parameters (GET) 或 Request Body (POST):
        tracked_movie_ids: 追蹤的電影 ID 列表（逗號分隔或 JSON 陣列）

    Returns:
        JSON 格式的所有統計資料，包含：
        - recent_movies: 近期上映電影統計
        - tracked_movies: 追蹤中電影統計
        - warning_movies: 預警電影統計
    """
    try:
        # ⚠️ 臨時方案：從請求中取得追蹤的電影 ID 列表
        # 🔄 未來改進：從後端資料庫根據使用者 ID 查詢追蹤清單
        from flask import request

        tracked_movie_ids = []

        # 支援 POST 請求（JSON body）
        if request.method == 'POST':
            data = request.get_json() or {}
            tracked_movie_ids = data.get('tracked_movie_ids', [])
        # 支援 GET 請求（query parameter）
        else:
            tracked_ids_param = request.args.get('tracked_movie_ids', '')
            if tracked_ids_param:
                tracked_movie_ids = [id.strip() for id in tracked_ids_param.split(',') if id.strip()]

        stats = stats_service.get_all_stats(tracked_movie_ids=tracked_movie_ids)
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'取得統計資料失敗: {str(e)}'
        }), 500
