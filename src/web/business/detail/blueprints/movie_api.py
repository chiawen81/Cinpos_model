"""
電影資料 API Blueprint
處理電影資料相關的 API 端點

使用本地資料庫，不再依賴外部 API
"""

from flask import Blueprint, request, jsonify
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime

# 建立 Blueprint
movie_api_bp = Blueprint('movie_api', __name__, url_prefix='/api')

# 資料路徑配置
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
MOVIEINFO_DIR = BASE_DIR / 'data' / 'processed' / 'movieInfo_gov' / 'combined'
BOXOFFICE_WEEKLY_DIR = BASE_DIR / 'data' / 'raw' / 'boxoffice_weekly' / '2025'
BOXOFFICE_PERMOVIE_FULL_DIR = BASE_DIR / 'data' / 'raw' / 'boxoffice_permovie' / 'full'


def get_latest_movieinfo_csv():
    """取得最新的 movieInfo CSV 檔案"""
    try:
        csv_files = sorted(MOVIEINFO_DIR.glob('movieInfo_gov_full_*.csv'), reverse=True)
        if not csv_files:
            return None
        return csv_files[0]
    except Exception as e:
        print(f"Error finding latest CSV: {e}")
        return None


def load_movieinfo_data():
    """載入電影基本資料"""
    latest_csv = get_latest_movieinfo_csv()
    if not latest_csv:
        return None
    try:
        df = pd.read_csv(latest_csv, encoding='utf-8-sig')
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None


@movie_api_bp.route('/debug/paths', methods=['GET'])
def debug_paths():
    """除錯用端點：顯示路徑資訊"""
    json_files = list(BOXOFFICE_WEEKLY_DIR.glob('boxoffice_*.json'))
    return jsonify({
        'BASE_DIR': str(BASE_DIR),
        'BOXOFFICE_WEEKLY_DIR': str(BOXOFFICE_WEEKLY_DIR),
        'dir_exists': BOXOFFICE_WEEKLY_DIR.exists(),
        'json_files_count': len(json_files),
        'json_files': [str(f) for f in json_files[:3]]  # 只顯示前3個
    })


@movie_api_bp.route('/debug/search', methods=['GET'])
def debug_search():
    """除錯用端點：測試搜尋邏輯"""
    keyword = request.args.get('keyword', '左').strip()

    # 讀取所有週票房資料
    all_movies = {}
    json_files = sorted(BOXOFFICE_WEEKLY_DIR.glob('boxoffice_*.json'))

    debug_info = {
        'keyword': keyword,
        'json_files_count': len(json_files),
        'movies_loaded': 0,
        'sample_movies': [],
        'matched_movies': []
    }

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'data' in data and 'dataItems' in data['data']:
                    for item in data['data']['dataItems']:
                        movie_id = item.get('movieId')
                        if movie_id and movie_id not in all_movies:
                            all_movies[movie_id] = item
        except Exception as e:
            debug_info['error'] = str(e)
            continue

    debug_info['movies_loaded'] = len(all_movies)

    # 顯示前5部電影作為樣本
    for movie_id, item in list(all_movies.items())[:5]:
        debug_info['sample_movies'].append({
            'movieId': movie_id,
            'name': item.get('name', '')
        })

    # 搜尋符合關鍵字的電影
    keyword_lower = keyword.lower()
    for movie_id, item in all_movies.items():
        name = item.get('name', '')
        if keyword_lower in name.lower():
            debug_info['matched_movies'].append({
                'movieId': movie_id,
                'name': name
            })

    return jsonify(debug_info)


@movie_api_bp.route('/search-movie', methods=['GET'])
def search_movie():
    """
    API: 搜尋電影（使用本地資料庫）

    從 boxoffice_weekly/2025 資料夾中搜尋電影

    Query Parameters:
        keyword: 搜尋關鍵字

    Returns:
        JSON 格式的搜尋結果
    """
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({'error': '請輸入搜尋關鍵字'}), 400

        # 讀取所有週票房資料
        all_movies = {}
        json_files = sorted(BOXOFFICE_WEEKLY_DIR.glob('boxoffice_*.json'))

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'data' in data and 'dataItems' in data['data']:
                        for item in data['data']['dataItems']:
                            movie_id = item.get('movieId')
                            # 使用 movieId 作為 key 避免重複
                            if movie_id and movie_id not in all_movies:
                                all_movies[movie_id] = item
            except Exception as e:
                # 記錄錯誤但繼續處理其他檔案
                print(f"Error reading {json_file}: {e}")
                continue

        # 載入電影詳細資料（用於取得片長、分級等資訊）
        movieinfo_df = load_movieinfo_data()

        # 搜尋符合關鍵字的電影
        keyword_lower = keyword.lower()
        results = []

        for movie_id, item in all_movies.items():
            name = item.get('name', '')
            if keyword_lower in name.lower():
                # 預設值
                film_length = 120
                duration = 120
                rating = ''
                is_restricted = 0

                # 嘗試從 movieInfo 中查詢詳細資訊
                if movieinfo_df is not None:
                    movie_row = movieinfo_df[movieinfo_df['gov_id'].astype(str) == str(movie_id)]
                    if not movie_row.empty:
                        movie = movie_row.iloc[0]
                        # 取得片長（分鐘）
                        if pd.notna(movie.get('film_length')):
                            film_length = int(movie['film_length'])
                            duration = film_length
                        # 取得分級
                        if pd.notna(movie.get('rating')):
                            rating = str(movie['rating'])
                            # 判斷是否為限制級
                            is_restricted = 1 if '限制級' in rating or 'R' in rating else 0

                results.append({
                    'movieId': movie_id,
                    'name': name,
                    'originalName': '',  # boxoffice_weekly 沒有原文片名
                    'releaseDate': item.get('releaseDate', ''),
                    'duration': duration,
                    'rating': rating,
                    'film_length': film_length,
                    'is_restricted': is_restricted
                })

        return jsonify({'success': True, 'results': results})

    except Exception as e:
        return jsonify({'success': False, 'error': f'搜尋失敗: {str(e)}'}), 500


@movie_api_bp.route('/movie/info/<movie_id>', methods=['GET'])
def movie_detail_by_id(movie_id):
    """
    API: 取得電影詳細資料（使用本地資料庫）

    從 movieInfo_gov CSV 讀取電影資料

    Args:
        movie_id: 電影 ID (gov_id)

    Returns:
        JSON 格式的電影詳細資料
    """
    try:
        if not movie_id:
            return jsonify({'error': '電影 ID 不可為空'}), 400

        # 載入電影資料
        df = load_movieinfo_data()
        if df is None:
            return jsonify({'success': False, 'error': '無法載入電影資料庫'}), 500

        # 查找電影資料
        movie_row = df[df['gov_id'].astype(str) == str(movie_id)]

        if movie_row.empty:
            return jsonify({'success': False, 'error': '找不到該電影'}), 404

        # 取得第一筆資料
        movie = movie_row.iloc[0]

        # 整理回傳資料
        result = {
            'movieId': str(movie['gov_id']),
            'name': movie['gov_title_zh'],
            'originalName': movie['gov_title_en'] if pd.notna(movie['gov_title_en']) else '',
            'releaseDate': movie['official_release_date'] if pd.notna(movie['official_release_date']) else '',
            'rating': movie['rating'] if pd.notna(movie['rating']) else '',
            'filmLength': int(movie['film_length']) * 60 if pd.notna(movie['film_length']) else 0,  # 轉換為秒
            'region': movie['region'] if pd.notna(movie['region']) else '',
            'publisher': movie['publisher'] if pd.notna(movie['publisher']) else '',
            'director': movie['director'] if pd.notna(movie['director']) else '',
            'actors': movie['actor_list'] if pd.notna(movie['actor_list']) else ''
        }

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'success': False, 'error': f'取得電影資料失敗: {str(e)}'}), 500


@movie_api_bp.route('/movie/boxoffice/<movid>', methods=['GET'])
def movie_boxoffice(movid):
    """
    API: 取得電影完整資料（票房 + 電影資訊）

    從 boxoffice_permovie/full 資料夾讀取電影完整資料

    Args:
        movid: 電影 ID (gov_id)

    Returns:
        JSON 格式的完整電影資料（包含票房歷史、電影資訊、演員、導演等）
    """
    try:
        if not movid:
            return jsonify({'error': '電影 ID 不可為空'}), 400

        # 查找對應的 JSON 檔案（檔名格式：{movid}_*.json）
        json_files = list(BOXOFFICE_PERMOVIE_FULL_DIR.glob(f'{movid}_*.json'))

        if not json_files:
            return jsonify({'success': False, 'error': '找不到該電影的資料'}), 404

        # 讀取第一個符合的檔案
        json_file = json_files[0]
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 檢查資料格式
        if not data.get('success') or 'data' not in data:
            return jsonify({'success': False, 'error': '資料格式錯誤'}), 500

        movie_data = data['data']

        # 整理回傳資料
        result = {
            'movieId': movie_data.get('movieId'),
            'name': movie_data.get('name'),
            'originalName': movie_data.get('originalName', ''),
            'region': movie_data.get('region', ''),
            'rating': movie_data.get('rating', ''),
            'releaseDate': movie_data.get('releaseDate', ''),
            'publisher': movie_data.get('publisher', ''),
            'filmLength': movie_data.get('filmLength', 0),  # 秒
            'amountInThisWeek': movie_data.get('amountInThisWeek', 0),
            'totalAmount': movie_data.get('totalAmount', 0),
            'filmMembers': movie_data.get('filmMembers', []),  # 演員、導演等
            'weeks': movie_data.get('weeks', []),  # 每週票房歷史
            'weekends': movie_data.get('weekends', [])  # 每週末票房歷史
        }

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'success': False, 'error': f'取得電影資料失敗: {str(e)}'}), 500
