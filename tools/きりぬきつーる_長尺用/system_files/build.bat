@echo off
cd /d "%~dp0"
set PATH=C:\Users\A00151\AppData\Local\Python\pythoncore-3.14-64\Scripts;C:\Users\A00151\AppData\Local\Python\pythoncore-3.13-64\Scripts;C:\Users\A00151\AppData\Local\Python\pythoncore-3.12-64\Scripts;C:\Users\A00151\AppData\Local\Bin;C:\Users\A00151\AppData\Local\Programs\Python\Python314\Scripts;C:\Users\A00151\AppData\Local\Programs\Python\Python313\Scripts;C:\Users\A00151\AppData\Local\Programs\Python\Python312\Scripts;C:\Users\A00151\AppData\Local\Programs\Python\Python311\Scripts;%PATH%

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b %errorlevel%
)

echo.
echo Building executable with PyInstaller...
pyinstaller --noconsole --onedir --clean --name="きりぬきつーる_長尺用" --icon="icon.ico" --distpath="../dist" --workpath="../build" main.py
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b %errorlevel%
)

echo.
if exist "ffmpeg.exe" (
    echo Copying ffmpeg.exe to _internal folder...
    copy /y "ffmpeg.exe" "..\dist\きりぬきつーる_長尺用\_internal\"
)

echo.
echo Deploying files to root folder...
if exist "..\きりぬきつーる_長尺用.exe" del /f /q "..\きりぬきつーる_長尺用.exe"
if exist "..\_internal" rmdir /s /q "..\_internal"

move /y "..\dist\きりぬきつーる_長尺用\きりぬきつーる_長尺用.exe" "..\きりぬきつーる_長尺用.exe"
move /y "..\dist\きりぬきつーる_長尺用\_internal" "..\_internal"

echo.
echo Cleaning up temp build directories...
rmdir /s /q "..\dist"
rmdir /s /q "..\build"
if exist "きりぬきつーる_長尺用.spec" del /f /q "きりぬきつーる_長尺用.spec"

echo.
echo Build and deployment completed successfully!
pause
