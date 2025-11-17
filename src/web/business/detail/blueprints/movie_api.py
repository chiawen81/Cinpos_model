"""
電影資料 API Blueprint
處理電影資料相關的 API 端點

注意：目前這些端點是代理外部 API (boxofficetw.tfai.org.tw)
TODO: 未來將改為使用自建資料庫
"""

from flask import Blueprint, request, jsonify
import requests

# 建立 Blueprint
movie_api_bp = Blueprint('movie_api', __name__, url_prefix='/api')


@movie_api_bp.route('/search-movie', methods=['GET'])
def search_movie():
    """
    API: 搜尋電影（代理公開 API）

    注意：此端點將改為使用自建資料庫，目前暫時保留直接呼叫外部 API

    Query Parameters:
        keyword: 搜尋關鍵字

    Returns:
        JSON 格式的搜尋結果
    """
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({'error': '請輸入搜尋關鍵字'}), 400

        # 呼叫外部 API（簡化版本）
        api_url = 'https://boxofficetw.tfai.org.tw/film/sf'
        params = {'keyword': keyword}
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()

        # 解析回應
        data = response.json()

        # 檢查回應格式（API 回應格式為 {data: {results: [...]}, success: true}）
        if data.get('success') and 'data' in data and 'results' in data['data']:
            api_results = data['data']['results']
            results = []
            for item in api_results:
                results.append({
                    'movieId': item.get('movieId'),
                    'name': item.get('name'),
                    'originalName': item.get('originalName', ''),
                    'releaseDate': item.get('releaseDate'),
                    'duration': item.get('duration'),
                    'rating': item.get('rating', ''),
                    'film_length': item.get('duration', 120),
                    'is_restricted': 1 if item.get('rating') == '限制級' else 0
                })
            return jsonify({'success': True, 'results': results})
        else:
            return jsonify({'success': True, 'results': []})

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'API 請求逾時，請稍後再試'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'搜尋失敗: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'搜尋失敗: {str(e)}'}), 500


@movie_api_bp.route('/movie-detail/<movie_id>', methods=['GET'])
def movie_detail_by_id(movie_id):
    """
    API: 取得電影詳細資料（代理公開 API）

    注意：此端點將改為使用自建資料庫，目前暫時保留直接呼叫外部 API

    Args:
        movie_id: 電影 ID

    Returns:
        JSON 格式的電影詳細資料
    """
    try:
        if not movie_id:
            return jsonify({'error': '電影 ID 不可為空'}), 400

        # 呼叫外部 API（簡化版本）
        api_url = f'https://boxofficetw.tfai.org.tw/film/gfd/{movie_id}'
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        # 解析回應
        data = response.json()

        # 檢查回應格式
        if data.get('success') and 'data' in data:
            movie_data = data['data']

            # 整理回傳資料
            result = {
                'movieId': movie_data.get('movieId'),
                'name': movie_data.get('name'),
                'originalName': movie_data.get('originalName', ''),
                'releaseDate': movie_data.get('releaseDate'),
                'rating': movie_data.get('rating', ''),
                'filmLength': movie_data.get('filmLength', 0),  # 單位：秒
                'weeks': movie_data.get('weeks', [])
            }

            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({'success': False, 'error': '無法取得電影資料'}), 404

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'API 請求逾時，請稍後再試'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'取得電影資料失敗: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'取得電影資料失敗: {str(e)}'}), 500
