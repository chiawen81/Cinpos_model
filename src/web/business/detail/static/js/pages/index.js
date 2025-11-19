/**
 * 首頁 JavaScript 檔案
 * 說明: 處理追蹤功能和篩選功能
 * 注意: TrackingManager 已移至 common/tracking.js
 */

// ============= 初始化 =============
// 使用全域的 trackingManager 實例（定義於 common/tracking.js）

// 分頁狀態
let currentPage = 1;
let totalPages = 1;
let currentFilters = {};

document.addEventListener('DOMContentLoaded', function() {
    initializeTrackingButtons();
    initializeFilterTabs();
    initializePagination();
    loadAllStats();  // 載入所有統計資料
    loadBoxOfficeList();  // 載入票房列表資料
});

// ============= 追蹤按鈕功能 =============
function initializeTrackingButtons() {
    const trackButtons = document.querySelectorAll('.btn-track-text');

    trackButtons.forEach(button => {
        const govId = button.getAttribute('data-gov-id');

        // 根據追蹤狀態設定按鈕文字和樣式
        updateButtonState(button, govId);

        // 點擊事件
        button.addEventListener('click', function(e) {
            e.preventDefault();
            handleTrackingToggle(button, govId);
        });
    });
}

/**
 * 更新按鈕狀態
 */
function updateButtonState(button, govId) {
    const isTracked = window.trackingManager.isTracked(govId);

    if (isTracked) {
        button.textContent = '取消追蹤';
        button.classList.add('tracked');
    } else {
        button.textContent = '加入追蹤';
        button.classList.remove('tracked');
    }

    // 更新所在行的 data-tracked 屬性
    const row = button.closest('tr');
    if (row) {
        row.setAttribute('data-tracked', isTracked);
    }
}

/**
 * 處理追蹤切換
 */
function handleTrackingToggle(button, govId) {
    const newState = window.trackingManager.toggleTracking(govId);

    // 更新按鈕狀態
    updateButtonState(button, govId);

    // 顯示提示訊息
    const movieName = button.closest('tr').querySelector('.movie-link').textContent;
    if (newState) {
        window.movieApp.showAlert('success', '已加入追蹤', `「${movieName}」已加入追蹤清單`);
    } else {
        window.movieApp.showAlert('info', '已取消追蹤', `「${movieName}」已從追蹤清單移除`);
    }

    // 更新統計卡片中的追蹤數量
    updateTrackingCount();

    // 如果當前在「我的追蹤」篩選，則重新篩選
    const activeFilter = document.querySelector('.filter-tab.active');
    if (activeFilter && activeFilter.getAttribute('data-filter') === 'tracked') {
        filterMovies('tracked');
    }
}

/**
 * 更新追蹤數量顯示
 * ⚠️ 臨時方案：使用 localStorage 追蹤清單
 * 🔄 未來改進：改用後端 API 從資料庫取得使用者的追蹤清單
 */
function updateTrackingCount() {
    // 重新載入所有統計資料（包含追蹤數量和預警電影）
    loadAllStats();
}

// ============= 篩選功能 =============
function initializeFilterTabs() {
    const filterTabs = document.querySelectorAll('.filter-tab');

    filterTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 移除所有 active 狀態
            filterTabs.forEach(t => t.classList.remove('active'));

            // 設定當前 tab 為 active
            this.classList.add('active');

            // 執行篩選
            const filterType = this.getAttribute('data-filter');
            filterMovies(filterType);
        });
    });
}

/**
 * 篩選電影
 */
function filterMovies(filterType) {
    // 根據篩選類型構建 API 查詢參數
    const filters = {};

    switch (filterType) {
        case 'all':
            // 不加任何篩選條件
            break;

        case 'now-showing':
            // 近期上映：最近30天內上映的電影
            const today = new Date();
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(today.getDate() - 30);

            filters.start_date = thirtyDaysAgo.toISOString().split('T')[0];
            filters.release_status = '上映中';
            break;

        case 'tracked':
            // ⚠️ 臨時方案：前端處理追蹤篩選
            // 🔄 未來改進：改用後端 API 從資料庫取得使用者的追蹤清單
            // 目前使用 localStorage 儲存追蹤清單，所以在前端篩選
            filters._client_side_filter = 'tracked';
            break;
    }

    // 重置頁碼並重新載入列表
    currentPage = 1;
    currentFilters = filters;
    loadBoxOfficeList(filters);
}

/**
 * 顯示無結果訊息
 */
function showNoResultsMessage(tbody, filterType) {
    // 先移除舊的訊息
    removeNoResultsMessage(tbody);

    const row = document.createElement('tr');
    row.className = 'no-results-row';
    row.innerHTML = `
        <td colspan="9" style="text-align: center; padding: 40px; color: var(--text-muted);">
            ${getNoResultsMessage(filterType)}
        </td>
    `;
    tbody.appendChild(row);
}

/**
 * 移除無結果訊息
 */
function removeNoResultsMessage(tbody) {
    const noResultsRow = tbody.querySelector('.no-results-row');
    if (noResultsRow) {
        noResultsRow.remove();
    }
}

/**
 * 取得無結果訊息
 */
function getNoResultsMessage(filterType) {
    switch (filterType) {
        case 'tracked':
            return '尚未追蹤任何電影<br><small>點擊「加入追蹤」來追蹤感興趣的電影</small>';
        case 'now-showing':
            return '目前沒有正在上映的電影';
        default:
            return '沒有找到電影';
    }
}

// ============= 分頁器功能 =============
/**
 * 初始化分頁器
 */
function initializePagination() {
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            if (currentPage > 1) {
                currentPage--;
                loadBoxOfficeList({...currentFilters, page: currentPage});
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            if (currentPage < totalPages) {
                currentPage++;
                loadBoxOfficeList({...currentFilters, page: currentPage});
            }
        });
    }
}

/**
 * 渲染分頁器
 */
function renderPagination(current, total) {
    currentPage = current;
    totalPages = total;

    const paginationPages = document.getElementById('paginationPages');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    // 清空頁碼區域
    paginationPages.innerHTML = '';

    // 如果只有一頁，隱藏分頁器
    if (total <= 1) {
        document.getElementById('paginationContainer').style.display = 'none';
        return;
    }

    // 顯示分頁器
    document.getElementById('paginationContainer').style.display = 'flex';

    // 更新上一頁按鈕
    prevBtn.disabled = current <= 1;

    // 更新下一頁按鈕
    nextBtn.disabled = current >= total;

    // 生成頁碼按鈕
    const maxPagesToShow = 5;
    let startPage = Math.max(1, current - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(total, startPage + maxPagesToShow - 1);

    // 調整起始頁,確保顯示足夠的頁碼
    if (endPage - startPage < maxPagesToShow - 1) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }

    // 第一頁
    if (startPage > 1) {
        const firstBtn = createPageButton(1, current);
        paginationPages.appendChild(firstBtn);

        if (startPage > 2) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'pagination-ellipsis';
            ellipsis.textContent = '...';
            paginationPages.appendChild(ellipsis);
        }
    }

    // 中間頁碼
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = createPageButton(i, current);
        paginationPages.appendChild(pageBtn);
    }

    // 最後一頁
    if (endPage < total) {
        if (endPage < total - 1) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'pagination-ellipsis';
            ellipsis.textContent = '...';
            paginationPages.appendChild(ellipsis);
        }

        const lastBtn = createPageButton(total, current);
        paginationPages.appendChild(lastBtn);
    }
}

/**
 * 創建頁碼按鈕
 */
function createPageButton(pageNum, currentPageNum) {
    const button = document.createElement('button');
    button.className = 'btn btn-secondary pagination-page';
    button.textContent = pageNum;

    if (pageNum === currentPageNum) {
        button.classList.add('active');
    }

    button.addEventListener('click', function() {
        if (pageNum !== currentPage) {
            currentPage = pageNum;
            loadBoxOfficeList({...currentFilters, page: pageNum});
        }
    });

    return button;
}

// ============= 統計資料載入 =============
/**
 * 載入所有統計資料
 * ⚠️ 臨時方案：從 localStorage 取得追蹤清單傳給後端
 * 🔄 未來改進：後端根據使用者 ID 從資料庫查詢追蹤清單
 */
async function loadAllStats() {
    try {
        // 從 localStorage 取得追蹤的電影 ID 列表
        const trackedMovieIds = window.trackingManager.trackedMovies;

        // 發送 POST 請求，傳入追蹤的電影 ID 列表
        const response = await fetch('/api/stats/all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tracked_movie_ids: trackedMovieIds
            })
        });
        const result = await response.json();

        if (result.success && result.data) {
            const data = result.data;

            // 1. 更新近期上映電影統計
            if (data.recent_movies) {
                const recentData = data.recent_movies;

                // 更新近期上映電影數量
                const countElement = document.getElementById('recentMoviesCount');
                if (countElement) {
                    countElement.textContent = recentData.recent_count || 0;
                }

                // 更新變化數值
                const changeElement = document.getElementById('recentMoviesChange');
                if (changeElement) {
                    const change = recentData.change_from_last_week || 0;

                    // 清除載入中樣式
                    changeElement.className = 'stat-change';

                    // 設定變化文字和樣式
                    if (change > 0) {
                        changeElement.classList.add('positive');
                        changeElement.textContent = `+${change} 較上週`;
                    } else if (change < 0) {
                        changeElement.classList.add('negative');
                        changeElement.textContent = `${change} 較上週`;
                    } else {
                        changeElement.textContent = '與上週持平';
                    }
                }
            }

            // 2. 更新追蹤中電影統計
            if (data.tracked_movies) {
                const trackedCountElement = document.getElementById('trackedMoviesCount');
                if (trackedCountElement) {
                    trackedCountElement.textContent = data.tracked_movies.count || 0;
                }
            }

            // 3. 更新預警電影統計
            if (data.warning_movies) {
                const warningData = data.warning_movies;

                // 更新總數
                const warningCountElement = document.getElementById('warningMoviesCount');
                if (warningCountElement) {
                    warningCountElement.textContent = warningData.total_count || 0;
                }

                // 更新詳細資訊（注意 x 部 / 嚴重 y 部）
                const warningDetailElement = document.getElementById('warningMoviesDetail');
                if (warningDetailElement) {
                    const attentionCount = warningData.attention_count || 0;
                    const criticalCount = warningData.critical_count || 0;

                    // 清除載入中樣式
                    warningDetailElement.className = 'stat-change';

                    if (warningData.total_count > 0) {
                        // 有預警電影時顯示詳細資訊
                        warningDetailElement.classList.add('negative');
                        warningDetailElement.innerHTML = `注意 ${attentionCount} 部 / 嚴重 ${criticalCount} 部`;
                    } else {
                        // 沒有預警電影時顯示正常
                        warningDetailElement.textContent = '無需關注';
                    }
                }
            }
        } else {
            console.error('載入統計資料失敗:', result.error || '未知錯誤');
            showStatsError();
        }
    } catch (error) {
        console.error('載入統計資料時發生錯誤:', error);
        showStatsError();
    }
}

/**
 * 載入近期上映電影統計資料（保留舊函數以防其他地方使用）
 * @deprecated 請使用 loadAllStats() 代替
 */
async function loadRecentMoviesStats() {
    try {
        const response = await fetch('/api/stats/recent-movies');
        const result = await response.json();

        if (result.success && result.data) {
            const data = result.data;

            // 更新近期上映電影數量
            const countElement = document.getElementById('recentMoviesCount');
            if (countElement) {
                countElement.textContent = data.recent_count || 0;
            }

            // 更新變化數值
            const changeElement = document.getElementById('recentMoviesChange');
            if (changeElement) {
                const change = data.change_from_last_week || 0;

                // 清除載入中樣式
                changeElement.className = 'stat-change';

                // 設定變化文字和樣式
                if (change > 0) {
                    changeElement.classList.add('positive');
                    changeElement.textContent = `+${change} 較上週`;
                } else if (change < 0) {
                    changeElement.classList.add('negative');
                    changeElement.textContent = `${change} 較上週`;
                } else {
                    changeElement.textContent = '與上週持平';
                }
            }
        } else {
            console.error('載入統計資料失敗:', result.error || '未知錯誤');
            showStatsError();
        }
    } catch (error) {
        console.error('載入統計資料時發生錯誤:', error);
        showStatsError();
    }
}

/**
 * 顯示統計資料載入錯誤
 */
function showStatsError() {
    const countElement = document.getElementById('recentMoviesCount');
    if (countElement) {
        countElement.textContent = '-';
    }

    const changeElement = document.getElementById('recentMoviesChange');
    if (changeElement) {
        changeElement.className = 'stat-change';
        changeElement.textContent = '載入失敗';
    }
}

// ============= 票房列表載入 =============
/**
 * 載入票房列表資料
 */
async function loadBoxOfficeList(filters = {}) {
    const tbody = document.getElementById('movieTableBody');

    // 顯示載入中
    tbody.innerHTML = `
        <tr>
            <td colspan="9" style="text-align: center; padding: 40px; color: var(--text-muted);">
                <span class="loading-text">載入中...</span>
            </td>
        </tr>
    `;

    try {
        // ⚠️ 臨時方案：檢查是否為前端篩選「我的追蹤」
        // 🔄 未來改進：改用後端 API 從資料庫取得使用者的追蹤清單
        const isClientSideTrackedFilter = filters._client_side_filter === 'tracked';

        // 構建查詢參數
        const params = new URLSearchParams({
            page: filters.page || 1,
            page_size: isClientSideTrackedFilter ? 100 : (filters.page_size || 10), // 追蹤篩選時先取得所有資料
            sort_by: filters.sort_by || 'release_date',
            sort_order: filters.sort_order || 'desc'
        });

        // 加入篩選條件（排除前端篩選標記）
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        if (filters.warning_status) params.append('warning_status', filters.warning_status);
        if (filters.release_status) params.append('release_status', filters.release_status);
        if (filters.is_first_run !== undefined) params.append('is_first_run', filters.is_first_run);

        // 發送 API 請求
        const response = await fetch(`/api/boxoffice/list?${params}`);
        const result = await response.json();

        if (result.success && result.data) {
            let moviesToDisplay = result.data;

            // ⚠️ 臨時方案：前端篩選追蹤的電影
            // 🔄 未來改進：後端直接返回使用者追蹤的電影
            if (isClientSideTrackedFilter) {
                const trackedIds = window.trackingManager.trackedMovies;
                moviesToDisplay = result.data.filter(movie =>
                    trackedIds.includes(movie.movie_id)
                );

                // 如果沒有追蹤的電影，顯示提示訊息
                if (moviesToDisplay.length === 0) {
                    showNoResultsMessage(tbody, 'tracked');
                    // 隱藏分頁器
                    document.getElementById('paginationContainer').style.display = 'none';
                    return;
                }
            }

            renderBoxOfficeList(moviesToDisplay);

            // 重新初始化追蹤按鈕
            initializeTrackingButtons();

            // 渲染分頁器
            // 如果 API 回應包含分頁資訊，使用它；否則計算總頁數
            const totalPages = result.pagination?.total_pages || 1;
            const currentPageNum = result.pagination?.page || filters.page || 1;

            renderPagination(currentPageNum, totalPages);
        } else {
            console.error('載入票房列表失敗:', result.error || '未知錯誤');
            showLoadError(tbody);
            // 隱藏分頁器
            document.getElementById('paginationContainer').style.display = 'none';
        }
    } catch (error) {
        console.error('載入票房列表時發生錯誤:', error);
        showLoadError(tbody);
        // 隱藏分頁器
        document.getElementById('paginationContainer').style.display = 'none';
    }
}

/**
 * 渲染票房列表
 */
function renderBoxOfficeList(movies) {
    const tbody = document.getElementById('movieTableBody');
    tbody.innerHTML = '';

    if (movies.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 40px; color: var(--text-muted);">
                    目前沒有電影資料
                </td>
            </tr>
        `;
        return;
    }

    movies.forEach(movie => {
        const row = createMovieRow(movie);
        tbody.appendChild(row);
    });
}

/**
 * 創建電影列表行
 */
function createMovieRow(movie) {
    const row = document.createElement('tr');
    row.setAttribute('data-filter-type', 'now-showing');
    row.setAttribute('data-tracked', movie.is_tracked);

    // 格式化數字
    const formatCurrency = (value) => {
        if (!value || value === null || value === undefined) return '-';
        // 原始資料單位是「元」，轉換為「萬元」顯示
        const wan = value / 10000;
        return `NT$${wan.toFixed(0)}萬`;
    };

    const formatPercentage = (value) => {
        if (value === null || value === undefined) return '-';
        // value 是小數（如 -0.3 表示 -30%）
        return `${(value * 100).toFixed(1)}%`;
    };

    // 判斷衰退率的顏色
    const getDeclineClass = (rate) => {
        if (!rate) return '';
        if (rate < -0.3) return 'text-warning';
        if (rate < -0.5) return 'text-danger';
        return 'text-success';
    };

    // 判斷預測差距的顏色
    const getAccuracyClass = (accuracy) => {
        if (!accuracy) return '';
        if (Math.abs(accuracy) < 0.1) return 'text-success';
        if (Math.abs(accuracy) < 0.2) return 'text-warning';
        return 'text-danger';
    };

    // 預警狀態徽章
    const getBadgeClass = (status) => {
        switch (status) {
            case '正常': return 'badge-success';
            case '注意': return 'badge-warning';
            case '嚴重': return 'badge-danger';
            default: return 'badge-secondary';
        }
    };

    row.innerHTML = `
        <td>
            <a href="/movie/${movie.movie_id}" class="movie-link">${movie.movie_name}</a>
        </td>
        <td>第${movie.current_week}週</td>
        <td>${formatCurrency(movie.current_week_predicted)}</td>
        <td>${formatCurrency(movie.last_week_predicted)}</td>
        <td>${formatCurrency(movie.last_week_actual)}</td>
        <td class="${getDeclineClass(movie.last_week_decline_rate)}">
            ${formatPercentage(movie.last_week_decline_rate)}
        </td>
        <td class="${getAccuracyClass(movie.prediction_accuracy)}">
            ${formatPercentage(movie.prediction_accuracy)}
        </td>
        <td>
            <span class="badge ${getBadgeClass(movie.warning_status)}">
                ${movie.warning_status}
            </span>
        </td>
        <td>
            <button class="btn-track-text" data-gov-id="${movie.movie_id}">
                ${movie.is_tracked ? '取消追蹤' : '加入追蹤'}
            </button>
        </td>
    `;

    return row;
}

/**
 * 顯示載入錯誤
 */
function showLoadError(tbody) {
    tbody.innerHTML = `
        <tr>
            <td colspan="9" style="text-align: center; padding: 40px; color: var(--text-danger);">
                載入失敗，請稍後再試
            </td>
        </tr>
    `;
}

// ============= 匯出功能 =============
window.movieTracking = {
    trackingManager: window.trackingManager,
    updateButtonState,
    updateTrackingCount,
    loadAllStats,
    loadRecentMoviesStats,
    loadBoxOfficeList
};
