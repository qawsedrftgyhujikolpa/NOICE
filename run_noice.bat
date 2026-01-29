@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo --------------------------------------------------
echo NOICE - The Digital Void Launcher
echo --------------------------------------------------
echo マシンリソースをしばき倒す準備をしています...
echo.

:: Anaconda/Pythonのパス設定
set PATH=C:\Users\tanak\anaconda3;C:\Users\tanak\anaconda3\Scripts;C:\Users\tanak\anaconda3\Library\bin;%PATH%

:: 依存関係のチェック（静かに実行）
py -m pip install fastapi uvicorn opencv-python numpy python-multipart moviepy >nul 2>&1

echo [STATUS] 虚無エンジンが起動しました
echo [LINK]   ブラウザで http://127.0.0.1:8000 を開いてください
echo.
echo * このウィンドウを閉じるとプログラムが終了します
echo.

:: 自動でブラウザを開く（おまけ）
start http://127.0.0.1:8000

py server.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] 起動に失敗しました。GPU が恥ずかしがっているかもしれません。
    pause
)

endlocal
