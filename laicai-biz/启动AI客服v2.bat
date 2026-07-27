@echo off
chcp 65001 >nul
title 来财AI客服 v2.0
color 0A

echo ========================================
echo     来财AI客服系统 v2.0
echo     叠石桥面料行业智能助手
echo ========================================
echo.

cd /d "%~dp0system"

echo [1/3] 检查依赖...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [错误] 未安装 Flask，正在安装...
    pip install flask -q
)

echo [2/3] 启动Web服务...
echo.
echo  访问地址: http://localhost:5188
echo  按 Ctrl+C 停止服务
echo.
echo ----------------------------------------
python web_v2.py

pause
