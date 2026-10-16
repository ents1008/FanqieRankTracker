@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
"D:\AI\confui\ComfyUI_windows_portable\ComfyUI\.ext\python.exe" "scripts\run_daily_update.py"
