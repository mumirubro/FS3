@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   🚀 TOJI Platform v2.0 - Startup
echo ========================================
echo.

:: Get the directory where the batch file is located
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

echo [1/3] Starting Backend API...
start "TOJI Backend" cmd /k "cd backend && ..\.venv\Scripts\python main.py"
timeout /t 3 /nobreak >nul

echo [2/3] Starting Telegram Bot...
start "TOJI Bot" cmd /k "cd bot && ..\.venv\Scripts\python toji_bot.py"
timeout /t 2 /nobreak >nul

echo [3/3] Starting WebApp Frontend...
start "TOJI WebApp" cmd /k "cd webapp && python -m http.server 5173"

echo.
echo ========================================
echo   ✅ All services are now running!
echo ========================================
echo.
echo 🌐 Backend API:  http://localhost:8000/docs
echo 🖥️ WebApp UI:    http://localhost:5173
echo 🤖 Bot:          @TOJIchk_bot
echo.
echo Press any key to check service status...
pause >nul

:: Show active ports
echo Activity Check:
netstat -ano | findstr ":8000 :5173"

echo.
echo To stop everything, close the three opened windows.
pause
