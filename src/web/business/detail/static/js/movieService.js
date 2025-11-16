/**
 * 電影相關 API Service
 * 統一管理所有電影相關的 API 調用
 */

const movieService = {
    /**
     * 搜尋電影
     * @param {string} keyword - 搜尋關鍵字
     * @returns {Promise<{success: boolean, results?: Array, error?: string}>}
     */
    async searchMovie(keyword) {
        try {
            const response = await fetch(`/api/search-movie?keyword=${encodeURIComponent(keyword)}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('搜尋電影錯誤:', error);
            return {
                success: false,
                error: '搜尋失敗,請檢查網路連線'
            };
        }
    },

    /**
     * 取得電影詳細資料
     * @param {string} movieId - 電影 ID
     * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
     */
    async getMovieDetail(movieId) {
        try {
            const response = await fetch(`/api/movie-detail/${movieId}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });
            const result = await response.json();
            return result;
        } catch (error) {
            console.error('取得電影詳細資料錯誤:', error);
            return {
                success: false,
                error: '取得電影資料失敗,請檢查網路連線'
            };
        }
    },

    /**
     * 預測票房
     * @param {Object} params - 預測參數
     * @param {Array} params.week_data - 週次資料
     * @param {Object} params.movie_info - 電影資訊
     * @param {number} params.predict_weeks - 預測週數
     * @returns {Promise<{success: boolean, data?: Object, error?: string, message?: string}>}
     */
    async predictBoxOffice({ week_data, movie_info, predict_weeks }) {
        try {
            const response = await fetch('/api/predict-new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    week_data,
                    movie_info,
                    predict_weeks
                })
            });
            const result = await response.json();
            return result;
        } catch (error) {
            console.error('預測票房錯誤:', error);
            return {
                success: false,
                error: '預測失敗,請檢查網路連線'
            };
        }
    },

    /**
     * 匯出預測結果
     * @param {Object} predictionResult - 預測結果
     * @param {string} format - 匯出格式 ('excel' 或 'csv')
     * @returns {Promise<Blob>}
     * @throws {Error} 當匯出失敗時拋出錯誤
     */
    async exportPrediction(predictionResult, format) {
        try {
            const response = await fetch('/api/predict-new/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prediction_result: predictionResult,
                    format: format
                })
            });

            if (!response.ok) {
                throw new Error('匯出失敗');
            }

            const blob = await response.blob();
            return blob;
        } catch (error) {
            console.error('匯出預測錯誤:', error);
            throw error;
        }
    },

    /**
     * 下載預處理資料
     * @param {Object} params - 下載參數
     * @param {Array} params.week_data - 週次資料
     * @param {Object} params.movie_info - 電影資訊
     * @returns {Promise<{blob: Blob, filename: string}>}
     * @throws {Error} 當下載失敗時拋出錯誤
     */
    async downloadPreprocessed({ week_data, movie_info }) {
        try {
            const response = await fetch('/api/predict-new/download-preprocessed', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    week_data,
                    movie_info
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '下載失敗');
            }

            // 取得檔案名稱
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `preprocessed_${new Date().getTime()}.csv`;
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }

            const blob = await response.blob();
            return { blob, filename };
        } catch (error) {
            console.error('下載預處理資料錯誤:', error);
            throw error;
        }
    }
};

// 匯出供其他模組使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = movieService;
}
