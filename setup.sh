#!/bin/bash

# Setup script for MD to Qdrant Importer
# This script sets up the environment and configuration

echo "============================================"
echo "MD to Qdrant Importer - Setup Script"
echo "============================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.8 or later."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt --quiet
echo "✓ Requirements installed"

# Create directories
echo "Creating directories..."
mkdir -p input_md_files
mkdir -p output_logs
echo "✓ Directories created"

# Check if .env exists
if [ -f ".env" ]; then
    echo "✓ .env file already exists"
    echo
    read -p "Do you want to reconfigure? (y/N): " reconfigure
    if [[ ! "$reconfigure" =~ ^[Yy]$ ]]; then
        echo "Keeping existing configuration."
    else
        cp .env .env.backup
        echo "✓ Existing .env backed up to .env.backup"
    fi
else
    reconfigure="y"
fi

# Configure if needed
if [[ "$reconfigure" =~ ^[Yy]$ ]]; then
    echo
    echo "Configuration Setup"
    echo "==================="
    echo "Please provide your Azure OpenAI credentials."
    echo "(You can find these in Azure Portal > Your AI Service > Keys and Endpoint)"
    echo
    
    # Copy template
    cp .env.template .env
    
    # Azure Endpoint
    read -p "Azure OpenAI Endpoint (e.g., https://myservice.openai.azure.com/): " azure_endpoint
    if [ ! -z "$azure_endpoint" ]; then
        sed -i.bak "s|AZURE_ENDPOINT=.*|AZURE_ENDPOINT=$azure_endpoint|" .env || \
        sed -i '' "s|AZURE_ENDPOINT=.*|AZURE_ENDPOINT=$azure_endpoint|" .env
    fi
    
    # Azure API Key
    read -p "Azure API Key: " azure_api_key
    if [ ! -z "$azure_api_key" ]; then
        sed -i.bak "s|AZURE_API_KEY=.*|AZURE_API_KEY=$azure_api_key|" .env || \
        sed -i '' "s|AZURE_API_KEY=.*|AZURE_API_KEY=$azure_api_key|" .env
    fi
    
    # Azure Deployment Name
    read -p "Azure Deployment Name (default: gpt-4o): " deployment_name
    deployment_name=${deployment_name:-gpt-4o}
    sed -i.bak "s|AZURE_DEPLOYMENT_NAME=.*|AZURE_DEPLOYMENT_NAME=$deployment_name|" .env || \
    sed -i '' "s|AZURE_DEPLOYMENT_NAME=.*|AZURE_DEPLOYMENT_NAME=$deployment_name|" .env
    
    # Qdrant Configuration
    echo
    echo "Qdrant Configuration (press Enter for defaults)"
    read -p "Qdrant Host (default: localhost): " qdrant_host
    qdrant_host=${qdrant_host:-localhost}
    sed -i.bak "s|QDRANT_HOST=.*|QDRANT_HOST=$qdrant_host|" .env || \
    sed -i '' "s|QDRANT_HOST=.*|QDRANT_HOST=$qdrant_host|" .env
    
    read -p "Qdrant Port (default: 6333): " qdrant_port
    qdrant_port=${qdrant_port:-6333}
    sed -i.bak "s|QDRANT_PORT=.*|QDRANT_PORT=$qdrant_port|" .env || \
    sed -i '' "s|QDRANT_PORT=.*|QDRANT_PORT=$qdrant_port|" .env
    
    # Collection Prefix
    read -p "Collection Prefix (default: game): " collection_prefix
    collection_prefix=${collection_prefix:-game}
    sed -i.bak "s|QDRANT_COLLECTION_PREFIX=.*|QDRANT_COLLECTION_PREFIX=$collection_prefix|" .env || \
    sed -i '' "s|QDRANT_COLLECTION_PREFIX=.*|QDRANT_COLLECTION_PREFIX=$collection_prefix|" .env
    
    # Clean up backup files
    rm -f .env.bak
    
    echo "✓ Configuration saved to .env"
fi

# Test Qdrant connection
echo
echo "Testing Qdrant connection..."
python3 -c "
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
"

if [ $? -ne 0 ]; then
    echo
    echo "Please ensure Qdrant is running:"
    echo "  docker run -p 6333:6333 qdrant/qdrant"
    echo "Or check your connection settings in .env"
    exit 1
fi

# Validate configuration
echo
echo "Validating configuration..."
python3 -c "
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
"

if [ $? -ne 0 ]; then
    echo
    echo "Please fix the configuration errors in .env and run setup again."
    exit 1
fi

echo
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo
echo "Usage:"
echo "------"
echo "1. Place your markdown files in: ./input_md_files/"
echo
echo "2. Run the GUI:"
echo "   python gui.py"
echo
echo "3. Or use the CLI:"
echo "   python cli.py ./input_md_files"
echo
echo "4. For help:"
echo "   python cli.py --help"
echo
echo "Collections that will be created:"
echo "  - ${collection_prefix}_general    : General content"
echo "  - ${collection_prefix}_npcs       : Extracted NPCs (canonical: true)"
echo "  - ${collection_prefix}_rulebooks  : Rulebook content"
echo "  - ${collection_prefix}_adventurepaths : Adventure content"
echo
echo "Happy importing!"
