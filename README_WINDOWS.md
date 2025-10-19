# Windows Setup Files for MD to Qdrant Importer

This package contains everything you need to set up the MD to Qdrant Importer on Windows.

## 📦 Files Included

### Setup Scripts

1. **setup.ps1** (PowerShell)
   - Main setup script for modern Windows (Windows 10/11)
   - Requires PowerShell 5.1 or later
   - Best option for most users
   - Creates virtual environment, installs dependencies, configures settings
   - Includes color-coded output and better error handling

2. **setup.bat** (Batch File)
   - Alternative setup script for older Windows or users who prefer CMD
   - Works on Windows 7 and later
   - Same functionality as PowerShell version
   - Use if you have issues with PowerShell execution policies

### Launcher Scripts

3. **start_gui.bat**
   - Quick launcher for the GUI interface
   - Double-click to run after setup is complete
   - Automatically activates virtual environment and starts the GUI

### Diagnostic Tools

4. **diagnose.bat**
   - Troubleshooting script to check your installation
   - Runs 8 diagnostic checks:
     - Python installation
     - pip availability
     - Virtual environment status
     - Required files
     - Configuration status
     - Qdrant connection
     - Package installation
   - Provides specific recommendations for fixing issues

### Documentation

5. **WINDOWS_SETUP.md**
   - Comprehensive Windows setup guide
   - Prerequisites and installation instructions
   - Three installation methods (PowerShell, Batch, Manual)
   - Detailed troubleshooting section
   - Tips for Windows users
   - Quick reference table

## 🚀 Quick Start

### First Time Setup

1. **Install Prerequisites**
   - Python 3.8+ (from [python.org](https://www.python.org/downloads/))
   - Qdrant (via Docker or standalone)
   - Azure OpenAI credentials ready

2. **Choose Your Setup Method**

   **Option A: PowerShell (Recommended)**
   ```powershell
   # Right-click PowerShell → Run as Administrator
   # Navigate to project directory
   cd path\to\md-to-qdrant-importer
   
   # Allow script execution (if needed)
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   
   # Run setup
   .\setup.ps1
   ```

   **Option B: Command Prompt**
   ```cmd
   # Open Command Prompt
   # Navigate to project directory
   cd path\to\md-to-qdrant-importer
   
   # Run setup
   setup.bat
   ```

3. **Follow the Prompts**
   - Enter Azure OpenAI endpoint
   - Enter Azure API key
   - Enter deployment name
   - Configure Qdrant connection (or use defaults)

4. **Verify Installation**
   - Run `diagnose.bat` to check everything is working
   - Should see "[OK]" for all checks

### Running the Application

**GUI Mode:**
- Double-click `start_gui.bat`
- Or run: `python gui.py` from activated virtual environment

**CLI Mode:**
```cmd
# Activate virtual environment first
venv\Scripts\activate.bat

# Run importer
python cli.py .\input_md_files

# With options
python cli.py .\input_md_files --skip-existing --verbose
```

## 🔧 What Each Setup Script Does

### During Setup

Both `setup.ps1` and `setup.bat` perform these steps:

1. **Check Python Installation**
   - Verifies Python 3.8+ is installed
   - Checks if Python is in PATH
   - Shows Python version

2. **Create Virtual Environment**
   - Creates isolated Python environment in `venv` folder
   - Prevents conflicts with system Python packages

3. **Install Dependencies**
   - Upgrades pip to latest version
   - Installs all packages from `requirements.txt`:
     - qdrant-client (vector database)
     - sentence-transformers (embeddings)
     - openai (Azure AI)
     - python-dotenv (configuration)
     - customtkinter (GUI)
     - And 10+ more packages

4. **Create Directories**
   - `input_md_files/` - Put your markdown files here
   - `output_logs/` - Processing logs and results

5. **Configure Settings**
   - Copies `.env.template` to `.env`
   - Prompts for Azure credentials
   - Prompts for Qdrant settings
   - Saves configuration securely

6. **Validate Installation**
   - Tests Qdrant connection
   - Validates configuration file
   - Reports any issues

## 📊 What Gets Created

After successful setup, you'll have:

```
md-to-qdrant-importer/
├── venv/                      # Virtual environment (don't commit)
│   ├── Scripts/
│   │   ├── python.exe
│   │   ├── activate.bat       # For CMD
│   │   └── Activate.ps1       # For PowerShell
│   └── Lib/                   # Installed packages
├── input_md_files/            # Your markdown files go here
├── output_logs/               # Processing results
├── .env                       # Your configuration (don't commit)
├── setup.ps1                  # PowerShell setup
├── setup.bat                  # Batch setup
├── start_gui.bat              # GUI launcher
├── diagnose.bat               # Diagnostic tool
├── WINDOWS_SETUP.md           # This guide
└── [Python source files]      # Main application
```

## 🔍 Troubleshooting Guide

### Run Diagnostics First

Always start with:
```cmd
diagnose.bat
```

This will identify most common issues.

### Common Issues

**"Python is not recognized"**
- Solution: Reinstall Python with "Add to PATH" checked
- Or manually add Python to system PATH

**"Cannot activate virtual environment"**
- Solution: Make sure you're in the project directory
- Check that `venv\Scripts\activate.bat` exists

**"Failed to connect to Qdrant"**
- Solution: Start Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
- Check `.env` has correct host/port

**"Module not found" errors**
- Solution: Activate venv and reinstall: `pip install -r requirements.txt`

**PowerShell execution policy error**
- Solution: Run PowerShell as Admin and execute:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### Getting More Help

1. Run `diagnose.bat` and share the output
2. Check `output_logs/` for detailed error messages
3. Read `WINDOWS_SETUP.md` for detailed troubleshooting
4. Open an issue on GitHub with:
   - Windows version
   - Python version
   - Error messages
   - Output from `diagnose.bat`

## 💡 Tips

### For Best Results

1. **Use PowerShell** over Command Prompt when possible
2. **Run as Administrator** for initial setup
3. **Keep paths simple** - avoid spaces and special characters
4. **Install in short path** like `C:\Projects\md-importer`
5. **Close antivirus** temporarily during pip install (speeds up)

### Virtual Environment Best Practices

- Always activate before running Python commands
- You'll see `(venv)` in your prompt when activated
- Deactivate with: `deactivate`
- Don't commit the `venv` folder to git
- Recreate if needed: delete `venv` folder and run setup again

### Configuration Management

- `.env` contains your secrets - never commit it
- `.env.template` is the template - safe to commit
- Back up `.env` before reconfiguring
- Use different prefixes for different game systems:
  ```
  QDRANT_COLLECTION_PREFIX=dnd
  QDRANT_COLLECTION_PREFIX=starwars
  ```

## 📋 Comparison: PowerShell vs Batch

| Feature | setup.ps1 | setup.bat |
|---------|-----------|-----------|
| Windows Compatibility | Win 10/11 | Win 7+ |
| Colored Output | ✅ | ❌ |
| Progress Indicators | ✅ | ❌ |
| Secure Password Input | ✅ | ❌ |
| Error Handling | Better | Basic |
| Speed | Faster | Slower |
| Requires Admin | Sometimes | Sometimes |

**Recommendation**: Use `setup.ps1` unless you encounter execution policy issues.

## 🎯 Next Steps

After successful setup:

1. **Start Qdrant** (if not already running)
   ```
   docker run -p 6333:6333 qdrant/qdrant
   ```

2. **Add Markdown Files**
   - Copy your `.md` files to `input_md_files\`
   - Files from MarkItDown work great

3. **Run the Importer**
   - GUI: Double-click `start_gui.bat`
   - CLI: `python cli.py .\input_md_files`

4. **Check Results**
   - View logs in `output_logs\`
   - Query Qdrant at http://localhost:6333/dashboard

5. **Start Using Your Data**
   - Use the collections created:
     - `game_general` - General content
     - `game_npcs` - NPC stat blocks
     - `game_rulebooks` - Rules content
     - `game_adventurepaths` - Adventures

## 📞 Support

- **Documentation**: See `WINDOWS_SETUP.md` for detailed guide
- **Diagnostics**: Run `diagnose.bat` for automatic troubleshooting
- **GitHub Issues**: [Report bugs](https://github.com/Cosmicjedi/md-to-qdrant-importer/issues)
- **GitHub Discussions**: [Ask questions](https://github.com/Cosmicjedi/md-to-qdrant-importer/discussions)

## 📝 Version Information

These scripts are compatible with:
- Windows 7, 8, 10, 11
- Python 3.8, 3.9, 3.10, 3.11, 3.12
- PowerShell 5.1+ (for .ps1)
- Command Prompt (for .bat)

---

**Ready to import?** Run `setup.ps1` or `setup.bat` and follow the prompts! 🚀
