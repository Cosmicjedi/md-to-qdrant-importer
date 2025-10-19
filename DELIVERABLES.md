# Windows Setup Package - Complete Deliverables

## 📦 Package Contents

This package contains everything needed to set up and run the MD to Qdrant Importer on Windows with enhanced GUI functionality.

### Core Setup Files

| File | Size | Description |
|------|------|-------------|
| **setup.ps1** | 9.7 KB | PowerShell setup script (recommended) |
| **setup.bat** | 6.8 KB | Batch file setup script (compatibility) |
| **start_gui.bat** | 985 B | Double-click launcher for GUI |
| **diagnose.bat** | 4.9 KB | Diagnostic tool for troubleshooting |

### Enhanced Application

| File | Description |
|------|-------------|
| **gui.py** | Updated GUI with collection prefix configuration |

**New GUI Features:**
- 🎯 Collection prefix configuration directly in the GUI
- 📊 Live preview of collection names
- 🔄 Runtime updates without editing .env
- ℹ️ Enhanced import confirmation showing collections
- 📈 Collection distribution in results

### Documentation

| File | Size | Purpose |
|------|------|---------|
| **README_WINDOWS.md** | 8.7 KB | Master overview and file explanations |
| **WINDOWS_SETUP.md** | 7.5 KB | Detailed installation and troubleshooting |
| **QUICK_START.md** | 2.4 KB | One-page quick reference |
| **GUI_UPDATE.md** | 11.2 KB | GUI changes and collection structure |

## 🎯 Key Features

### Windows Setup Scripts

✅ **Automated Installation**
- Creates virtual environment
- Installs all dependencies
- Configures Azure credentials
- Tests Qdrant connection
- Validates configuration

✅ **Cross-Compatible**
- PowerShell version (modern Windows)
- Batch file version (maximum compatibility)
- Manual setup instructions

✅ **User-Friendly**
- Color-coded output (PowerShell)
- Progress indicators
- Helpful error messages
- Validation at each step

### Enhanced GUI

✅ **Collection Management**
- Change collection prefix without editing files
- See collections before import
- Support multiple prefixes/game systems
- Visual feedback

✅ **Better User Experience**
- Clear status indicators
- Detailed progress logging
- Collection distribution in results
- Confirmation dialogs with context

## 🔧 Collection Structure (Corrected)

The actual collections created are:

```
{prefix}_npcs           - Extracted NPC stat blocks (canonical: true)
{prefix}_rulebooks      - Core rulebook content  
{prefix}_adventurepaths - Adventure and campaign content
```

**Note:** There is NO `_general` collection. Content is routed based on filename:
- "adventure path" → `_adventurepaths`
- "rulebook", "rules", etc. → `_rulebooks`
- NPCs → `_npcs`
- Default → `_rulebooks`

## 📋 What Was Fixed

### Issue 1: Missing Collection Prefix Configuration
**Problem:** Users couldn't change collection prefix without editing .env file
**Solution:** Added GUI controls for prefix configuration with live preview

### Issue 2: Incorrect Documentation
**Problem:** Documentation mentioned `_general` collection that isn't really used
**Solution:** Updated all docs and setup scripts to show actual three collections

### Issue 3: No Collection Visibility
**Problem:** Users didn't know which collections would be created
**Solution:** GUI now shows collections before import and distribution after

## 🚀 Quick Start Guide

### First Time Setup

1. **Run Setup Script**
   ```powershell
   .\setup.ps1
   ```
   Or:
   ```cmd
   setup.bat
   ```

2. **Enter Azure Credentials When Prompted**
   - Azure OpenAI Endpoint
   - API Key
   - Deployment Name

3. **Configure Collection Prefix (Optional)**
   - Default is "game"
   - Change in GUI or .env file

4. **Launch GUI**
   ```cmd
   start_gui.bat
   ```
   Or:
   ```cmd
   venv\Scripts\activate.bat
   python gui.py
   ```

### Using the Enhanced GUI

1. **Load Configuration** - Click "Load/Reload Config"
2. **Set Prefix** (optional) - Change from "game" to your desired prefix
3. **Update Collections** - Click button to apply new prefix
4. **Select Input** - Browse to your markdown files directory
5. **Configure Options** - Check/uncheck as needed
6. **Start Import** - Confirms collections before starting
7. **Review Results** - See distribution across collections

## 📊 Collection Prefix Examples

### Single Game System
```
QDRANT_COLLECTION_PREFIX=game
```
Collections:
- game_npcs
- game_rulebooks
- game_adventurepaths

### Multiple Systems
```
# D&D 5e
QDRANT_COLLECTION_PREFIX=dnd5e
→ dnd5e_npcs, dnd5e_rulebooks, dnd5e_adventurepaths

# Star Wars
QDRANT_COLLECTION_PREFIX=starwars  
→ starwars_npcs, starwars_rulebooks, starwars_adventurepaths

# Pathfinder
QDRANT_COLLECTION_PREFIX=pathfinder
→ pathfinder_npcs, pathfinder_rulebooks, pathfinder_adventurepaths
```

### Campaign Organization
```
# Core books (shared)
QDRANT_COLLECTION_PREFIX=core
→ core_npcs, core_rulebooks, core_adventurepaths

# Campaign specific
QDRANT_COLLECTION_PREFIX=campaign_stormcrown
→ campaign_stormcrown_npcs, campaign_stormcrown_rulebooks, ...
```

## 🔍 Troubleshooting

### Quick Diagnostics
```cmd
diagnose.bat
```
This checks:
- Python installation
- pip availability
- Virtual environment
- Required files
- Configuration
- Qdrant connection
- Installed packages
- System info

### Common Issues

**Python not found**
- Reinstall Python with "Add to PATH" checked
- See WINDOWS_SETUP.md for manual PATH configuration

**PowerShell execution policy**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Qdrant connection failed**
```cmd
docker run -p 6333:6333 qdrant/qdrant
```

**Missing modules**
```cmd
venv\Scripts\activate.bat
pip install -r requirements.txt
```

## 📁 Installation Structure

After setup:
```
md-to-qdrant-importer/
├── venv/                    # Virtual environment
│   └── Scripts/
│       ├── python.exe
│       ├── activate.bat
│       └── Activate.ps1
├── input_md_files/          # Your markdown files
├── output_logs/             # Processing logs
├── .env                     # Your configuration
├── setup.ps1               # These new files
├── setup.bat               # ↓
├── start_gui.bat           # ↓
├── diagnose.bat            # ↓
├── gui.py                  # Updated version
└── [other Python files]    # Original repo files
```

## 🎓 Learning Path

1. **Start Here**: README_WINDOWS.md
2. **Quick Setup**: QUICK_START.md  
3. **GUI Changes**: GUI_UPDATE.md
4. **Detailed Help**: WINDOWS_SETUP.md
5. **Issues**: diagnose.bat

## 💡 Pro Tips

### For Best Results
- Use PowerShell over Command Prompt
- Run as Administrator for initial setup
- Keep installation path short (no spaces)
- Close antivirus during pip install (faster)
- Always activate venv before Python commands

### Collection Management
- Use descriptive prefixes
- Keep prefixes under 30 characters
- Use underscores, not spaces
- Document your prefix choices
- One prefix per game system or campaign

### GUI Workflow
1. Configure once, import many times
2. Change prefix for different systems
3. Use "Skip existing" for incremental imports
4. Save results for record keeping
5. Check stats to verify import

## 🔄 Upgrade Instructions

### From Previous Version

1. **Backup old GUI** (optional):
   ```cmd
   copy gui.py gui_old.py
   ```

2. **Copy new files**:
   - Replace `gui.py` with updated version
   - Add `setup.ps1`, `setup.bat`, `start_gui.bat`, `diagnose.bat`

3. **No other changes needed**
   - Virtual environment stays the same
   - .env file compatible
   - All dependencies remain

4. **Test**:
   ```cmd
   venv\Scripts\activate.bat
   python gui.py
   ```

## 📞 Support Resources

| Resource | Purpose |
|----------|---------|
| diagnose.bat | Automatic problem detection |
| WINDOWS_SETUP.md | Comprehensive troubleshooting |
| GitHub Issues | Report bugs |
| GitHub Discussions | Ask questions |
| output_logs/ | Detailed error messages |

## ✅ Validation Checklist

Before reporting issues, verify:
- [ ] Python 3.8+ installed with PATH
- [ ] Virtual environment created
- [ ] All packages installed (diagnose.bat)
- [ ] .env file exists with credentials
- [ ] Qdrant is running
- [ ] Can access Qdrant dashboard (http://localhost:6333)
- [ ] Azure credentials are valid
- [ ] Input directory exists and has .md files

## 🎯 Success Metrics

After successful setup and import:
- ✅ GUI launches without errors
- ✅ Configuration shows "Loaded ✓"
- ✅ Can change collection prefix
- ✅ Collections preview shows correct names
- ✅ Import completes successfully
- ✅ Can view statistics
- ✅ Results show distribution by collection
- ✅ Qdrant dashboard shows your collections

## 📝 Version History

**v1.1 - Current**
- Added collection prefix configuration to GUI
- Fixed collection documentation (removed _general)
- Enhanced import confirmation
- Added collection distribution to results
- Updated all setup scripts
- Created comprehensive Windows setup package

**v1.0 - Original**
- Basic GUI
- CLI interface
- Azure AI NPC extraction
- Qdrant integration

## 🤝 Contributing

If you improve these setup scripts:
1. Test on fresh Windows installation
2. Update relevant documentation
3. Submit pull request with description
4. Include before/after examples

## 📄 License

Same as main repository (check repository for details)

---

**Ready to start?** Run `setup.ps1` or `setup.bat` and you'll be importing in minutes! 🚀

For questions or issues:
- Run `diagnose.bat` first
- Check WINDOWS_SETUP.md for solutions
- Search GitHub Issues
- Create new issue with diagnostic output
