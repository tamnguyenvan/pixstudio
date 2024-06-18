@echo off
rem You'd have to install `pyside6` before running this script.

cd /d "%~dp0.."
pyside6-rcc resources.qrc -o resources.py

rem Pause the script to keep the console window open (optional).
pause