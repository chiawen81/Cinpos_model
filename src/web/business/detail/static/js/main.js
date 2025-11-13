/**
 * 主要 JavaScript 檔案
 * 說明: 處理頁面互動和動態功能
 */

// ============= 全域變數 =============
const API_BASE_URL = window.location.origin;

// ============= 頁面初始化 =============
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeSidebarToggle();
    initializeCharts();
    initializeExportButtons();
    initializeAlerts();
});

// ============= 工具提示初始化 =============
function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.classList.add('tooltip');
        const tooltipContent = document.createElement('span');
        tooltipContent.className = 'tooltip-content';
        tooltipContent.textContent = element.getAttribute('data-tooltip');
        element.appendChild(tooltipContent);
    });
}

// ============= 側邊欄切換（手機版）=============
function initializeSidebarToggle() {
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebarNav = document.getElementById('sidebarNav');

    if (!toggleBtn || !sidebarNav) return;

    // 漢堡按鈕點擊事件
    toggleBtn.addEventListener('click', () => {
        toggleBtn.classList.toggle('active');
        sidebarNav.classList.toggle('open');
    });

    // 點擊選單項目後自動關閉（手機版）
    const navLinks = sidebarNav.querySelectorAll('.sidebar-nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                toggleBtn.classList.remove('active');
                sidebarNav.classList.remove('open');
            }
        });
    });

    // 視窗大小變化時，如果切換到桌面版，自動關閉選單
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            toggleBtn.classList.remove('active');
            sidebarNav.classList.remove('open');
        }
    });
}

// ============= 圖表初始化 =============
function initializeCharts() {
    // 這個函數會被 charts.js 覆寫
    console.log('Charts initialization placeholder');
}

// ============= 匯出功能 =============
function initializeExportButtons() {
    const exportBtns = document.querySelectorAll('[data-export]');
    
    exportBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const format = btn.getAttribute('data-export');
            const govId = btn.getAttribute('data-gov-id');
            
            await exportReport(govId, format);
        });
    });
}

/**
 * 匯出報表
 * @param {string} govId - 政府代號
 * @param {string} format - 檔案格式
 */
async function exportReport(govId, format) {
    try {
        // 顯示載入中
        showLoading();
        
        const response = await fetch(`${API_BASE_URL}/api/export/${govId}?format=${format}`);
        
        if (!response.ok) {
            throw new Error('匯出失敗');
        }
        
        // 取得檔案
        const blob = await response.blob();
        const filename = response.headers.get('Content-Disposition')
            ?.split('filename=')[1]
            ?.replace(/['"]/g, '') || `report.${format}`;
        
        // 下載檔案
        downloadFile(blob, filename);
        
        showAlert('success', '匯出成功', '報表已開始下載');
    } catch (error) {
        console.error('Export error:', error);
        showAlert('danger', '匯出失敗', error.message);
    } finally {
        hideLoading();
    }
}

/**
 * 下載檔案
 * @param {Blob} blob - 檔案內容
 * @param {string} filename - 檔案名稱
 */
function downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// ============= 警告提示 =============
function initializeAlerts() {
    // 自動關閉警告
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            fadeOutElement(alert);
        }, 5000);
    });
}

/**
 * 顯示警告訊息
 * @param {string} type - 警告類型 (success, warning, danger)
 * @param {string} title - 標題
 * @param {string} message - 訊息內容
 */
function showAlert(type, title, message) {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} fade-in`;
    
    const icons = {
        success: '✓',
        warning: '⚠',
        danger: '✗'
    };
    
    alertElement.innerHTML = `
        <span class="alert-icon">${icons[type] || 'ℹ'}</span>
        <div class="alert-content">
            <div class="alert-title">${title}</div>
            <div class="alert-message">${message}</div>
        </div>
    `;
    
    alertContainer.appendChild(alertElement);
    
    // 5秒後自動關閉
    setTimeout(() => {
        fadeOutElement(alertElement);
    }, 5000);
}

/**
 * 創建警告容器
 */
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.maxWidth = '400px';
    document.body.appendChild(container);
    return container;
}

// ============= 載入狀態 =============
/**
 * 顯示載入中
 */
function showLoading() {
    const loadingOverlay = document.getElementById('loading-overlay') || createLoadingOverlay();
    loadingOverlay.style.display = 'flex';
}

/**
 * 隱藏載入中
 */
function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

/**
 * 創建載入遮罩
 */
function createLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        display: none;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    overlay.innerHTML = '<div class="loading-spinner"></div>';
    document.body.appendChild(overlay);
    return overlay;
}

// ============= 工具函數 =============
/**
 * 淡出並移除元素
 * @param {HTMLElement} element - 要移除的元素
 */
function fadeOutElement(element) {
    element.style.transition = 'opacity 0.5s';
    element.style.opacity = '0';
    setTimeout(() => {
        element.remove();
    }, 500);
}

/**
 * 格式化貨幣
 * @param {number} amount - 金額
 * @returns {string} 格式化的貨幣字串
 */
function formatCurrency(amount) {
    if (amount >= 100000000) {
        return `NT$${(amount / 100000000).toFixed(1)}億`;
    } else if (amount >= 10000) {
        return `NT$${(amount / 10000).toFixed(1)}萬`;
    } else {
        return `NT$${amount.toLocaleString()}`;
    }
}

/**
 * 格式化百分比
 * @param {number} value - 數值
 * @returns {string} 格式化的百分比
 */
function formatPercentage(value) {
    return `${(value * 100).toFixed(1)}%`;
}

// ============= 導出函數 =============
window.movieApp = {
    showAlert,
    showLoading,
    hideLoading,
    exportReport,
    formatCurrency,
    formatPercentage
};
