@echo off
chcp 65001 >nul
set "bat_path=%~dp0"
set "log_file=%~dp0log.txt"
set t1=%time%
echo Start %~nx0 %date% %t1%>>"%log_file%"
REM patch_allpac.exe tsuki_re_ja allpac
python patch_allpac.py tsuki_re_ja allpac
set t2=%time%
echo End %~nx0 %date% %t2%>>"%log_file%"
for /F "usebackq" %%s in (`call "%bat_path%time_calc.bat" "%t1%" "%t2%"`) do (
	set delta=%%s
)
echo Work time %delta%>>"%log_file%"
echo ------------------------>>"%log_file%"
echo Work time %delta%
pause
