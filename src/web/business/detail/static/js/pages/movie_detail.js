/**
 * 電影詳細頁 JavaScript 檔案
 * 說明: 處理追蹤按鈕和收合功能
 * 注意: TrackingManager 已移至 common/tracking.js
 */

// ============= 初始化 =============
// 使用全域的 trackingManager 實例
const trackingManager = window.trackingManager;

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
