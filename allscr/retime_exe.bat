@echo off
chcp 65001
if not exist retimed md retimed
&~dp0retime_msad_audio.exe audio_stream.txt raw\allscr.mrg_0000.bin decompressed retimed
pause