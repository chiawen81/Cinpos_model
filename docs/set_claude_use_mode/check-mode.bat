@echo off
chcp 65001 >nul
echo.
echo ========================================
echo        檢查 Claude Code 當前模式
echo ========================================
echo.
if defined ANTHROPIC_API_KEY (
    echo [✓] 當前使用：API Key 模式
    echo [ℹ] API Key 前綴：%ANTHROPIC_API_KEY:~0,20%...
) else (
    echo [✓] 當前使用：訂閱身分模式
)
echo.
echo ========================================
echo.