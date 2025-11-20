@echo off
chcp 65001
rd /s/q build
rd /s/q dist
python -m venv retime_env
call retime_env\Scripts\activate
python.exe -m pip install --upgrade pip
pip install pyinstaller
pyinstaller --onefile retime_msad_audio.py
move /y "%~dp0dist\*" "%~dp0"
pause