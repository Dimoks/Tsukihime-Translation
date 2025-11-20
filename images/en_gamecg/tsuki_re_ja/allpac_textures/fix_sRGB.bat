@echo off
chcp 65001
for %%I in (*.png) do (
	echo Processing: %%~nxI
	magick "%%I" -set colorspace sRGB "%%~nxI"
)
pause
