/**
 * 預測頁面交互邏輯
 */

// 假資料：搜尋結果
const mockSearchData = {
    "test電影選項": {
        movieId: "99999",
        name: "test電影選項",
        originalName: "TEST MOVIE OPTION",
        releaseDate: "2025-01-01",
        duration: 120,
        rating: "普遍級"
    },
    "test查無電影": {
        movieId: null,
        name: "test查無電影",
        noResult: true
    }
};

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

// 搜尋功能
searchInput.addEventListener('input', handleSearchInput);
searchButton.addEventListener('click', performSearch);

function handleSearchInput(e) {
    const keyword = e.target.value.trim();

    if (keyword.length === 0) {
        searchDropdown.style.display = 'none';
        return;
    }

    // 模擬搜尋
    performSearch();
}

function performSearch() {
    const keyword = searchInput.value.trim();

    if (keyword.length === 0) {
        searchDropdown.style.display = 'none';
        return;
    }

    // 檢查假資料
    if (mockSearchData[keyword]) {
        const movie = mockSearchData[keyword];

        if (movie.noResult) {
            showNoResults();
        } else {
            showSearchResults([movie]);
        }
    } else {
        // 實際環境應該呼叫 API
        // 這裡顯示空結果
        searchDropdown.innerHTML = '';
        searchDropdown.style.display = 'none';
    }
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

// 開始預測
predictButton.addEventListener('click', () => {
    // TODO: 實作預測邏輯
    alert('預測功能將在後續實作');
});

// 點擊外部關閉下拉選單
document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) &&
        !searchDropdown.contains(e.target) &&
        !searchButton.contains(e.target)) {
        searchDropdown.style.display = 'none';
    }
});
