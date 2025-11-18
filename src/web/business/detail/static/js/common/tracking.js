/**
 * 追蹤管理共用模組
 * 說明: 提供電影追蹤功能的統一管理
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

// ============= 初始化全域實例 =============
const trackingManager = new TrackingManager();

// ============= 匯出到全域 =============
window.trackingManager = trackingManager;
