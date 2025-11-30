#!/bin/bash
# 
# Flask 應用啟動腳本
# 說明: 使用 uv 管理套件並啟動 Flask 應用

echo "🎬 電影票房預測系統啟動中..."

# 檢查是否安裝 uv
if ! command -v uv &> /dev/null; then
    echo "❌ 錯誤: 未安裝 uv"
    echo "請先安裝 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 創建虛擬環境（如果不存在）
if [ ! -d ".venv" ]; then
    echo "📦 創建虛擬環境..."
    uv venv
fi

# 安裝依賴
echo "📦 安裝套件..."
uv pip install -r requirements.txt

# 設定環境變數
export FLASK_APP=app.py
export FLASK_DEBUG=true

# 啟動應用
echo "🚀 啟動 Flask 應用..."
echo "📌 訪問 http://localhost:5000 查看網站"
echo "按 Ctrl+C 停止服務"

uv run python app.py
