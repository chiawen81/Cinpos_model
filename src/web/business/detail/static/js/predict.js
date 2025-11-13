/**
 * 預測頁面交互邏輯
 */

// DOM 元素
const searchInput = document.getElementById('movieSearchInput');
const searchButton = document.getElementById('searchButton');
const searchDropdown = document.getElementById('searchDropdown');
const selectedMovieInfo = document.getElementById('selectedMovieInfo');
const movieBasicInfo = document.getElementById('movieBasicInfo');
const selectedMovieTitle = document.getElementById('selectedMovieTitle');
const clearSelection = document.getElementById('clearSelection');
const addWeekButton = document.getElementById('addWeekButton');
const predictButton = document.getElementById('predictButton');

// 當前選中的電影
let currentSelectedMovie = null;

// 搜尋防抖計時器
let searchTimeout = null;

// 搜尋功能
searchInput.addEventListener('input', handleSearchInput);
searchButton.addEventListener('click', performSearch);

function handleSearchInput(e) {
    const keyword = e.target.value.trim();

    if (keyword.length === 0) {
        searchDropdown.style.display = 'none';
        return;
    }

    // 防抖：延遲 500ms 後才搜尋
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        performSearch();
    }, 500);
}

async function performSearch() {
    const keyword = searchInput.value.trim();

    if (keyword.length === 0) {
        searchDropdown.style.display = 'none';
        return;
    }

    // 顯示載入中
    searchDropdown.innerHTML = '<div class="search-loading">搜尋中...</div>';
    searchDropdown.style.display = 'block';

    try {
        // 呼叫後端代理 API（避免 CORS 問題）
        const response = await fetch(`/api/search-movie?keyword=${encodeURIComponent(keyword)}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        const data = await response.json();

        if (!data.success) {
            showSearchError(data.error || '搜尋失敗，請稍後再試');
            return;
        }

        if (data.results && data.results.length > 0) {
            showSearchResults(data.results);
        } else {
            showNoResults();
        }
    } catch (error) {
        console.error('搜尋錯誤:', error);
        showSearchError('搜尋失敗，請檢查網路連線');
    }
}

function showSearchError(message) {
    searchDropdown.innerHTML = `
        <div class="search-error">
            <p>❌ ${message}</p>
        </div>
    `;
    searchDropdown.style.display = 'block';
}

function showSearchResults(results) {
    searchDropdown.innerHTML = '';

    results.forEach(movie => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `
            <div class="search-result-title">${movie.name}</div>
            <div class="search-result-meta">
                ${movie.originalName} | 上映日期: ${movie.releaseDate}
            </div>
        `;

        item.addEventListener('click', () => selectMovie(movie));
        searchDropdown.appendChild(item);
    });

    searchDropdown.style.display = 'block';
}

function showNoResults() {
    searchDropdown.innerHTML = `
        <div class="search-no-result">
            <p>查無電影</p>
            <p style="font-size: 0.875rem; margin-top: 8px;">請嘗試其他關鍵字</p>
        </div>
    `;
    searchDropdown.style.display = 'block';
}

function selectMovie(movie) {
    currentSelectedMovie = movie;

    // 隱藏搜尋下拉
    searchDropdown.style.display = 'none';
    searchInput.value = movie.name;

    // 顯示選中的電影資訊
    selectedMovieTitle.textContent = movie.name;
    movieBasicInfo.innerHTML = `
        <div><strong>原文片名：</strong>${movie.originalName || '-'}</div>
        <div><strong>上映日期：</strong>${movie.releaseDate || '-'}</div>
        <div><strong>片長：</strong>${movie.duration || '-'} 分鐘</div>
        <div><strong>分級：</strong>${movie.rating || '-'}</div>
    `;
    selectedMovieInfo.style.display = 'block';
}

// 清除選擇
clearSelection.addEventListener('click', () => {
    currentSelectedMovie = null;
    searchInput.value = '';
    selectedMovieInfo.style.display = 'none';
    searchDropdown.style.display = 'none';
});

// 新增一週
addWeekButton.addEventListener('click', () => {
    const tbody = document.getElementById('weekDataTable');
    const currentRows = tbody.querySelectorAll('tr');
    const nextWeek = currentRows.length + 1;

    const newRow = document.createElement('tr');
    newRow.setAttribute('data-week', nextWeek);
    newRow.innerHTML = `
        <td><input type="number" class="table-input integer-only" name="week" value="${nextWeek}" min="1"></td>
        <td><input type="number" class="table-input integer-only" name="boxoffice" placeholder="例: 12000000" min="0" step="1"></td>
        <td><input type="number" class="table-input integer-only" name="audience" placeholder="例: 40000" min="0" step="1"></td>
        <td><input type="number" class="table-input integer-only" name="screens" placeholder="例: 150" min="0" step="1"></td>
        <td><button class="btn btn-danger-dark btn-sm">X</button></td>
    `;

    // 綁定刪除事件
    const deleteBtn = newRow.querySelector('.btn');
    deleteBtn.addEventListener('click', () => deleteRow(newRow));

    // 綁定驗證事件
    bindIntegerValidation(newRow);

    tbody.appendChild(newRow);
    updateDeleteButtons();
});

// 刪除列
function deleteRow(row) {
    row.remove();
    updateDeleteButtons();
}

// 更新刪除按鈕狀態（第一列不可刪除）
function updateDeleteButtons() {
    const tbody = document.getElementById('weekDataTable');
    const rows = tbody.querySelectorAll('tr');

    rows.forEach((row, index) => {
        const deleteBtn = row.querySelector('.btn');
        if (deleteBtn && index === 0) {
            deleteBtn.classList.add('btn-disabled');
            deleteBtn.disabled = true;
        } else if (deleteBtn) {
            deleteBtn.classList.remove('btn-disabled');
            deleteBtn.disabled = false;
        }
    });
}

// 綁定整數驗證
function bindIntegerValidation(container) {
    const integerInputs = container.querySelectorAll('.integer-only');

    integerInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            // 只允許純數字
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
        });

        input.addEventListener('keydown', (e) => {
            // 禁止輸入小數點、負號、e
            if (e.key === '.' || e.key === '-' || e.key === 'e' || e.key === 'E') {
                e.preventDefault();
            }
        });
    });
}

// 初始化：綁定現有列的刪除和驗證
document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('weekDataTable');
    const rows = tbody.querySelectorAll('tr');

    rows.forEach((row) => {
        const deleteBtn = row.querySelector('.btn');
        if (deleteBtn && !deleteBtn.disabled) {
            deleteBtn.addEventListener('click', () => deleteRow(row));
        }

        bindIntegerValidation(row);
    });

    updateDeleteButtons();
});

// 表格驗證
function validateTableData() {
    const tbody = document.getElementById('weekDataTable');
    const rows = tbody.querySelectorAll('tr');
    const validationMessage = document.getElementById('validationMessage');

    // 清除之前的驗證訊息
    validationMessage.textContent = '';
    validationMessage.style.display = 'none';

    // 檢查至少要有 2 週資料
    if (rows.length < 2) {
        validationMessage.textContent = '⚠️ 至少需要 2 週的歷史資料';
        validationMessage.style.display = 'block';
        return false;
    }

    // 檢查每一列的必填欄位
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const boxofficeInput = row.querySelector('input[name="boxoffice"]');

        if (!boxofficeInput || !boxofficeInput.value || boxofficeInput.value.trim() === '') {
            validationMessage.textContent = `⚠️ 第 ${i + 1} 週的票房為必填欄位`;
            validationMessage.style.display = 'block';
            boxofficeInput.focus();
            return false;
        }

        // 檢查票房是否為正數
        const boxoffice = parseInt(boxofficeInput.value);
        if (boxoffice <= 0) {
            validationMessage.textContent = `⚠️ 第 ${i + 1} 週的票房必須大於 0`;
            validationMessage.style.display = 'block';
            boxofficeInput.focus();
            return false;
        }
    }

    return true;
}

// 收集表格資料
function collectTableData() {
    const tbody = document.getElementById('weekDataTable');
    const rows = tbody.querySelectorAll('tr');
    const weekData = [];

    rows.forEach((row, index) => {
        const weekInput = row.querySelector('input[name="week"]');
        const boxofficeInput = row.querySelector('input[name="boxoffice"]');
        const audienceInput = row.querySelector('input[name="audience"]');
        const screensInput = row.querySelector('input[name="screens"]');

        weekData.push({
            week: parseInt(weekInput.value) || (index + 1),
            boxoffice: parseInt(boxofficeInput.value) || 0,
            audience: parseInt(audienceInput.value) || 0,
            screens: parseInt(screensInput.value) || 0
        });
    });

    return weekData;
}

// 全域變數儲存預測結果
let currentPredictionResult = null;

// 開始預測
predictButton.addEventListener('click', async () => {
    // 驗證表格資料
    if (!validateTableData()) {
        return;
    }

    // 收集表格資料
    const weekData = collectTableData();

    // 準備電影資訊
    const movieInfo = currentSelectedMovie ? {
        name: currentSelectedMovie.name,
        release_date: currentSelectedMovie.releaseDate || new Date().toISOString().split('T')[0],
        film_length: currentSelectedMovie.film_length || currentSelectedMovie.duration || 120,
        is_restricted: currentSelectedMovie.is_restricted || 0
    } : {
        name: '未知電影',
        release_date: new Date().toISOString().split('T')[0],
        film_length: 120,
        is_restricted: 0
    };

    // 取得預測週數
    const modelSelect = document.getElementById('modelSelect');
    const predictWeeks = 3; // 預設預測 3 週

    // 顯示載入中
    predictButton.textContent = '預測中...';
    predictButton.disabled = true;

    try {
        // 呼叫預測 API
        const response = await fetch('/api/predict-new', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                week_data: weekData,
                movie_info: movieInfo,
                predict_weeks: predictWeeks
            })
        });

        const result = await response.json();

        if (!result.success) {
            alert(`預測失敗: ${result.message || result.error}`);
            return;
        }

        // 儲存預測結果
        currentPredictionResult = result;

        // 顯示預測結果
        displayPredictionResults(result);

    } catch (error) {
        console.error('預測錯誤:', error);
        alert('預測失敗，請檢查網路連線');
    } finally {
        predictButton.textContent = '開始預測';
        predictButton.disabled = false;
    }
});

// 顯示預測結果
function displayPredictionResults(result) {
    const predictionResults = document.getElementById('predictionResults');
    const predictionTableBody = document.getElementById('predictionTableBody');

    // 清空舊資料
    predictionTableBody.innerHTML = '';

    // 顯示歷史資料
    result.history.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>第 ${item.week} 週</td>
            <td><span class="badge badge-success">實際</span></td>
            <td>${formatCurrency(item.boxoffice)}</td>
            <td>${formatNumber(item.audience)}</td>
            <td>${item.screens || '-'}</td>
            <td>-</td>
            <td>-</td>
        `;
        predictionTableBody.appendChild(row);
    });

    // 顯示預測資料
    result.predictions.forEach(item => {
        const row = document.createElement('tr');
        const declineColor = item.decline_rate < -0.3 ? 'danger' : (item.decline_rate < -0.15 ? 'warning' : 'success');
        const warningBadge = result.warnings.find(w => w.week === item.week) ?
            `<span class="badge badge-danger">⚠️</span>` : '-';

        row.innerHTML = `
            <td>第 ${item.week} 週</td>
            <td><span class="badge badge-primary">預測</span></td>
            <td>${formatCurrency(item.boxoffice)}</td>
            <td>${formatNumber(item.audience)}</td>
            <td>${item.screens || '-'}</td>
            <td><span class="badge badge-${declineColor}">${formatPercentage(item.decline_rate)}</span></td>
            <td>${warningBadge}</td>
        `;
        predictionTableBody.appendChild(row);
    });

    // 顯示結果區塊
    predictionResults.style.display = 'block';

    // 捲動到結果
    predictionResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// 格式化函數
function formatCurrency(value) {
    return new Intl.NumberFormat('zh-TW', {
        style: 'currency',
        currency: 'TWD',
        minimumFractionDigits: 0
    }).format(value);
}

function formatNumber(value) {
    return new Intl.NumberFormat('zh-TW').format(value);
}

function formatPercentage(value) {
    return new Intl.NumberFormat('zh-TW', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(value);
}

// 匯出功能
document.getElementById('exportExcel').addEventListener('click', () => {
    exportPrediction('excel');
});

document.getElementById('exportCSV').addEventListener('click', () => {
    exportPrediction('csv');
});

async function exportPrediction(format) {
    if (!currentPredictionResult) {
        alert('請先進行預測');
        return;
    }

    try {
        const response = await fetch('/api/predict-new/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prediction_result: currentPredictionResult,
                format: format
            })
        });

        if (!response.ok) {
            throw new Error('匯出失敗');
        }

        // 下載檔案
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `prediction_${new Date().getTime()}.${format === 'excel' ? 'xlsx' : 'csv'}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

    } catch (error) {
        console.error('匯出錯誤:', error);
        alert('匯出失敗，請稍後再試');
    }
}

// 點擊外部關閉下拉選單
document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) &&
        !searchDropdown.contains(e.target) &&
        !searchButton.contains(e.target)) {
        searchDropdown.style.display = 'none';
    }
});
