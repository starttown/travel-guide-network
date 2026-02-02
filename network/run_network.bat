@echo off
cd /d "%~dp0"
python.exe launch.py all
if errorlevel 1 pause
