@echo off
chcp 65001 >nul
cd /d "%~dp0system_files"
echo ========================================================
echo   🦊 AI搭載ショート動画切り抜きツール『きりぬきつーる』
echo   起動しています。しばらくお待ちください...
echo ========================================================

where uv >nul 2>nul
if %errorlevel% equ 0 (
    uv run --python 3.9 --with customtkinter --with opencv-python --with "moviepy<2.0.0" --with openai-whisper --with pillow src/main.py
    goto end
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    py src/main.py
    goto end
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python src/main.py
    goto end
)

echo.
echo [エラー] Pythonまたはuvが見つかりませんでした。
pause

:end
