# Setup script for MD to Qdrant Importer (Windows PowerShell)
# This script sets up the environment and configuration

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "MD to Qdrant Importer - Setup Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            Write-Host "✓ Python found: $version" -ForegroundColor Green
            break
        }
    } catch {}
}

if ($null -eq $pythonCmd) {
    Write-Host "Error: Python 3 is not installed." -ForegroundColor Red
    Write-Host "Please install Python 3.8 or later from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation!" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment if it doesn't exist
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    & $pythonCmd -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
$activateScript = ".\venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    # Check execution policy
    $executionPolicy = Get-ExecutionPolicy
    if ($executionPolicy -eq "Restricted") {
        Write-Host "Warning: PowerShell execution policy is Restricted" -ForegroundColor Yellow
        Write-Host "Attempting to bypass for this session..." -ForegroundColor Yellow
        Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
    }
    
    try {
        & $activateScript
        Write-Host "✓ Virtual environment activated" -ForegroundColor Green
    } catch {
        Write-Host "Warning: Could not activate with PowerShell, trying cmd..." -ForegroundColor Yellow
        cmd /c "venv\Scripts\activate.bat && python --version"
    }
} else {
    Write-Host "✗ Activation script not found" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& python -m pip install --upgrade pip --quiet
Write-Host "✓ pip upgraded" -ForegroundColor Green

# Install requirements
Write-Host "Installing requirements (this may take a few minutes)..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    & pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Requirements installed" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to install requirements" -ForegroundColor Red
        Write-Host "Trying without --quiet flag to see errors..." -ForegroundColor Yellow
        & pip install -r requirements.txt
        Read-Host "Press Enter to continue anyway"
    }
} else {
    Write-Host "✗ requirements.txt not found" -ForegroundColor Red
    exit 1
}

# Create directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "input_md_files" | Out-Null
New-Item -ItemType Directory -Force -Path "output_logs" | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green

# Check if .env exists
$reconfigure = $false
if (Test-Path ".env") {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
    Write-Host ""
    $response = Read-Host "Do you want to reconfigure? (y/N)"
    if ($response -match "^[Yy]") {
        $reconfigure = $true
        Copy-Item .env .env.backup -Force
        Write-Host "✓ Existing .env backed up to .env.backup" -ForegroundColor Green
    } else {
        Write-Host "Keeping existing configuration." -ForegroundColor Cyan
    }
} else {
    $reconfigure = $true
}

# Configure if needed
if ($reconfigure) {
    Write-Host ""
    Write-Host "Configuration Setup" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    Write-Host "Please provide your Azure OpenAI credentials." -ForegroundColor Yellow
    Write-Host "(You can find these in Azure Portal > Your AI Service > Keys and Endpoint)" -ForegroundColor Yellow
    Write-Host ""
    
    # Copy template
    if (Test-Path ".env.template") {
        Copy-Item .env.template .env -Force
    } else {
        Write-Host "✗ .env.template not found" -ForegroundColor Red
        exit 1
    }
    
    # Read current values for defaults
    $envContent = Get-Content .env -Raw
    
    # Azure Endpoint
    $azure_endpoint = Read-Host "Azure OpenAI Endpoint (e.g., https://myservice.openai.azure.com/)"
    if ($azure_endpoint) {
        $envContent = $envContent -replace "AZURE_ENDPOINT=.*", "AZURE_ENDPOINT=$azure_endpoint"
    }
    
    # Azure API Key
    $azure_api_key = Read-Host "Azure API Key" -AsSecureString
    $azure_api_key_plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($azure_api_key)
    )
    if ($azure_api_key_plain) {
        $envContent = $envContent -replace "AZURE_API_KEY=.*", "AZURE_API_KEY=$azure_api_key_plain"
    }
    
    # Azure Deployment Name
    $deployment_name = Read-Host "Azure Deployment Name (default: gpt-4o)"
    if (-not $deployment_name) {
        $deployment_name = "gpt-4o"
    }
    $envContent = $envContent -replace "AZURE_DEPLOYMENT_NAME=.*", "AZURE_DEPLOYMENT_NAME=$deployment_name"
    
    # Qdrant Configuration
    Write-Host ""
    Write-Host "Qdrant Configuration (press Enter for defaults)" -ForegroundColor Cyan
    
    $qdrant_host = Read-Host "Qdrant Host (default: localhost)"
    if (-not $qdrant_host) {
        $qdrant_host = "localhost"
    }
    $envContent = $envContent -replace "QDRANT_HOST=.*", "QDRANT_HOST=$qdrant_host"
    
    $qdrant_port = Read-Host "Qdrant Port (default: 6333)"
    if (-not $qdrant_port) {
        $qdrant_port = "6333"
    }
    $envContent = $envContent -replace "QDRANT_PORT=.*", "QDRANT_PORT=$qdrant_port"
    
    # Collection Prefix
    $collection_prefix = Read-Host "Collection Prefix (default: game)"
    if (-not $collection_prefix) {
        $collection_prefix = "game"
    }
    $envContent = $envContent -replace "QDRANT_COLLECTION_PREFIX=.*", "QDRANT_COLLECTION_PREFIX=$collection_prefix"
    
    # Save configuration
    Set-Content -Path .env -Value $envContent
    Write-Host "✓ Configuration saved to .env" -ForegroundColor Green
}

# Test Qdrant connection
Write-Host ""
Write-Host "Testing Qdrant connection..." -ForegroundColor Yellow

$testScript = @"
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv
load_dotenv()

try:
    client = QdrantClient(
        host=os.getenv('QDRANT_HOST', 'localhost'),
        port=int(os.getenv('QDRANT_PORT', '6333'))
    )
    collections = client.get_collections()
    print('✓ Successfully connected to Qdrant')
    print(f'  Found {len(collections.collections)} collections')
except Exception as e:
    print(f'✗ Failed to connect to Qdrant: {e}')
    print('  Make sure Qdrant is running at the configured address')
    exit(1)
"@

$testScript | & python -
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Please ensure Qdrant is running:" -ForegroundColor Yellow
    Write-Host "  docker run -p 6333:6333 qdrant/qdrant" -ForegroundColor White
    Write-Host "Or check your connection settings in .env" -ForegroundColor Yellow
    Read-Host "Press Enter to continue anyway"
}

# Validate configuration
Write-Host ""
Write-Host "Validating configuration..." -ForegroundColor Yellow

$validateScript = @"
from config import get_config
config = get_config()
is_valid, errors = config.validate()
if is_valid:
    print('✓ Configuration is valid')
else:
    print('✗ Configuration errors:')
    for error in errors:
        print(f'  - {error}')
    exit(1)
"@

$validateScript | & python -
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Please fix the configuration errors in .env and run setup again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "------" -ForegroundColor Cyan
Write-Host "1. Place your markdown files in: .\input_md_files\" -ForegroundColor White
Write-Host ""
Write-Host "2. Run the GUI:" -ForegroundColor Yellow
Write-Host "   python gui.py" -ForegroundColor White
Write-Host ""
Write-Host "3. Or use the CLI:" -ForegroundColor Yellow
Write-Host "   python cli.py .\input_md_files" -ForegroundColor White
Write-Host ""
Write-Host "4. For help:" -ForegroundColor Yellow
Write-Host "   python cli.py --help" -ForegroundColor White
Write-Host ""
Write-Host "Collections that will be created:" -ForegroundColor Cyan
Write-Host "  - ${collection_prefix}_npcs          : Extracted NPCs (canonical: true)" -ForegroundColor White
Write-Host "  - ${collection_prefix}_rulebooks     : Rulebook content" -ForegroundColor White
Write-Host "  - ${collection_prefix}_adventurepaths: Adventure content" -ForegroundColor White
Write-Host ""
Write-Host "Happy importing!" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"
