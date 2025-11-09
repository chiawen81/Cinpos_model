/**
 * 圖表相關功能
 * 說明: 使用 Plotly.js 繪製互動式圖表
 */

// ============= 圖表設定 =============
const chartConfig = {
    // 深色主題設定
    layout: {
        paper_bgcolor: '#2a2a2a',
        plot_bgcolor: '#1a1a1a',
        font: {
            color: '#FFFFFF'
        },
        xaxis: {
            gridcolor: 'rgba(218, 218, 255, 0.1)',
            zerolinecolor: 'rgba(218, 218, 255, 0.2)'
        },
        yaxis: {
            gridcolor: 'rgba(218, 218, 255, 0.1)',
            zerolinecolor: 'rgba(218, 218, 255, 0.2)'
        },
        margin: {
            t: 40,
            r: 20,
            b: 60,
            l: 80
        },
        showlegend: true,
        legend: {
            bgcolor: 'rgba(42, 42, 42, 0.8)',
            bordercolor: 'rgba(218, 218, 255, 0.2)',
            borderwidth: 1
        }
    },
    config: {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    }
};

// ============= 初始化圖表 =============
function initializeCharts() {
    const chartContainers = document.querySelectorAll('[data-chart]');
    
    chartContainers.forEach(container => {
        const chartType = container.getAttribute('data-chart');
        const chartData = JSON.parse(container.getAttribute('data-chart-data') || '{}');
        
        switch(chartType) {
            case 'boxoffice-trend':
                drawBoxOfficeTrendChart(container, chartData);
                break;
            case 'prediction-comparison':
                drawPredictionComparisonChart(container, chartData);
                break;
            case 'decline-rate':
                drawDeclineRateChart(container, chartData);
                break;
            default:
                console.warn(`Unknown chart type: ${chartType}`);
        }
    });
}

/**
 * 繪製票房趨勢圖
 * @param {HTMLElement} container - 圖表容器
 * @param {Object} data - 圖表資料
 */
function drawBoxOfficeTrendChart(container, data) {
    const history = data.history || [];
    const predictions = data.predictions || [];
    
    // 準備歷史資料
    const historyTrace = {
        x: history.map(d => `第${d.week}週`),
        y: history.map(d => d.boxoffice),
        name: '實際票房',
        type: 'scatter',
        mode: 'lines+markers',
        line: {
            color: '#71DDFF',
            width: 3
        },
        marker: {
            color: '#71DDFF',
            size: 8
        }
    };
    
    // 準備預測資料
    const predictionTrace = {
        x: predictions.map(d => `第${d.week}週`),
        y: predictions.map(d => d.boxoffice),
        name: '預測票房',
        type: 'scatter',
        mode: 'lines+markers',
        line: {
            color: '#9C6DFF',
            width: 3,
            dash: 'dash'
        },
        marker: {
            color: '#9C6DFF',
            size: 8
        }
    };
    
    // 信心區間
    const confidenceBand = {
        x: [...predictions.map(d => `第${d.week}週`), ...predictions.map(d => `第${d.week}週`).reverse()],
        y: [...predictions.map(d => d.confidence_upper), ...predictions.map(d => d.confidence_lower).reverse()],
        fill: 'toself',
        fillcolor: 'rgba(156, 109, 255, 0.2)',
        line: { color: 'transparent' },
        name: '信心區間',
        showlegend: true,
        type: 'scatter',
        mode: 'lines'
    };
    
    const layout = {
        ...chartConfig.layout,
        title: '票房趨勢與預測',
        xaxis: {
            ...chartConfig.layout.xaxis,
            title: '週次'
        },
        yaxis: {
            ...chartConfig.layout.yaxis,
            title: '票房 (NT$)',
            tickformat: ',.0f'
        }
    };
    
    Plotly.newPlot(container, [historyTrace, confidenceBand, predictionTrace], layout, chartConfig.config);
}

/**
 * 繪製預測比較圖
 * @param {HTMLElement} container - 圖表容器
 * @param {Object} data - 圖表資料
 */
function drawPredictionComparisonChart(container, data) {
    const weeks = data.weeks || [];
    const models = data.models || {};
    
    const traces = Object.keys(models).map((modelName, index) => {
        const colors = ['#71DDFF', '#9C6DFF', '#FF6B6B', '#51CF66'];
        return {
            x: weeks,
            y: models[modelName],
            name: modelName,
            type: 'bar',
            marker: {
                color: colors[index % colors.length]
            }
        };
    });
    
    const layout = {
        ...chartConfig.layout,
        title: '模型預測比較',
        barmode: 'group',
        xaxis: {
            ...chartConfig.layout.xaxis,
            title: '週次'
        },
        yaxis: {
            ...chartConfig.layout.yaxis,
            title: '預測票房 (NT$)',
            tickformat: ',.0f'
        }
    };
    
    Plotly.newPlot(container, traces, layout, chartConfig.config);
}

/**
 * 繪製衰退率圖表
 * @param {HTMLElement} container - 圖表容器
 * @param {Object} data - 圖表資料
 */
function drawDeclineRateChart(container, data) {
    const weeks = data.weeks || [];
    const declineRates = data.decline_rates || [];
    const avgDeclineRate = data.avg_decline_rate || 0;
    
    // 衰退率柱狀圖
    const barTrace = {
        x: weeks.map(w => `第${w}週`),
        y: declineRates.map(r => r * 100),
        type: 'bar',
        name: '週衰退率',
        marker: {
            color: declineRates.map(r => {
                if (r < -0.5) return '#FF4444';
                if (r < -0.3) return '#FFA500';
                if (r < -0.1) return '#FFDD00';
                return '#51CF66';
            })
        }
    };
    
    // 平均線
    const avgLine = {
        x: weeks.map(w => `第${w}週`),
        y: Array(weeks.length).fill(avgDeclineRate * 100),
        type: 'scatter',
        mode: 'lines',
        name: '平均衰退率',
        line: {
            color: '#DADAFF',
            width: 2,
            dash: 'dash'
        }
    };
    
    const layout = {
        ...chartConfig.layout,
        title: '票房衰退率分析',
        xaxis: {
            ...chartConfig.layout.xaxis,
            title: '週次'
        },
        yaxis: {
            ...chartConfig.layout.yaxis,
            title: '衰退率 (%)',
            tickformat: '.1f',
            ticksuffix: '%'
        },
        shapes: [
            {
                type: 'line',
                x0: 0,
                x1: 1,
                xref: 'paper',
                y0: -30,
                y1: -30,
                line: {
                    color: '#FFA500',
                    width: 1,
                    dash: 'dot'
                }
            }
        ],
        annotations: [
            {
                x: 0.98,
                y: -30,
                xref: 'paper',
                text: '警戒線 (-30%)',
                showarrow: false,
                font: {
                    color: '#FFA500',
                    size: 12
                },
                xanchor: 'right'
            }
        ]
    };
    
    Plotly.newPlot(container, [barTrace, avgLine], layout, chartConfig.config);
}

/**
 * 更新圖表資料
 * @param {string} chartId - 圖表ID
 * @param {Object} newData - 新資料
 */
function updateChart(chartId, newData) {
    const container = document.getElementById(chartId);
    if (!container) return;
    
    const chartType = container.getAttribute('data-chart');
    container.setAttribute('data-chart-data', JSON.stringify(newData));
    
    // 重新繪製圖表
    switch(chartType) {
        case 'boxoffice-trend':
            drawBoxOfficeTrendChart(container, newData);
            break;
        case 'prediction-comparison':
            drawPredictionComparisonChart(container, newData);
            break;
        case 'decline-rate':
            drawDeclineRateChart(container, newData);
            break;
    }
}

/**
 * 導出圖表為圖片
 * @param {string} chartId - 圖表ID
 * @param {string} format - 圖片格式 (png, svg, jpeg)
 */
function exportChart(chartId, format = 'png') {
    Plotly.downloadImage(chartId, {
        format: format,
        width: 1200,
        height: 600,
        filename: `chart_${new Date().getTime()}`
    });
}

// ============= 即時更新功能 =============
/**
 * 開始即時更新圖表
 * @param {string} govId - 政府代號
 * @param {number} interval - 更新間隔（毫秒）
 */
function startRealtimeUpdate(govId, interval = 60000) {
    setInterval(async () => {
        try {
            const response = await fetch(`/api/movie/${govId}/latest`);
            if (response.ok) {
                const data = await response.json();
                updateChart('boxoffice-trend-chart', data);
            }
        } catch (error) {
            console.error('Failed to update chart:', error);
        }
    }, interval);
}

// ============= 圖表互動功能 =============
/**
 * 添加圖表互動事件
 * @param {string} chartId - 圖表ID
 */
function addChartInteractions(chartId) {
    const container = document.getElementById(chartId);
    
    // 點擊事件
    container.on('plotly_click', function(data) {
        const point = data.points[0];
        console.log('Clicked point:', point);
        
        // 顯示詳細資訊
        showPointDetails(point);
    });
    
    // 懸停事件
    container.on('plotly_hover', function(data) {
        const point = data.points[0];
        // 可以在此添加自定義懸停效果
    });
}

/**
 * 顯示資料點詳細資訊
 * @param {Object} point - 資料點
 */
function showPointDetails(point) {
    const details = `
        週次: ${point.x}
        票房: ${formatCurrency(point.y)}
        類型: ${point.data.name}
    `;
    
    movieApp.showAlert('info', '詳細資訊', details);
}

// ============= 初始化 =============
// 覆寫 main.js 中的 placeholder
window.initializeCharts = initializeCharts;

// 導出功能
window.chartUtils = {
    updateChart,
    exportChart,
    startRealtimeUpdate,
    addChartInteractions
};
