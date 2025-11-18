/**
 * 首頁 JavaScript 檔案
 * 說明: 處理追蹤功能和篩選功能
 */

// ============= 追蹤管理 =============
class TrackingManager {
    constructor() {
        this.storageKey = 'tracked_movies';
        this.trackedMovies = this.loadTrackedMovies();
    }

    /**
     * 從 localStorage 載入追蹤清單
     */
    loadTrackedMovies() {
        try {
            const data = localStorage.getItem(this.storageKey);
            return data ? JSON.parse(data) : [];
        } catch (error) {
            console.error('Failed to load tracked movies:', error);
            return [];
        }
    }

    /**
     * 儲存追蹤清單到 localStorage
     */
    saveTrackedMovies() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.trackedMovies));
        } catch (error) {
            console.error('Failed to save tracked movies:', error);
        }
    }

    /**
     * 檢查電影是否已追蹤
     */
    isTracked(govId) {
        return this.trackedMovies.includes(govId);
    }

    /**
     * 加入追蹤
     */
    addTracking(govId) {
        if (!this.isTracked(govId)) {
            this.trackedMovies.push(govId);
            this.saveTrackedMovies();
            return true;
        }
        return false;
    }

    /**
     * 取消追蹤
     */
    removeTracking(govId) {
        const index = this.trackedMovies.indexOf(govId);
        if (index > -1) {
            this.trackedMovies.splice(index, 1);
            this.saveTrackedMovies();
            return true;
        }
        return false;
    }

    /**
     * 切換追蹤狀態
     */
    toggleTracking(govId) {
        if (this.isTracked(govId)) {
            this.removeTracking(govId);
            return false;
        } else {
            this.addTracking(govId);
            return true;
        }
    }
}

// ============= 初始化 =============
const trackingManager = new TrackingManager();

document.addEventListener('DOMContentLoaded', function() {
    initializeTrackingButtons();
    initializeFilterTabs();
    updateTrackingCount();
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
    const isTracked = trackingManager.isTracked(govId);

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
    const newState = trackingManager.toggleTracking(govId);

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
 */
function updateTrackingCount() {
    const trackingCount = trackingManager.trackedMovies.length;
    const statValue = document.querySelector('.stats-grid .stat-card:nth-child(2) .stat-value');
    if (statValue) {
        statValue.textContent = trackingCount;
    }
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
    const tbody = document.getElementById('movieTableBody');
    const rows = tbody.querySelectorAll('tr');

    rows.forEach(row => {
        let shouldShow = false;

        switch (filterType) {
            case 'all':
                shouldShow = true;
                break;

            case 'now-showing':
                shouldShow = row.getAttribute('data-filter-type') === 'now-showing';
                break;

            case 'tracked':
                const govId = row.querySelector('.btn-track-text')?.getAttribute('data-gov-id');
                shouldShow = govId && trackingManager.isTracked(govId);
                break;
        }

        row.style.display = shouldShow ? '' : 'none';
    });

    // 檢查是否有顯示的電影
    const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');

    if (visibleRows.length === 0) {
        showNoResultsMessage(tbody, filterType);
    } else {
        removeNoResultsMessage(tbody);
    }
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

// ============= 匯出功能 =============
window.movieTracking = {
    trackingManager,
    updateButtonState,
    updateTrackingCount
};
