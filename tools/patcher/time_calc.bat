@echo off
setlocal enabledelayedexpansion

rem Parameters must be in quotes
set t1=%~1
set t2=%~2

set /a hours=%t2:~0,2%-%t1:~0,2%
set /a minutes=1%t2:~3,2%-1%t1:~3,2%
set /a seconds=1%t2:~6,2%-1%t1:~6,2%
set /a cs=1%t2:~9,2%-1%t1:~9,2%

if !cs! LSS 0 (
	set /a seconds-=1
	set /a cs+=1000
)
if !seconds! LSS 0 (
	set /a minutes-=1
	set /a seconds+=60
)
if !minutes! LSS 0 (
	set /a hours-=1
	set /a minutes+=60
)
if !hours! LSS 0 (
	set /a hours+=24
)

set "cs=0!cs!"
set "seconds=0!seconds!"
set "minutes=0!minutes!"

set t3=!hours!:!minutes:~-2!:!seconds:~-2!,!cs:~-2!
echo !t3!

endlocal
