# Windows Setup - Quick Reference Card

## 🎯 Choose Your Method

### Method 1: PowerShell (Recommended)
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup.ps1
```

### Method 2: Command Prompt
```cmd
setup.bat
```

### Method 3: Manual
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.template .env
notepad .env
```

## 📋 Prerequisites Checklist

- [ ] Python 3.8+ installed (with PATH)
- [ ] Qdrant running (docker or binary)
- [ ] Azure OpenAI credentials ready
- [ ] Git installed (optional)

## 🔧 Essential Commands

### Setup & Configuration
```cmd
setup.bat              # Run setup
diagnose.bat           # Check for issues
start_gui.bat          # Launch GUI
```

### Virtual Environment
```cmd
venv\Scripts\activate.bat    # Activate (CMD)
.\venv\Scripts\Activate.ps1  # Activate (PowerShell)
deactivate                    # Deactivate
```

### Running the Application
```cmd
python gui.py                    # GUI mode
python cli.py .\input_md_files  # CLI mode
python cli.py --help             # Show options
```

### Qdrant
```cmd
docker run -p 6333:6333 qdrant/qdrant  # Start Qdrant
```

## 🔍 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Python not found | Add Python to PATH |
| Can't activate venv | Run from project root |
| Qdrant connection failed | Start Qdrant container |
| Module not found | `pip install -r requirements.txt` |
| Script execution blocked | Change PowerShell policy |

## 📁 File Structure

```
md-to-qdrant-importer/
├── setup.ps1           ← Run this (PowerShell)
├── setup.bat           ← Or this (CMD)
├── start_gui.bat       ← Double-click after setup
├── diagnose.bat        ← Run if issues
├── WINDOWS_SETUP.md    ← Full guide
└── README_WINDOWS.md   ← Overview
```

## 🚀 30-Second Setup

1. Open PowerShell as Admin
2. `cd` to project directory  
3. Run `.\setup.ps1`
4. Enter Azure credentials when prompted
5. Double-click `start_gui.bat`

## 💡 Pro Tips

- Use PowerShell over CMD
- Keep paths short and simple
- Always activate venv before commands
- Run `diagnose.bat` if anything fails
- Check `output_logs/` for errors

## 📞 Need Help?

1. Run `diagnose.bat`
2. Read `WINDOWS_SETUP.md`
3. Check GitHub Issues
4. Include diagnostic output when asking for help

---

**Quick Start:** `.\setup.ps1` → Double-click `start_gui.bat` → Import!
