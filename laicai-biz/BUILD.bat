@echo off
chcp 65001 >nul
echo ========================================
echo   来财AI客服 - 一键打包EXE
echo ========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装Python！
    echo 请先下载安装 Python 3.9+ 
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [错误] pip未安装
    pause
    exit /b 1
)

echo [1/4] 安装依赖...
pip install pyinstaller flask -q
if errorlevel 1 (
    echo [错误] 依赖安装失败，请以管理员身份运行
    pause
    exit /b 1
)

echo [2/4] 打包中（首次可能需要2-5分钟）...
cd /d "%~dp0"

:: 打包主程序（包含所有依赖）
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "来财AI客服" ^
    --add-data "system;system" ^
    --hidden-import=flask ^
    --hidden-import=werkzeug.serving ^
    --collect-all=flask ^
    system/web.py

if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo [3/4] 清理临时文件...
if exist build rmdir /s /q build
if exist __pycache__ rmdir /s /q __pycache__
if exist "system\__pycache__" rmdir /s /q "system\__pycache__"
if exist "system\agent\__pycache__" rmdir /s /q "system\agent\__pycache__"
if exist "system\tools\__pycache__" rmdir /s /q "system\tools\__pycache__"
if exist "system\db\__pycache__" rmdir /s /q "system\db\__pycache__"

echo [4/4] 完成！
echo.
echo ========================================
echo   打包成功！
echo ========================================
echo.
echo EXE文件位置: dist\来财AI客服.exe
echo.
echo 使用方法:
echo   1. 双击 来财AI客服.exe
echo   2. 浏览器自动打开 http://localhost:5188
echo   3. 开始使用AI客服
echo.
echo 首次使用请先导入产品资料（详见 README.md）
echo.
pause
