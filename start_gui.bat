@echo off
REM Quick launcher for MD to Qdrant Importer
REM Double-click this file to run the GUI

title MD to Qdrant Importer

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo Configuration file not found!
    echo Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

REM Launch the GUI
echo Starting MD to Qdrant Importer GUI...
echo.
python gui.py

REM If GUI exits with error
if %errorlevel% neq 0 (
    echo.
    echo GUI exited with error code %errorlevel%
    echo.
    echo Try running from command line to see detailed errors:
    echo   1. Open Command Prompt
    echo   2. cd to this directory
    echo   3. Run: venv\Scripts\activate.bat
    echo   4. Run: python gui.py
    echo.
    pause
)
