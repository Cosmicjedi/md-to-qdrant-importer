@echo off
REM Diagnostic script for MD to Qdrant Importer
REM Run this if you're having setup issues

title MD to Qdrant Importer - Diagnostics

echo ============================================
echo MD to Qdrant Importer - Diagnostics
echo ============================================
echo.

REM Check Python
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%V in ('python --version') do echo [OK] %%V
) else (
    echo [ERROR] Python not found in PATH
    echo   Install Python from https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH" during installation
)
echo.

REM Check pip
echo [2/8] Checking pip...
python -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%V in ('python -m pip --version') do echo [OK] %%V
) else (
    echo [ERROR] pip not found
    echo   Run: python -m ensurepip --default-pip
)
echo.

REM Check virtual environment
echo [3/8] Checking virtual environment...
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment exists
    for /f "delims=" %%V in ('venv\Scripts\python.exe --version') do echo     %%V
) else (
    echo [WARNING] Virtual environment not found
    echo   Run setup.bat to create it
)
echo.

REM Check requirements.txt
echo [4/8] Checking requirements.txt...
if exist "requirements.txt" (
    echo [OK] requirements.txt found
    for /f %%A in ('type requirements.txt ^| find /c /v ""') do echo     Contains %%A packages
) else (
    echo [ERROR] requirements.txt not found
    echo   Are you in the correct directory?
)
echo.

REM Check .env.template
echo [5/8] Checking .env.template...
if exist ".env.template" (
    echo [OK] .env.template found
) else (
    echo [ERROR] .env.template not found
    echo   This file is required for setup
)
echo.

REM Check .env
echo [6/8] Checking .env configuration...
if exist ".env" (
    echo [OK] .env file exists
    
    REM Check for placeholder values
    findstr /C:"your-service.openai.azure.com" .env >nul
    if %errorlevel% equ 0 (
        echo [WARNING] Azure endpoint still has placeholder value
    )
    
    findstr /C:"your-api-key-here" .env >nul
    if %errorlevel% equ 0 (
        echo [WARNING] Azure API key still has placeholder value
    )
) else (
    echo [WARNING] .env file not found
    echo   Run setup.bat to create it
)
echo.

REM Check Qdrant connection
echo [7/8] Checking Qdrant connection...
if exist "venv\Scripts\python.exe" (
    call venv\Scripts\activate.bat
    python -c "from qdrant_client import QdrantClient; client = QdrantClient(host='localhost', port=6333); collections = client.get_collections(); print('[OK] Connected to Qdrant'); print(f'     Found {len(collections.collections)} collections')" 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Cannot connect to Qdrant
        echo   Make sure Qdrant is running:
        echo     docker run -p 6333:6333 qdrant/qdrant
        echo   Or check if it's running at a different address
    )
) else (
    echo [SKIPPED] Virtual environment not set up yet
)
echo.

REM Check installed packages
echo [8/8] Checking installed packages...
if exist "venv\Scripts\python.exe" (
    call venv\Scripts\activate.bat
    
    echo Checking key packages:
    for %%P in (qdrant-client sentence-transformers openai python-dotenv customtkinter) do (
        python -c "import importlib; importlib.import_module('%%P'.replace('-','_')); print('[OK] %%P installed')" 2>nul
        if !errorlevel! neq 0 (
            echo [ERROR] %%P not installed
        )
    )
) else (
    echo [SKIPPED] Virtual environment not set up yet
)
echo.

REM System information
echo ============================================
echo System Information
echo ============================================
echo OS: 
ver
echo.
echo Python Location:
where python
echo.
echo Current Directory:
cd
echo.

REM Recommendations
echo ============================================
echo Recommendations
echo ============================================
echo.

set ISSUES=0

if not exist "venv\Scripts\python.exe" (
    echo - Run setup.bat to create virtual environment
    set /a ISSUES+=1
)

if not exist ".env" (
    echo - Run setup.bat to configure Azure credentials
    set /a ISSUES+=1
)

findstr /C:"your-api-key-here" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo - Edit .env file with your actual Azure credentials
    set /a ISSUES+=1
)

python -c "from qdrant_client import QdrantClient; client = QdrantClient(host='localhost', port=6333); collections = client.get_collections()" >nul 2>&1
if %errorlevel% neq 0 (
    echo - Start Qdrant: docker run -p 6333:6333 qdrant/qdrant
    set /a ISSUES+=1
)

if %ISSUES% equ 0 (
    echo [OK] No issues detected!
    echo You should be able to run: python gui.py
) else (
    echo Found %ISSUES% issue(s) that need attention.
)

echo.
echo For more help, see WINDOWS_SETUP.md
echo.
pause
