/**
 * 電影詳細頁 JavaScript 檔案
 * 說明: 處理追蹤按鈕和收合功能
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
    initializeTrackButton();
    initializeCollapsibleSection();
});

// ============= 追蹤按鈕功能 =============
function initializeTrackButton() {
    const trackButton = document.getElementById('trackButton');
    if (!trackButton) return;

    const govId = trackButton.getAttribute('data-gov-id');
    const movieTitle = trackButton.getAttribute('data-title');

    // 設定初始狀態
    updateTrackButtonState(trackButton, govId);

    // 點擊事件
    trackButton.addEventListener('click', function() {
        const newState = trackingManager.toggleTracking(govId);
        updateTrackButtonState(trackButton, govId);

        // 顯示提示訊息
        if (newState) {
            window.movieApp.showAlert('success', '已加入追蹤', `「${movieTitle}」已加入追蹤清單`);
        } else {
            window.movieApp.showAlert('info', '已取消追蹤', `「${movieTitle}」已從追蹤清單移除`);
        }
    });
}

/**
 * 更新追蹤按鈕狀態
 */
function updateTrackButtonState(button, govId) {
    const isTracked = trackingManager.isTracked(govId);
    const iconSvg = button.querySelector('.track-icon');
    const textSpan = button.querySelector('.track-text');

    if (isTracked) {
        // 已追蹤狀態 - 顯示取消追蹤
        textSpan.textContent = '取消追蹤';
        // 更改圖示為勾選
        iconSvg.innerHTML = '<path d="M20 6L9 17l-5-5"></path>';
    } else {
        // 未追蹤狀態 - 顯示追蹤
        textSpan.textContent = '追蹤';
        // 更改圖示為加號
        iconSvg.innerHTML = '<path d="M12 5v14M5 12h14"></path>';
    }
}

// ============= 收合功能 =============
function initializeCollapsibleSection() {
    const toggleButton = document.getElementById('toggleMoreInfo');
    const collapsibleSection = document.getElementById('moreInfo');

    if (!toggleButton || !collapsibleSection) return;

    toggleButton.addEventListener('click', function() {
        const isOpen = collapsibleSection.classList.contains('open');

        if (isOpen) {
            // 收合
            collapsibleSection.classList.remove('open');
            toggleButton.classList.remove('open');
        } else {
            // 展開
            collapsibleSection.classList.add('open');
            toggleButton.classList.add('open');
        }
    });
}
