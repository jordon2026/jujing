@echo off
chcp 65001 > nul
echo ========================================
echo       用户端启动脚本
echo ========================================
echo.

cd /d "%~dp0frontend"

echo [OK] 正在启动用户端服务器...
echo [>] 访问地址: http://localhost:5175
echo [*] 目录: %cd%
echo [x] 关闭窗口即可停止服务器
echo.
echo ========================================
echo.

python run_frontend.py

pause
