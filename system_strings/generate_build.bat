@echo off
chcp 65001
rd /s/q build
rd /s/q dist
python -m venv generate_env
call generate_env\Scripts\activate
python.exe -m pip install --upgrade pip
pip install pyinstaller
pyinstaller --onefile generate_readable.py
move /y "%~dp0dist\*" "%~dp0"
pause