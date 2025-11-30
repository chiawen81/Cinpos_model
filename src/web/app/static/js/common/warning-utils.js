/**
 * 衰退預警工具函數
 * 提供統一的預警徽章生成邏輯，避免重複程式碼
 */

/**
 * 根據預警等級生成對應的徽章 HTML
 * @param {string} level - 預警等級：'正常', '注意', '嚴重'
 * @param {Object} options - 選項
 * @param {boolean} options.showIcon - 是否顯示圖示（預設 false）
 * @returns {string} 徽章 HTML 字串
 */
function getWarningBadgeHTML(level, options = {}) {
    const showIcon = options.showIcon || false;

    switch (level) {
        case '嚴重':
            return showIcon
                ? '<span class="badge badge-danger">🚨 嚴重</span>'
                : '<span class="badge badge-danger">嚴重</span>';

        case '注意':
            return showIcon
                ? '<span class="badge badge-warning">⚠️ 注意</span>'
                : '<span class="badge badge-warning">注意</span>';

        case '正常':
        default:
            return '<span class="badge badge-success">正常</span>';
    }
}

/**
 * 根據預警物件生成徽章 HTML
 * @param {Object} warning - 預警物件
 * @param {string} warning.level - 預警等級
 * @param {Object} options - 選項
 * @returns {string} 徽章 HTML 字串
 */
function getWarningBadge(warning, options = {}) {
    if (!warning || !warning.level) {
        return '<span class="badge badge-success">正常</span>';
    }

    return getWarningBadgeHTML(warning.level, options);
}

/**
 * 根據預警等級取得對應的 CSS class
 * @param {string} level - 預警等級
 * @returns {string} CSS class 名稱
 */
function getWarningBadgeClass(level) {
    switch (level) {
        case '嚴重':
            return 'badge-danger';
        case '注意':
            return 'badge-warning';
        case '正常':
        default:
            return 'badge-success';
    }
}

/**
 * 根據預警等級取得對應的顏色
 * @param {string} level - 預警等級
 * @returns {string} 顏色代碼
 */
function getWarningColor(level) {
    switch (level) {
        case '嚴重':
            return '#dc3545'; // danger red
        case '注意':
            return '#ffc107'; // warning yellow
        case '正常':
        default:
            return '#28a745'; // success green
    }
}

// 匯出到全域（如果需要）
if (typeof window !== 'undefined') {
    window.warningUtils = {
        getWarningBadgeHTML,
        getWarningBadge,
        getWarningBadgeClass,
        getWarningColor
    };
}
