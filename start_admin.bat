@echo off
echo Starting Jujing Admin System...

:: Start Backend
cd /d "%~dp0backend"
start "Backend Server" python app.py

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start Frontend
cd /d "%~dp0admin"
start "Frontend Dev Server" npm run dev

echo.
echo Admin System is starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo.
pause
