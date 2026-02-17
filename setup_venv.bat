@echo off
REM Setup script for local development with virtual environment (Windows)

echo Setting up NoxFeed development environment...

REM Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    exit /b 1
)

REM Check if venv exists
if exist venv (
    echo Virtual environment already exists at venv
    set /p recreate="Do you want to recreate it? (y/N): "
    if /i "%recreate%"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q venv
    ) else (
        echo Skipping venv creation.
        exit /b 0
    )
)

REM Create virtual environment
echo Creating virtual environment at venv...
python -m venv venv

REM Activate venv and install dependencies
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

if exist requirements.txt (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
) else (
    echo Warning: requirements.txt not found.
)

echo.
echo Setup complete!
echo.
echo To activate the virtual environment:
echo   venv\Scripts\activate
echo.
echo To run the application:
echo   python noxfeed.py
echo.
echo To deactivate the virtual environment:
echo   deactivate
echo.

pause
