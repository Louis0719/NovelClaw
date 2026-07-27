@echo off
chcp 65001 >nul
echo ========================================
echo   来财AI客服 - 启动程序
echo ========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python！
    echo 请先安装 Python 3.9+ 
    echo 下载: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

:: 安装依赖
echo [1/3] 检查依赖...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装Flask（首次）...
    pip install flask -q
)

:: 启动
echo [2/3] 启动AI客服...
cd /d "%~dp0"
echo.
echo 浏览器即将自动打开 http://localhost:5188
echo 如果没有打开，请手动复制上面地址到浏览器
echo 按 Ctrl+C 可停止服务
echo.
python system\web.py
