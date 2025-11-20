@echo off
chcp 65001 >nul
rd /s/q build
rd /s/q dist
python -m venv patcher_env
call patcher_env\Scripts\activate
python.exe -m pip install --upgrade pip
pip install pyinstaller
pyinstaller --onefile patch_allpac.py
pyinstaller --onefile patch_allui.py
pyinstaller --onefile patch_parts.py
move /y "%~dp0dist\*" "%~dp0"
pause