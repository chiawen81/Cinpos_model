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
const downloadPreprocessedButton = document.getElementById('downloadPreprocessedButton');
const cleanDataButton = document.getElementById('cleanDataButton');

// 當前選中的電影
let currentSelectedMovie = null;

// 搜尋防抖計時器
let searchTimeout = null;

// 儲存原始週次資料（用於重新清洗）
let originalWeekData = null;

// 儲存清洗報告
let lastCleaningReport = null;

// 格式化日期函數（補零）
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');  // 月份補零
    const day = String(date.getDate()).padStart(2, '0');          // 日期補零
    return `${year}-${month}-${day}`;
}

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

async function selectMovie(movie) {
    currentSelectedMovie = movie;

    // 隱藏搜尋下拉
    searchDropdown.style.display = 'none';
    searchInput.value = movie.name;

    // 顯示載入中
    selectedMovieTitle.textContent = movie.name;
    movieBasicInfo.innerHTML = '<div>載入中...</div>';
    selectedMovieInfo.style.display = 'block';

    try {
        // 呼叫後端 API 取得電影詳細資料
        const response = await fetch(`/api/movie-detail/${movie.movieId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        const result = await response.json();

        if (!result.success) {
            // 若無法取得詳細資料，使用搜尋結果的基本資料
            updateMovieBasicInfo(movie, null);
            return;
        }

        const movieDetail = result.data;

        // 更新電影基本資訊（包含片長和分級）
        updateMovieBasicInfo(movie, movieDetail);

        // 預帶週次表格資料
        if (movieDetail.weeks && movieDetail.weeks.length > 0) {
            // 先帶入原始資料
            populateWeekData(movieDetail.weeks);

            // 自動執行資料清洗
            if (movie.releaseDate) {
                // 備份原始資料
                originalWeekData = JSON.parse(JSON.stringify(movieDetail.weeks));

                // 執行清洗
                const { cleanedData, report } = cleanWeekData(movieDetail.weeks, movie.releaseDate);

                // 儲存清洗報告
                lastCleaningReport = report;

                // 更新表格為清洗後的資料
                populateWeekData(cleanedData);

                // 重新計算首週指標
                recalculateFirstWeekMetrics(cleanedData);

                // 顯示清洗報告
                showCleaningReport(report);
            }
        }

    } catch (error) {
        console.error('取得電影詳細資料錯誤:', error);
        // 發生錯誤時使用搜尋結果的基本資料
        updateMovieBasicInfo(movie, null);
    }
}

// 更新電影基本資訊
function updateMovieBasicInfo(movie, movieDetail) {
    // 計算片長（將秒轉換為分鐘）
    let filmLength = '-';
    if (movieDetail && movieDetail.filmLength) {
        filmLength = Math.round(movieDetail.filmLength / 60);
    } else if (movie.duration) {
        filmLength = movie.duration;
    }

    // 取得分級
    const rating = (movieDetail && movieDetail.rating) || movie.rating || '-';

    // 取得電影 ID
    const movieId = (movieDetail && movieDetail.movieId) || movie.movieId || '-';

    // 首週相關指標初始顯示為 "-"，等待資料清洗後由 recalculateFirstWeekMetrics() 更新
    // 這樣可以確保顯示的是清洗後的真實週次第一週的資料
    movieBasicInfo.innerHTML = `
        <div><strong>電影 ID：</strong>${movieId}</div>
        <div><strong>原文片名：</strong>${movie.originalName || '-'}</div>
        <div><strong>上映日期：</strong>${movie.releaseDate || '-'}</div>
        <div><strong>片長：</strong>${filmLength} 分鐘</div>
        <div><strong>分級：</strong>${rating}</div>
        <div><strong>首週放映天數：</strong>-</div>
        <div><strong>首週票房：</strong>-</div>
        <div><strong>首週日均票房：</strong>-</div>
    `;
}

// 重新計算首週指標（用於資料清洗後）
function recalculateFirstWeekMetrics(cleanedData) {
    if (!currentSelectedMovie || !cleanedData || cleanedData.length === 0) {
        return;
    }

    // 找到清洗後的第一週資料（week === 1）
    const firstWeek = cleanedData.find(w => w.week === 1);
    if (!firstWeek || !firstWeek.boxoffice) {
        return;
    }

    // 計算首週放映天數：從上映日到第一週結束日的天數
    let firstWeekDays = 7; // 預設 7 天

    if (firstWeek.date && currentSelectedMovie.releaseDate) {
        try {
            // 解析上映日
            const releaseDate = new Date(currentSelectedMovie.releaseDate);

            // 解析第一週結束日（格式: "2025-09-15~2025-09-21"）
            const dates = firstWeek.date.split('~');
            if (dates.length === 2) {
                const firstWeekEndDate = new Date(dates[1]);

                // 計算天數：從上映日到第一週結束日（包含起始日）
                const diffTime = firstWeekEndDate - releaseDate;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // +1 因為包含起始日

                if (diffDays > 0) {
                    firstWeekDays = diffDays;
                } else {
                    console.warn('首週結束日早於上映日，使用預設 7 天');
                }
            }
        } catch (e) {
            console.warn('無法解析首週日期範圍，使用預設 7 天', e);
        }
    }

    // 計算首週票房
    const firstWeekBoxoffice = formatCurrency(Math.round(firstWeek.boxoffice));

    // 計算日均票房
    const firstWeekDailyAvg = formatCurrency(Math.round(firstWeek.boxoffice / firstWeekDays));

    // 更新顯示中的首週指標
    const currentHTML = movieBasicInfo.innerHTML;
    const updatedHTML = currentHTML
        .replace(/(<div><strong>首週放映天數：<\/strong>).*?(<\/div>)/, `$1${firstWeekDays} 天$2`)
        .replace(/(<div><strong>首週票房：<\/strong>).*?(<\/div>)/, `$1${firstWeekBoxoffice}$2`)
        .replace(/(<div><strong>首週日均票房：<\/strong>).*?(<\/div>)/, `$1${firstWeekDailyAvg}$2`);

    movieBasicInfo.innerHTML = updatedHTML;
}

// 預帶週次表格資料
function populateWeekData(weeks) {
    const tbody = document.getElementById('weekDataTable');

    // 清空現有的表格資料
    tbody.innerHTML = '';

    // 填入週次資料（顯示全部資料）
    const displayWeeks = weeks;

    displayWeeks.forEach((weekData, index) => {
        const weekNumber = weekData.week || index + 1;  // 使用資料中的 week，或 index + 1
        const newRow = document.createElement('tr');
        newRow.setAttribute('data-week', weekNumber);

        // 支援兩種資料格式：
        // 1. API 格式：{amount, tickets, theaterCount}
        // 2. 清洗後格式：{boxoffice, audience, screens, week, activeWeek}
        const boxoffice = weekData.boxoffice || weekData.amount || 0;
        const audience = weekData.audience || weekData.tickets || 0;
        const screens = weekData.screens || weekData.theaterCount || 0;

        // 活躍週次：從清洗後的資料讀取，如果沒有則自動計算
        let activeWeekDisplay = '-';
        if (weekData.activeWeek !== undefined && weekData.activeWeek !== null) {
            activeWeekDisplay = weekData.activeWeek;
        } else if (boxoffice > 0) {
            // 如果是 API 資料（還沒清洗），且票房 > 0，暫時顯示 "-" 等待清洗
            activeWeekDisplay = '-';
        }

        // 日期範圍：從清洗後的資料讀取
        let dateDisplay = '-';
        if (weekData.dateRange) {
            dateDisplay = weekData.dateRange;
        } else if (weekData.date) {
            // 如果是 API 格式的 date (格式: "2025-09-15~2025-09-21")，轉換為顯示格式
            try {
                const dates = weekData.date.split('~');
                if (dates.length === 2) {
                    const startDate = new Date(dates[0]);
                    const endDate = new Date(dates[1]);
                    dateDisplay = `${formatDate(startDate)} - ${formatDate(endDate)}`;
                }
            } catch (e) {
                dateDisplay = '-';
            }
        }

        newRow.innerHTML = `
            <td><input type="number" class="table-input integer-only" name="week" value="${weekNumber}" min="1"></td>
            <td><span class="active-week-display">${activeWeekDisplay}</span></td>
            <td><span class="date-display">${dateDisplay}</span></td>
            <td><input type="number" class="table-input integer-only" name="boxoffice" placeholder="例: 12000000" value="${Math.round(boxoffice)}" min="0" step="1"></td>
            <td><input type="number" class="table-input integer-only" name="audience" placeholder="例: 40000" value="${Math.round(audience)}" min="0" step="1"></td>
            <td><input type="number" class="table-input integer-only" name="screens" placeholder="例: 150" value="${screens}" min="0" step="1"></td>
            <td><button class="btn btn-danger-dark btn-sm">刪除</button></td>
        `;

        // 綁定刪除事件
        const deleteBtn = newRow.querySelector('.btn');
        deleteBtn.addEventListener('click', () => deleteRow(newRow));

        // 綁定驗證事件
        bindIntegerValidation(newRow);

        tbody.appendChild(newRow);
    });

    // 更新刪除按鈕狀態
    updateDeleteButtons();
}

// 清除選擇
clearSelection.addEventListener('click', () => {
    currentSelectedMovie = null;
    searchInput.value = '';
    selectedMovieInfo.style.display = 'none';
    searchDropdown.style.display = 'none';

    // 重置表格為預設的 2 週空白資料
    const tbody = document.getElementById('weekDataTable');
    tbody.innerHTML = '';

    for (let i = 1; i <= 2; i++) {
        const newRow = document.createElement('tr');
        newRow.setAttribute('data-week', i);
        newRow.innerHTML = `
            <td><input type="number" class="table-input integer-only" name="week" value="${i}" min="1"></td>
            <td><span class="active-week-display">-</span></td>
            <td><span class="date-display">-</span></td>
            <td><input type="number" class="table-input integer-only" name="boxoffice" placeholder="例: 12000000" min="0" step="1"></td>
            <td><input type="number" class="table-input integer-only" name="audience" placeholder="例: 40000" min="0" step="1"></td>
            <td><input type="number" class="table-input integer-only" name="screens" placeholder="例: 150" min="0" step="1"></td>
            <td><button class="btn btn-danger-dark btn-sm">刪除</button></td>
        `;

        // 綁定刪除事件
        const deleteBtn = newRow.querySelector('.btn');
        deleteBtn.addEventListener('click', () => deleteRow(newRow));

        // 綁定驗證事件
        bindIntegerValidation(newRow);

        tbody.appendChild(newRow);
    }

    updateDeleteButtons();
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
        <td><span class="active-week-display">-</span></td>
        <td><span class="date-display">-</span></td>
        <td><input type="number" class="table-input integer-only" name="boxoffice" placeholder="例: 12000000" min="0" step="1"></td>
        <td><input type="number" class="table-input integer-only" name="audience" placeholder="例: 40000" min="0" step="1"></td>
        <td><input type="number" class="table-input integer-only" name="screens" placeholder="例: 150" min="0" step="1"></td>
        <td><button class="btn btn-danger-dark btn-sm">刪除</button></td>
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
        const weekInput = row.querySelector('input[name="week"]');
        const boxofficeInput = row.querySelector('input[name="boxoffice"]');
        const audienceInput = row.querySelector('input[name="audience"]');
        const screensInput = row.querySelector('input[name="screens"]');

        // 驗證週次
        if (!weekInput || !weekInput.value || weekInput.value.trim() === '') {
            validationMessage.textContent = `⚠️ 第 ${i + 1} 列的週次為必填欄位`;
            validationMessage.style.display = 'block';
            weekInput.focus();
            return false;
        }
        const week = parseInt(weekInput.value);
        if (week <= 0) {
            validationMessage.textContent = `⚠️ 第 ${i + 1} 列的週次必須大於 0`;
            validationMessage.style.display = 'block';
            weekInput.focus();
            return false;
        }

        // 驗證票房
        if (!boxofficeInput || !boxofficeInput.value || boxofficeInput.value.trim() === '') {
            validationMessage.textContent = `⚠️ 第 ${i + 1} 週的票房為必填欄位`;
            validationMessage.style.display = 'block';
            boxofficeInput.focus();
            return false;
        }
        const boxoffice = parseInt(boxofficeInput.value);
        if (boxoffice <= 0) {
            validationMessage.textContent = `⚠️ 第 ${i + 1} 週的票房必須大於 0`;
            validationMessage.style.display = 'block';
            boxofficeInput.focus();
            return false;
        }

        // 驗證觀影人次
        if (!audienceInput || !audienceInput.value || audienceInput.value.trim() === '') {
            validationMessage.textContent = `⚠️ 第 ${i + 1} 週的觀影人次為必填欄位`;
            validationMessage.style.display = 'block';
            audienceInput.focus();
            return false;
        }
        const audience = parseInt(audienceInput.value);
        if (audience <= 0) {
            validationMessage.textContent = `⚠️ 第 ${i + 1} 週的觀影人次必須大於 0`;
            validationMessage.style.display = 'block';
            audienceInput.focus();
            return false;
        }

        // 驗證院線數
        if (!screensInput || !screensInput.value || screensInput.value.trim() === '') {
            validationMessage.textContent = `⚠️ 第 ${i + 1} 週的院線數為必填欄位`;
            validationMessage.style.display = 'block';
            screensInput.focus();
            return false;
        }
        const screens = parseInt(screensInput.value);
        if (screens <= 0) {
            validationMessage.textContent = `⚠️ 第 ${i + 1} 週的院線數必須大於 0`;
            validationMessage.style.display = 'block';
            screensInput.focus();
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
        const dateDisplay = row.querySelector('.date-display');

        // 收集日期範圍（轉換格式：從 "YYYY-MM-DD - YYYY-MM-DD" 到 "YYYY-MM-DD~YYYY-MM-DD"）
        let weekRange = null;
        if (dateDisplay && dateDisplay.textContent && dateDisplay.textContent !== '-') {
            // 將 " - " 替換為 "~" 以符合後端期望的格式
            weekRange = dateDisplay.textContent.replace(' - ', '~');
        }

        weekData.push({
            week: parseInt(weekInput.value) || (index + 1),
            boxoffice: parseInt(boxofficeInput.value) || 0,
            audience: parseInt(audienceInput.value) || 0,
            screens: parseInt(screensInput.value) || 0,
            week_range: weekRange  // 新增：日期範圍（格式: "YYYY-MM-DD~YYYY-MM-DD"）
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

    // 檢查是否為非首輪電影
    if (lastCleaningReport && lastCleaningReport.isNonFirstRound) {
        const rangeText = lastCleaningReport.interruptedWeekRange
            ? `中斷週次範圍：第 ${lastCleaningReport.interruptedWeekRange.start}-${lastCleaningReport.interruptedWeekRange.end} 週\n`
            : '';
        alert(
            '⚠️ 檢測到非首輪電影\n\n' +
            rangeText +
            `連續 ${lastCleaningReport.maxConsecutiveZeros} 週票房為 0\n\n` +
            '由於訓練資料只包含首輪電影，模型無法對非首輪電影進行準確預測。\n' +
            '請選擇首輪電影進行預測。'
        );
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
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
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

/**
 * 資料清洗功能
 * 完全對齊 flatten_timeseries.py 的邏輯
 */
function cleanWeekData(weekData, releaseDate) {
    const report = {
        originalCount: weekData.length,
        missingData: {
            boxoffice: 0,
            audience: 0,
            screens: 0
        },
        removed: {
            beforeRelease: 0,
            interrupted: 0
        },
        finalCount: 0,
        isFirstRound: true,
        isNonFirstRound: false,
        maxConsecutiveZeros: 0,
        interruptedWeekRange: null
    };

    // 計算缺失值比例（基於原始資料）
    weekData.forEach(week => {
        const boxoffice = week.boxoffice || week.amount || 0;
        const audience = week.audience || week.tickets || 0;
        const screens = week.screens || week.theaterCount || 0;

        if (boxoffice === 0) report.missingData.boxoffice++;
        if (audience === 0) report.missingData.audience++;
        if (screens === 0) report.missingData.screens++;
    });

    // === Step 1: 過濾正式上映日之前的週次 ===
    let cleanedData = [];
    const releaseDateObj = new Date(releaseDate);

    weekData.forEach((week) => {
        // 取得週次結束日（從 date 欄位解析，格式: "2025-09-15~2025-09-21"）
        if (week.date) {
            try {
                const weekEnd = new Date(week.date.split('~')[1]);
                // 只保留週次結束日 >= 上映日的資料
                if (weekEnd >= releaseDateObj) {
                    cleanedData.push({
                        boxoffice: week.boxoffice || week.amount || 0,
                        audience: week.audience || week.tickets || 0,
                        screens: week.screens || week.theaterCount || 0,
                        date: week.date
                    });
                } else {
                    report.removed.beforeRelease++;
                }
            } catch (e) {
                // 無法解析日期，保留資料
                cleanedData.push({
                    boxoffice: week.boxoffice || week.amount || 0,
                    audience: week.audience || week.tickets || 0,
                    screens: week.screens || week.theaterCount || 0,
                    date: week.date
                });
            }
        } else {
            // 沒有 date 欄位，保留資料
            cleanedData.push({
                boxoffice: week.boxoffice || week.amount || 0,
                audience: week.audience || week.tickets || 0,
                screens: week.screens || week.theaterCount || 0
            });
        }
    });

    // === Step 2: 計算連續零票房週次（zero_streak）===
    const zeroStreaks = [];
    let currentStreak = 0;

    cleanedData.forEach((week) => {
        if (week.boxoffice === 0) {
            currentStreak++;
        } else {
            currentStreak = 0;
        }
        zeroStreaks.push(currentStreak);
    });

    // 標記哪些 row 屬於輪次（in_round）
    // 規則：連續第 3 週（含）以上零票房 → 不屬於任何輪次
    const inRound = zeroStreaks.map(streak => streak < 3);

    // 檢測最大連續零票房週次
    report.maxConsecutiveZeros = Math.max(...zeroStreaks);

    // 如果有連續 3 週以上零票房，標記為非首輪
    if (report.maxConsecutiveZeros >= 3) {
        report.isNonFirstRound = true;
        report.isFirstRound = false;

        // 找出中斷週次範圍（第一個連續 3 週零票房的區間）
        let start = -1, end = -1;
        for (let i = 0; i < zeroStreaks.length; i++) {
            if (zeroStreaks[i] === 3 && start === -1) {
                // 連續第 3 週，往回推算起始位置
                start = i - 2 + 1; // +1 因為週次從 1 開始
                end = i + 1;
            }
            // 延續中斷區間
            if (zeroStreaks[i] > 3 && start !== -1) {
                end = i + 1;
            }
            // 中斷結束
            if (zeroStreaks[i] === 0 && start !== -1) {
                break;
            }
        }

        if (start !== -1 && end !== -1) {
            report.interruptedWeekRange = { start, end };
        }
    }

    // === Step 3: 過濾不在輪次內的 row ===
    const beforeStep3Count = cleanedData.length;
    cleanedData = cleanedData.filter((week, index) => inRound[index]);
    const removedInStep3 = beforeStep3Count - cleanedData.length;

    // === Step 4: 移除輪次末尾票房 = 0 的週次 ===
    let lastNonZeroIndex = -1;
    for (let i = cleanedData.length - 1; i >= 0; i--) {
        if (cleanedData[i].boxoffice > 0) {
            lastNonZeroIndex = i;
            break;
        }
    }

    if (lastNonZeroIndex !== -1 && lastNonZeroIndex < cleanedData.length - 1) {
        const removedCount = cleanedData.length - lastNonZeroIndex - 1;
        report.removed.interrupted = removedInStep3 + removedCount;
        cleanedData = cleanedData.slice(0, lastNonZeroIndex + 1);
    } else {
        report.removed.interrupted = removedInStep3;
    }

    // === Step 5: 重新編號週次（真實週次 + 活躍週次 + 日期範圍）===

    // 找出第一週的日期範圍，作為基準
    let firstWeekStartDate = null;
    if (cleanedData.length > 0 && cleanedData[0].date) {
        try {
            const firstWeekDateStr = cleanedData[0].date.split('~')[0];
            firstWeekStartDate = new Date(firstWeekDateStr);
        } catch (e) {
            console.warn('無法解析第一週日期，將無法計算日期範圍');
        }
    }

    let activeWeekCounter = 0;
    cleanedData = cleanedData.map((week, index) => {
        // 真實週次：所有週次連續編號（包含票房=0的週次）
        const realWeek = index + 1;

        // 活躍週次：只對票房>0的週次編號
        let activeWeek = null;
        if (week.boxoffice > 0) {
            activeWeekCounter++;
            activeWeek = activeWeekCounter;
        }

        // 計算日期範圍（基於第一週的起始日期）
        let dateRange = week.date || null;  // 保留原有的 date（如果有的話）
        if (firstWeekStartDate && realWeek > 1) {
            // 推算該週的日期範圍
            // 第 N 週的起始日 = 第一週起始日 + (N-1) * 7 天
            const weekStartDate = new Date(firstWeekStartDate);
            weekStartDate.setDate(firstWeekStartDate.getDate() + (realWeek - 1) * 7);

            // 第 N 週的結束日 = 起始日 + 6 天
            const weekEndDate = new Date(weekStartDate);
            weekEndDate.setDate(weekStartDate.getDate() + 6);

            // 格式化日期（YYYY-MM-DD）
            dateRange = `${formatDate(weekStartDate)} - ${formatDate(weekEndDate)}`;
        } else if (firstWeekStartDate && realWeek === 1 && week.date) {
            // 第一週使用原始的 date，但重新格式化為 "YYYY-MM-DD - YYYY-MM-DD"
            try {
                const dates = week.date.split('~');
                if (dates.length === 2) {
                    const startDate = new Date(dates[0]);
                    const endDate = new Date(dates[1]);
                    dateRange = `${formatDate(startDate)} - ${formatDate(endDate)}`;
                }
            } catch (e) {
                // 保持原始格式
            }
        }

        return {
            ...week,
            week: realWeek,           // 真實週次
            activeWeek: activeWeek,   // 活躍週次（可能為 null）
            dateRange: dateRange      // 日期範圍（格式: "YYYY-M-D - YYYY-M-D"）
        };
    });

    report.finalCount = cleanedData.length;

    return {
        cleanedData,
        report
    };
}

// 顯示清洗報告
function showCleaningReport(report) {
    const missingBoxoffice = ((report.missingData.boxoffice / report.originalCount) * 100).toFixed(1);
    const missingAudience = ((report.missingData.audience / report.originalCount) * 100).toFixed(1);
    const missingScreens = ((report.missingData.screens / report.originalCount) * 100).toFixed(1);

    let reportHtml = `
<div class="cleaning-report">
    <h3>資料清洗報告</h3>
    <div class="report-divider"></div>

    <div class="report-section mb-2">
        <strong>原始資料：</strong>${report.originalCount} 筆
    </div>

    <div class="report-section mb-2">
        <strong>缺失值比例：</strong>
        <div class="report-item">- 票房：${missingBoxoffice}% (${report.missingData.boxoffice}筆)</div>
        <div class="report-item">- 觀影人次：${missingAudience}% (${report.missingData.audience}筆)</div>
        <div class="report-item">- 院線數：${missingScreens}% (${report.missingData.screens}筆)</div>
    </div>

    <div class="report-section mb-2">
        <strong>移除資料：</strong>
        <div class="report-item">- 上映日前的週次：${report.removed.beforeRelease} 筆</div>
        <div class="report-item">- 中斷週次資料：${report.removed.interrupted} 筆</div>
    </div>

    <div class="report-section mb-2 text-brane-secondary ">
        <strong>最終資料：</strong>${report.finalCount} 筆
    </div>
    `;

    if (report.isNonFirstRound && report.interruptedWeekRange) {
        reportHtml += `
    <div class="report-divider"></div>
    <div class="report-warning mb-4">
        <strong class="text-danger-light">⚠️ 警告：此電影非首輪電影！</strong>
        <div class="report-item mt-1 ml-1">中斷週次範圍：第 ${report.interruptedWeekRange.start}-${report.interruptedWeekRange.end} 週</div>
        <div class="report-item ml-1">連續 ${report.maxConsecutiveZeros} 週票房為 0</div>
        <div class="report-item ml-1">無法進行預測</div>
    </div>`;
    }

    reportHtml += `</div>`;

    // 創建遮罩層
    const backdrop = document.createElement('div');
    backdrop.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #151515E5; z-index: 9999; backdrop-filter: blur(4px);';

    // 顯示報告（可以用 alert 或自訂 modal）
    const reportContainer = document.createElement('div');
    reportContainer.innerHTML = reportHtml;
    reportContainer.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 10000; background: #222222; color: #e0e0e0; padding: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);width: 400px;';

    // 關閉函數：同時移除遮罩和彈窗
    const closeModal = () => {
        document.body.removeChild(backdrop);
        document.body.removeChild(reportContainer);
    };

    const closeButton = document.createElement('button');
    closeButton.textContent = '關閉';
    closeButton.className = 'btn btn-secondary w-100';
    closeButton.style.marginTop = '20px';
    closeButton.onclick = closeModal;
    reportContainer.querySelector('.cleaning-report').appendChild(closeButton);

    // 點擊遮罩也能關閉
    backdrop.onclick = closeModal;

    document.body.appendChild(backdrop);
    document.body.appendChild(reportContainer);
}

// 點擊外部關閉下拉選單
document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) &&
        !searchDropdown.contains(e.target) &&
        !searchButton.contains(e.target)) {
        searchDropdown.style.display = 'none';
    }
});

// 下載票房資料
downloadPreprocessedButton.addEventListener('click', async () => {
    // 收集表格資料（不進行必填驗證）
    const weekData = collectTableData();

    // 檢查是否有資料
    if (weekData.length === 0) {
        alert('請先輸入週次資料');
        return;
    }

    // 檢查是否至少有 3 週資料
    if (weekData.length < 3) {
        alert('至少需要 3 週的資料才能生成預處理資料（從第 3 週開始計算特徵）');
        return;
    }

    // 準備電影資訊
    const movieInfo = currentSelectedMovie ? {
        gov_id: currentSelectedMovie.movieId || 'web_input',
        name: currentSelectedMovie.name,
        release_date: currentSelectedMovie.releaseDate || new Date().toISOString().split('T')[0],
        film_length: currentSelectedMovie.film_length || currentSelectedMovie.duration || 120,
        is_restricted: currentSelectedMovie.is_restricted || 0
    } : {
        gov_id: 'web_input',
        name: '未知電影',
        release_date: new Date().toISOString().split('T')[0],
        film_length: 120,
        is_restricted: 0
    };

    // 顯示載入中
    downloadPreprocessedButton.textContent = '下載中...';
    downloadPreprocessedButton.disabled = true;

    try {
        // 呼叫下載 API
        const response = await fetch('/api/predict-new/download-preprocessed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                week_data: weekData,
                movie_info: movieInfo
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '下載失敗');
        }

        // 下載檔案
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        // 從 response headers 取得檔案名稱，或使用預設名稱
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `preprocessed_${new Date().getTime()}.csv`;
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        console.log('票房資料下載成功');

    } catch (error) {
        console.error('下載票房資料錯誤:', error);
        alert(`下載失敗: ${error.message}`);
    } finally {
        downloadPreprocessedButton.textContent = '下載票房資料';
        downloadPreprocessedButton.disabled = false;
    }
});

// 資料清洗按鈕
cleanDataButton.addEventListener('click', () => {
    // 檢查是否有選擇電影
    if (!currentSelectedMovie || !currentSelectedMovie.releaseDate) {
        alert('請先選擇電影以取得上映日期');
        return;
    }

    // 收集當前表格資料
    const currentData = collectTableData();
    if (currentData.length === 0) {
        alert('表格中沒有資料可以清洗');
        return;
    }

    // 備份原始資料（首次清洗時）
    if (!originalWeekData) {
        originalWeekData = JSON.parse(JSON.stringify(currentData));
    }

    // 執行清洗
    const { cleanedData, report } = cleanWeekData(currentData, currentSelectedMovie.releaseDate);

    // 儲存清洗報告
    lastCleaningReport = report;

    // 更新表格資料
    populateWeekData(cleanedData);

    // 重新計算並更新首週指標
    recalculateFirstWeekMetrics(cleanedData);

    // 顯示清洗報告
    showCleaningReport(report);
});
