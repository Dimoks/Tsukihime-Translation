@echo off
chcp 65001 >nul
rd /s/q bntx_replace
rd /s/q build
rd /s/q dist
python -m venv replace_env
call replace_env\Scripts\activate
python.exe -m pip install --upgrade pip
pip install cython
pip install pyinstaller
pyinstaller bntx_replace.py --contents-directory bntx_replace
robocopy "dist\bntx_replace" "%cd%" /move /e /xj
pause