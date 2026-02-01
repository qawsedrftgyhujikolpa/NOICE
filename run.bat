@echo off
chcp 65001 >nul
cls
echo.
echo ===============================================================
echo    NOICE - The Digital Void
echo ===============================================================
echo.

py --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found
    echo Please install Python 3.10 or higher
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

if not exist uploads mkdir uploads
if not exist processed_videos mkdir processed_videos

echo [INFO] Installing dependencies...
py -m pip install --quiet --upgrade pip
py -m pip install --quiet fastapi uvicorn opencv-python numpy python-multipart moviepy

echo.
echo ===============================================================
echo    Starting server...
echo    Open http://127.0.0.1:8000 in your browser
echo ===============================================================
echo.

py server.py

echo.
echo Server stopped
pause
