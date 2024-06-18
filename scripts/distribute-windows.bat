@echo off

cd /d "%~dp0.."

# You'd have to install `pyinstaller` before running this script.
pyinstaller --onefile --name pixstudio main.py

rem Pause the script to keep the console window open (optional).
pause