@echo off
REM Emergency Fix Script for md-to-qdrant-importer
REM This script will:
REM 1. Check Python installation
REM 2. Create virtual environment if missing
REM 3. Install dependencies
REM 4. Verify the installation

echo ============================================
echo MD to Qdrant Importer - Emergency Setup
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo [1/5] Python found:
python --version
echo.

REM Check if venv directory exists
if exist "venv" (
    echo [2/5] Virtual environment directory found
) else (
    echo [2/5] Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create virtual environment
        echo Try: python -m pip install --upgrade pip
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment and install dependencies
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to activate virtual environment
    echo The venv\Scripts\activate.bat file is missing
    echo Recreating virtual environment...
    rmdir /s /q venv
    python -m venv venv
    call venv\Scripts\activate.bat
)
echo.

REM Upgrade pip
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo.

REM Install requirements
echo [5/5] Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt --quiet
    if %ERRORLEVEL% NEQ 0 (
        echo WARNING: Some packages failed to install
        echo Trying with verbose output...
        pip install -r requirements.txt
    )
) else (
    echo ERROR: requirements.txt not found
    echo Creating basic requirements.txt...
    (
        echo qdrant-client
        echo sentence-transformers
        echo python-dotenv
    ) > requirements.txt
    pip install -r requirements.txt
)
echo.

echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo To use the importer:
echo   1. Make sure this window stays open OR
echo   2. Run: venv\Scripts\activate.bat
echo   3. Then run: python gui.py
echo.
echo Virtual environment is now active in this window.
echo Type 'python gui.py' to start the GUI
echo.

cmd /k
