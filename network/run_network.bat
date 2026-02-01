@echo off
REM Switch to the script directory
cd /d "%~dp0"

REM Add Scripts directory to PATH temporarily
set PATH=%~dp0python_runtime\Scripts;%PATH%

REM Check if Python runtime exists
if not exist "python_runtime\python.exe" (
    echo ERROR: python_runtime\python.exe not found!
    pause
    exit /b 1
)

REM Check if launch.py exists
if not exist "launch.py" (
    echo ERROR: launch.py not found!
    pause
    exit /b 1
)

REM Create logs directory
if not exist "logs" mkdir logs

REM Start the program
echo Starting Travel Guide Network...
"python_runtime\python.exe" launch.py all

REM Pause if error occurs
if errorlevel 1 (
    echo.
    echo Program exited with error.
    pause
)
