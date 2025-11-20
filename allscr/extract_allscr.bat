@echo off
chcp 65001
set "allscr=allscr.mrg"
mangetsu_tools.exe -mze -a %allscr% -p decompressed

REM We move the binary archives to the raw directory
if not exist "raw" md "raw"
move /y "decompressed\allscr\allscr.mrg_0000.bin" "raw"
move /y "decompressed\allscr\allscr.mrg_0001.bin" "raw"
move /y "decompressed\allscr\allscr.mrg_0002.bin" "raw"

setlocal enabledelayedexpansion
for %%I in ("raw\*.bin") do (
    set par=
    set head=
    set /p head=<"%%I"
    if defined head set "head=!head:~0,4!"
    echo %%~nxI !head!

    if /i "!head!"=="mrgd" (
        set "par=-mze -a "%%I" -p "mzp""
    ) else if /i "!head!"=="MZX0" (
        set "par=-mxd -mxi -a "%%I" -p "mzx\%%~dpnI.txt""
    )

    if defined par mangetsu_tools.exe !par!
)
endlocal

mangetsu_tools.exe -mxd -mxi -a "decompressed\allscr\*.bin" -p "decompressed"
rd /s/q decompressed\allscr

echo Split scripts into lines by commands
powershell -c "gci 'decompressed' *.raw | %% { (gc $_.FullName) -replace ';', \";`n\" | sc ($_.FullName -replace '\.raw$', '.txt') -NoNewline; ri $_.FullName -Force }"

echo Manually patching bad script lines
REM V1 quirks
set "inputFile=decompressed\allscr.mrg_0143.txt"
powershell -c "$text = gc '%inputFile%' -Raw; $text.Replace('_STCP)21,0);', '_STCP(21,0);') | sc '%inputFile%' -NoNewline"
set "inputFile=decompressed\allscr.mrg_0169.txt"
powershell -c "$text = gc '%inputFile%' -Raw; $text.Replace('_SEFD(5,,,`001:2000)();', '_SEFD(5,,,`001:2000);') | sc '%inputFile%' -NoNewline"
set "inputFile=decompressed\allscr.mrg_0369.txt"
powershell -c "$text = gc '%inputFile%' -Raw; $text.Replace('_MFAD(,,`001:8000,,`011:0)0);', '_MFAD(,,`001:8000,,`011:0);') | sc '%inputFile%' -NoNewline"
set "inputFile=decompressed\allscr.mrg_0495.txt"
powershell -c "$text = gc '%inputFile%' -Raw; $text.Replace('_STZ4(5,498,498,498,498,0,0,0)gb);', '_STZ4(5,498,498,498,498,0,0,0);') | sc '%inputFile%' -NoNewline"
REM V1.0.1 quirks
set "inputFile=decompressed\allscr.mrg_0010.txt"
powershell -c "$text = gc '%inputFile%' -Raw; $text.Replace('_STGS(0,,0,800,0)#);', '_STGS(0,,0,800,0);') | sc '%inputFile%' -NoNewline"
set "inputFile=decompressed\allscr.mrg_0347.txt"
powershell -c "$text = gc '%inputFile%' -Raw; $text.Replace('_SQK2(11,2,2,100,-1,0,0,0,0)+);', '_SQK2(11,2,2,100,-1,0,0,0,0);') | sc '%inputFile%' -NoNewline"
set "inputFile=decompressed\allscr.mrg_0459.txt"
powershell -c "$text = gc '%inputFile%' -Raw; $text.Replace('_STTR,0,26);', '_STTR(0,26);') | sc '%inputFile%' -NoNewline"
pause
