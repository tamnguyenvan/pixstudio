@echo off

cd /d "%~dp0.."

pyinstaller --noconsole --onefile --windowed --icon=icons/icon.ico --name pixstudio main.py

rem Pause the script to keep the console window open (optional).
pause