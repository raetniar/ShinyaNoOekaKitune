cd /d "%~dp0"
uv run --python 3.9 --with customtkinter --with opencv-python --with "moviepy<2.0.0" --with openai-whisper --with pillow src/main.py
pause