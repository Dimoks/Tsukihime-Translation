@echo off
chcp 65001

echo Adding binary archives to build
xcopy "raw\*.bin" "build\" /y/q

xcopy "retimed\*.txt" "patched\\" /y/q

echo Apply tweaks

set TARGET=patched
for %%I in (.) do set "WORKDIR=%%~nxI"
git rev-parse --is-insive-work-tree >nul 2>&1 && set "TARGET=%WORKDIR%/patched"

for %%F in ("manual_tweaks\*") do (
    git apply --directory="%TARGET%" -p0 -v "%%F"
)

echo Merge strings of patched files to build
powershell -c "gci 'patched' '*.txt' | %% { (gc $_.FullName -Raw) -Replace '\n', '' | sc (\"build\\\" + $_.Name) -NoNewline }"

mangetsu_tools.exe -mxc -mxi -p "build\*.txt"
echo Finished compressing script files

echo Packing final mrg file
mangetsu_tools.exe -mzp -a "allscr_repacked.mrg" -p "build"
pause
