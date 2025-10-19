# Windows Setup Guide for MD to Qdrant Importer

This guide will help you set up the MD to Qdrant Importer on Windows.

## Prerequisites

### 1. Install Python

1. Download Python 3.8 or later from [python.org](https://www.python.org/downloads/)
2. **IMPORTANT**: During installation, check the box "Add Python to PATH"
3. Verify installation by opening Command Prompt or PowerShell and typing:
   ```
   python --version
   ```
   You should see something like "Python 3.11.x"

### 2. Install Git (Optional but Recommended)

Download Git from [git-scm.com](https://git-scm.com/download/win)

### 3. Install Qdrant

You have two options:

#### Option A: Docker Desktop (Recommended)
1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Start Docker Desktop
3. Open Command Prompt or PowerShell and run:
   ```
   docker run -d -p 6333:6333 qdrant/qdrant
   ```

#### Option B: Qdrant Windows Binary
1. Download from [Qdrant Releases](https://github.com/qdrant/qdrant/releases)
2. Extract and run the executable

### 4. Get Azure OpenAI Credentials

1. Log in to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Go to "Keys and Endpoint"
4. Note down:
   - Endpoint URL (e.g., https://your-service.openai.azure.com/)
   - API Key
   - Your deployment name (e.g., gpt-4o)

## Installation

### Method 1: Using PowerShell (Recommended)

1. Download or clone this repository
2. Open PowerShell as Administrator (right-click PowerShell → Run as Administrator)
3. Navigate to the project directory:
   ```powershell
   cd path\to\md-to-qdrant-importer
   ```
4. If you get an execution policy error, run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
5. Run the setup script:
   ```powershell
   .\setup.ps1
   ```
6. Follow the prompts to enter your Azure credentials

### Method 2: Using Command Prompt

1. Download or clone this repository
2. Open Command Prompt
3. Navigate to the project directory:
   ```cmd
   cd path\to\md-to-qdrant-importer
   ```
4. Run the setup script:
   ```cmd
   setup.bat
   ```
5. Follow the prompts to enter your Azure credentials

### Method 3: Manual Setup

If the automated scripts don't work, follow these steps:

1. Open Command Prompt or PowerShell in the project directory

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - PowerShell: `.\venv\Scripts\Activate.ps1`
   - Command Prompt: `venv\Scripts\activate.bat`

4. Upgrade pip:
   ```
   python -m pip install --upgrade pip
   ```

5. Install requirements:
   ```
   pip install -r requirements.txt
   ```

6. Create directories:
   ```
   mkdir input_md_files
   mkdir output_logs
   ```

7. Copy the environment template:
   ```
   copy .env.template .env
   ```

8. Edit `.env` with Notepad and add your Azure credentials:
   ```
   AZURE_ENDPOINT=https://your-service.openai.azure.com/
   AZURE_API_KEY=your-api-key-here
   AZURE_DEPLOYMENT_NAME=gpt-4o
   ```

## Usage

### Before Each Use

Always activate the virtual environment first:

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

You should see `(venv)` at the beginning of your prompt.

### Running the GUI

```
python gui.py
```

### Running the CLI

```
python cli.py .\input_md_files
```

For more options:
```
python cli.py --help
```

## Troubleshooting

### "Python is not recognized"

**Problem**: Windows can't find Python.

**Solution**:
1. Reinstall Python and check "Add Python to PATH"
2. Or manually add Python to PATH:
   - Search for "Environment Variables" in Windows
   - Click "Environment Variables"
   - Under "User variables", find "Path"
   - Add `C:\Users\YourUsername\AppData\Local\Programs\Python\Python3XX` (adjust version)
   - Add `C:\Users\YourUsername\AppData\Local\Programs\Python\Python3XX\Scripts`

### "Cannot be loaded because running scripts is disabled"

**Problem**: PowerShell execution policy blocks scripts.

**Solution**:
1. Open PowerShell as Administrator
2. Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. Type `Y` and press Enter

### "Failed to connect to Qdrant"

**Problem**: Qdrant is not running or connection settings are wrong.

**Solution**:
1. Check if Qdrant is running:
   - Docker: `docker ps` (should show qdrant container)
   - Binary: Check Task Manager for qdrant.exe
2. Verify `.env` settings:
   ```
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   ```
3. Try accessing http://localhost:6333/dashboard in your browser

### "No module named 'qdrant_client'"

**Problem**: Dependencies not installed or wrong Python environment.

**Solution**:
1. Make sure virtual environment is activated (you should see `(venv)`)
2. Run: `pip install -r requirements.txt`

### "SSL Certificate Error" with Azure

**Problem**: Corporate firewall or proxy blocking Azure connection.

**Solution**:
1. Check your internet connection
2. Try disabling VPN if you're using one
3. Contact your IT department about firewall rules for Azure services

### GUI Window is Blank or Crashes

**Problem**: GUI library issues or missing dependencies.

**Solution**:
1. Update customtkinter: `pip install --upgrade customtkinter`
2. Update Pillow: `pip install --upgrade Pillow`
3. Try the CLI instead: `python cli.py .\input_md_files`

### "ImportError: DLL load failed"

**Problem**: Missing Visual C++ Redistributables.

**Solution**:
1. Download and install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Restart your computer
3. Try setup again

## File Locations

- **Input files**: `.\input_md_files\` - Place your markdown files here
- **Output logs**: `.\output_logs\` - Processing logs and results
- **Configuration**: `.env` - Your settings (don't share this file!)
- **Virtual environment**: `.\venv\` - Python packages

## Tips for Windows Users

1. **Use PowerShell instead of CMD** - It has better support for modern Python tools

2. **Keep paths simple** - Avoid spaces in directory names:
   - Good: `C:\Projects\md-importer`
   - Bad: `C:\My Documents\MD to Qdrant Importer`

3. **Run as Administrator** - Some operations may require admin rights

4. **Antivirus** - Some antivirus software may slow down Python. Add the `venv` folder to exclusions if needed.

5. **Windows Defender** - May scan every file during installation. Be patient!

## Uninstallation

1. Deactivate virtual environment (if active): `deactivate`
2. Delete the project folder
3. If you installed Docker just for this, uninstall Docker Desktop

## Getting Help

- **GitHub Issues**: [Report problems](https://github.com/Cosmicjedi/md-to-qdrant-importer/issues)
- **Check logs**: Look in `.\output_logs\` for detailed error messages
- **Test configuration**: Run `python validate.py` to check your setup

## Quick Reference

| Task | PowerShell | Command Prompt |
|------|-----------|----------------|
| Activate venv | `.\venv\Scripts\Activate.ps1` | `venv\Scripts\activate.bat` |
| Deactivate venv | `deactivate` | `deactivate` |
| Run setup | `.\setup.ps1` | `setup.bat` |
| Start GUI | `python gui.py` | `python gui.py` |
| Start CLI | `python cli.py .\input` | `python cli.py .\input` |
| Update packages | `pip install -r requirements.txt --upgrade` | Same |

## Next Steps

After successful setup:

1. Place your markdown files in `.\input_md_files\`
2. Make sure Qdrant is running
3. Run the GUI (`python gui.py`) or CLI (`python cli.py .\input_md_files`)
4. Check the output logs for results
5. Query your data in Qdrant!

Happy importing! 🚀
