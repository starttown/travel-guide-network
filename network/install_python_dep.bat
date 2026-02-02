@echo off
cd /d "%~dp0"
pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r requirements.txt
pause
