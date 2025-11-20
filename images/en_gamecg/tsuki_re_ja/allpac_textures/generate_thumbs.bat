@echo off
chcp 65001
if not exist thumb md thumb
for %%I in (*.png) do (
	echo Processing: %%~nxI
	magick "%%I" -resize 16.69%% "thumb\%%~nxI"
)
pause
