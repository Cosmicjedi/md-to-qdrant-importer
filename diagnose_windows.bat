@echo off
REM Diagnostic script for md-to-qdrant-importer
REM Checks your environment and identifies issues

echo ============================================
echo MD to Qdrant Importer - Diagnostics
echo ============================================
echo.

echo [CHECK 1] Python Installation
echo ------------------------------
python --version 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python NOT found in PATH
    echo.
    echo FIX: Install Python from https://python.org
    echo      Make sure to check 'Add Python to PATH' during installation
    echo.
) else (
    echo ✅ Python is installed
    python --version
)
echo.

echo [CHECK 2] Virtual Environment
echo ------------------------------
if exist "venv\Scripts\python.exe" (
    echo ✅ Virtual environment exists
    venv\Scripts\python.exe --version
) else (
    echo ❌ Virtual environment NOT found or incomplete
    echo.
    echo FIX: Run emergency_setup.bat to create it
)
echo.

echo [CHECK 3] Activation Script
echo ------------------------------
if exist "venv\Scripts\activate.bat" (
    echo ✅ Activation script exists
) else (
    echo ❌ Activation script MISSING
    echo.
    echo FIX: Virtual environment is corrupted
    echo      Delete 'venv' folder and run emergency_setup.bat
)
echo.

echo [CHECK 4] Key Python Files
echo ------------------------------
if exist "import_processor.py" (
    echo ✅ import_processor.py exists
    python -m py_compile import_processor.py 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ import_processor.py has SYNTAX ERRORS
        echo.
        echo FIX: Download clean import_processor.py from artifacts
    ) else (
        echo ✅ import_processor.py is valid
    )
) else (
    echo ❌ import_processor.py MISSING
)
echo.

if exist "qdrant_handler.py" (
    echo ✅ qdrant_handler.py exists
) else (
    echo ❌ qdrant_handler.py MISSING
)
echo.

if exist "gui.py" (
    echo ✅ gui.py exists
) else (
    echo ❌ gui.py MISSING
)
echo.

if exist "config.py" (
    echo ✅ config.py exists
) else (
    echo ❌ config.py MISSING
)
echo.

echo [CHECK 5] Requirements
echo ------------------------------
if exist "requirements.txt" (
    echo ✅ requirements.txt exists
) else (
    echo ❌ requirements.txt MISSING
)
echo.

echo [CHECK 6] Environment File
echo ------------------------------
if exist ".env" (
    echo ✅ .env exists
) else (
    echo ⚠️  .env file MISSING
    echo    This is optional but recommended
)
echo.

echo ============================================
echo Diagnostic Summary
echo ============================================
echo.

REM Count issues
set ISSUES=0

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 set /a ISSUES+=1

if not exist "venv\Scripts\activate.bat" set /a ISSUES+=1
if not exist "import_processor.py" set /a ISSUES+=1
if not exist "gui.py" set /a ISSUES+=1

if %ISSUES%==0 (
    echo ✅ No critical issues found!
    echo.
    echo You should be able to run the GUI.
    echo Try: .\start_gui.bat
) else (
    echo ❌ Found %ISSUES% critical issue(s)
    echo.
    echo RECOMMENDED ACTION:
    echo   1. Download emergency_setup.bat
    echo   2. Run it to fix your environment
    echo   3. Download clean import_processor.py if needed
)
echo.

echo ============================================
echo.
pause
