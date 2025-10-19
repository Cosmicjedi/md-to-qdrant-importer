@echo off
REM Setup script for MD to Qdrant Importer (Windows Batch)
REM This script sets up the environment and configuration

setlocal enabledelayedexpansion

echo ============================================
echo MD to Qdrant Importer - Setup Script
echo ============================================
echo.

REM Check if Python is installed
set PYTHON_CMD=
for %%P in (python python3 py) do (
    %%P --version >nul 2>&1
    if !errorlevel! equ 0 (
        set PYTHON_CMD=%%P
        goto :python_found
    )
)

:python_not_found
echo Error: Python 3 is not installed.
echo Please install Python 3.8 or later from https://www.python.org/downloads/
echo Make sure to check 'Add Python to PATH' during installation!
pause
exit /b 1

:python_found
for /f "delims=" %%V in ('%PYTHON_CMD% --version') do set PYTHON_VERSION=%%V
echo [OK] Python found: !PYTHON_VERSION!

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded

REM Install requirements
echo Installing requirements (this may take a few minutes)...
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)

pip install -r requirements.txt --quiet
if !errorlevel! neq 0 (
    echo [WARNING] Installation had issues, trying without quiet flag...
    pip install -r requirements.txt
    echo.
    echo Press any key to continue anyway...
    pause >nul
)
echo [OK] Requirements installed

REM Create directories
echo Creating directories...
if not exist "input_md_files" mkdir input_md_files
if not exist "output_logs" mkdir output_logs
echo [OK] Directories created

REM Check if .env exists
set RECONFIGURE=N
if exist ".env" (
    echo [OK] .env file already exists
    echo.
    set /p RECONFIGURE="Do you want to reconfigure? (y/N): "
    if /i "!RECONFIGURE!"=="y" (
        copy .env .env.backup >nul
        echo [OK] Existing .env backed up to .env.backup
    ) else (
        echo Keeping existing configuration.
        goto :skip_config
    )
) else (
    set RECONFIGURE=Y
)

REM Configure if needed
if /i "!RECONFIGURE!"=="Y" (
    echo.
    echo Configuration Setup
    echo ===================
    echo Please provide your Azure OpenAI credentials.
    echo ^(You can find these in Azure Portal ^> Your AI Service ^> Keys and Endpoint^)
    echo.
    
    REM Copy template
    if not exist ".env.template" (
        echo [ERROR] .env.template not found
        pause
        exit /b 1
    )
    copy .env.template .env >nul
    
    REM Azure Endpoint
    set /p AZURE_ENDPOINT="Azure OpenAI Endpoint (e.g., https://myservice.openai.azure.com/): "
    if not "!AZURE_ENDPOINT!"=="" (
        powershell -Command "(Get-Content .env) -replace 'AZURE_ENDPOINT=.*', 'AZURE_ENDPOINT=!AZURE_ENDPOINT!' | Set-Content .env"
    )
    
    REM Azure API Key
    set /p AZURE_API_KEY="Azure API Key: "
    if not "!AZURE_API_KEY!"=="" (
        powershell -Command "(Get-Content .env) -replace 'AZURE_API_KEY=.*', 'AZURE_API_KEY=!AZURE_API_KEY!' | Set-Content .env"
    )
    
    REM Azure Deployment Name
    set DEPLOYMENT_NAME=gpt-4o
    set /p DEPLOYMENT_NAME="Azure Deployment Name (default: gpt-4o): "
    if "!DEPLOYMENT_NAME!"=="" set DEPLOYMENT_NAME=gpt-4o
    powershell -Command "(Get-Content .env) -replace 'AZURE_DEPLOYMENT_NAME=.*', 'AZURE_DEPLOYMENT_NAME=!DEPLOYMENT_NAME!' | Set-Content .env"
    
    REM Qdrant Configuration
    echo.
    echo Qdrant Configuration (press Enter for defaults)
    
    set QDRANT_HOST=localhost
    set /p QDRANT_HOST="Qdrant Host (default: localhost): "
    if "!QDRANT_HOST!"=="" set QDRANT_HOST=localhost
    powershell -Command "(Get-Content .env) -replace 'QDRANT_HOST=.*', 'QDRANT_HOST=!QDRANT_HOST!' | Set-Content .env"
    
    set QDRANT_PORT=6333
    set /p QDRANT_PORT="Qdrant Port (default: 6333): "
    if "!QDRANT_PORT!"=="" set QDRANT_PORT=6333
    powershell -Command "(Get-Content .env) -replace 'QDRANT_PORT=.*', 'QDRANT_PORT=!QDRANT_PORT!' | Set-Content .env"
    
    REM Collection Prefix
    set COLLECTION_PREFIX=game
    set /p COLLECTION_PREFIX="Collection Prefix (default: game): "
    if "!COLLECTION_PREFIX!"=="" set COLLECTION_PREFIX=game
    powershell -Command "(Get-Content .env) -replace 'QDRANT_COLLECTION_PREFIX=.*', 'QDRANT_COLLECTION_PREFIX=!COLLECTION_PREFIX!' | Set-Content .env"
    
    echo [OK] Configuration saved to .env
)

:skip_config

REM Test Qdrant connection
echo.
echo Testing Qdrant connection...

python -c "from qdrant_client import QdrantClient; import os; from dotenv import load_dotenv; load_dotenv(); client = QdrantClient(host=os.getenv('QDRANT_HOST', 'localhost'), port=int(os.getenv('QDRANT_PORT', '6333'))); collections = client.get_collections(); print('✓ Successfully connected to Qdrant'); print(f'  Found {len(collections.collections)} collections')" 2>nul
if !errorlevel! neq 0 (
    echo [WARNING] Failed to connect to Qdrant
    echo Please ensure Qdrant is running:
    echo   docker run -p 6333:6333 qdrant/qdrant
    echo Or check your connection settings in .env
    echo.
    echo Press any key to continue anyway...
    pause >nul
)

REM Validate configuration
echo.
echo Validating configuration...

python -c "from config import get_config; config = get_config(); is_valid, errors = config.validate(); print('✓ Configuration is valid') if is_valid else [print(f'✗ Configuration errors:\n  - ' + '\n  - '.join(errors)) or exit(1)]"
if !errorlevel! neq 0 (
    echo.
    echo Please fix the configuration errors in .env and run setup again.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Usage:
echo ------
echo 1. Place your markdown files in: .\input_md_files\
echo.
echo 2. Run the GUI:
echo    python gui.py
echo.
echo 3. Or use the CLI:
echo    python cli.py .\input_md_files
echo.
echo 4. For help:
echo    python cli.py --help
echo.
echo Collections that will be created:
echo   - !COLLECTION_PREFIX!_general       : General content
echo   - !COLLECTION_PREFIX!_npcs          : Extracted NPCs (canonical: true)
echo   - !COLLECTION_PREFIX!_rulebooks     : Rulebook content
echo   - !COLLECTION_PREFIX!_adventurepaths: Adventure content
echo.
echo Happy importing!
echo.
pause
