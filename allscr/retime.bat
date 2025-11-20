@echo off
chcp 65001
if not exist retimed md retimed
python retime_msad_audio.py audio_stream.txt raw\allscr.mrg_0000.bin decompressed retimed
pause