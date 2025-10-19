# GUI and Collection Updates

## Summary of Changes

I've updated the Windows setup package with the following improvements:

### 1. Enhanced GUI (`gui.py`)

**New Features:**
- ✨ **Collection Prefix Configuration**: You can now change the collection prefix directly from the GUI
- 📊 **Live Collections Preview**: Shows which collections will be created based on your prefix
- 🔄 **Runtime Prefix Updates**: Change the prefix without editing the .env file
- ℹ️ **Better Import Confirmation**: Shows which collections will be used before import

**New GUI Elements:**
- Collection Prefix section with:
  - Text entry for the prefix
  - "Update Collections" button
  - Live preview of collection names
- Enhanced import confirmation dialog showing exact collections to be used
- Collection distribution in import results log

**How to Use:**
1. Load configuration (Azure credentials)
2. Modify the collection prefix if desired (default: "game")
3. Click "Update Collections" to apply
4. Select input directory and start import

### 2. Corrected Collection Structure

**Collections Created:**
```
{prefix}_npcs           - Extracted NPC stat blocks (canonical: true)
{prefix}_rulebooks      - Core rulebook content
{prefix}_adventurepaths - Adventure and campaign content
```

**Important Note:** There is NO `{prefix}_general` collection. The code routes content to one of these three collections based on filename analysis:

- **_npcs**: NPCs extracted via Azure AI
- **_rulebooks**: Files with "rulebook", "rules", "handbook", "guide", "manual", "compendium" in filename
- **_adventurepaths**: Files with "adventure path" or "adventurepath" in filename

### 3. Collection Routing Logic

The system automatically determines which collection to use:

```python
# From qdrant_handler.py determine_collection()

If filename contains "adventure path" or "adventurepath":
    → {prefix}_adventurepaths

Else if filename contains rulebook keywords:
    ("rulebook", "core rules", "rules", "handbook", "guide", "manual", "compendium")
    → {prefix}_rulebooks

Else:
    → DEFAULT (would be general, but the actual implementation routes to rulebooks)
```

**Note:** The code has a small inconsistency - it references `qdrant_collection_general` in config.py but the routing logic doesn't have a pure "general" category. All non-adventure content goes to rulebooks or NPCs.

## Updated Setup Scripts

All setup scripts now correctly reflect the three-collection structure:

### setup.ps1 (PowerShell)
```
Collections that will be created:
  - game_npcs          : Extracted NPCs (canonical: true)
  - game_rulebooks     : Rulebook content
  - game_adventurepaths: Adventure content
```

### setup.bat (Batch)
```
Collections that will be created:
  - game_npcs          : Extracted NPCs (canonical: true)
  - game_rulebooks     : Rulebook content
  - game_adventurepaths: Adventure content
```

### Documentation Updates
- README_WINDOWS.md
- Quick reference materials
- All mentions of `_general` collection removed

## Collection Prefix Examples

### Default Configuration
```
QDRANT_COLLECTION_PREFIX=game
```
Creates:
- game_npcs
- game_rulebooks  
- game_adventurepaths

### Multiple Game Systems
```
QDRANT_COLLECTION_PREFIX=dnd5e
```
Creates:
- dnd5e_npcs
- dnd5e_rulebooks
- dnd5e_adventurepaths

```
QDRANT_COLLECTION_PREFIX=starwars
```
Creates:
- starwars_npcs
- starwars_rulebooks
- starwars_adventurepaths

### Campaign-Specific
```
QDRANT_COLLECTION_PREFIX=campaign_stormcrown
```
Creates:
- campaign_stormcrown_npcs
- campaign_stormcrown_rulebooks
- campaign_stormcrown_adventurepaths

## Using the New GUI

### Changing Collection Prefix

**Method 1: Via GUI**
1. Launch GUI: `python gui.py`
2. Load configuration
3. In the "Collection Prefix" section, change "game" to your desired prefix
4. Click "Update Collections"
5. Preview shows updated collection names
6. Start import with new prefix

**Method 2: Via .env File**
1. Edit `.env` file
2. Change `QDRANT_COLLECTION_PREFIX=game` to your desired prefix
3. Save file
4. Click "Load/Reload Config" in GUI
5. Prefix automatically updates

**Method 3: Environment Variable (temporary)**
```cmd
set QDRANT_COLLECTION_PREFIX=myprefix
python gui.py
```

### Import Process

1. **Configure Prefix**: Set your collection prefix
2. **Select Directory**: Browse to your markdown files
3. **Set Options**:
   - Include subdirectories (recursive)
   - Skip files already in database
   - Extract NPCs (requires Azure AI)
4. **Start Import**: Click "Start Import"
5. **Confirmation Dialog**: Shows:
   - Input directory
   - Collections that will be used
   - Asks for confirmation
6. **Monitor Progress**: 
   - Progress bar updates
   - Log shows detailed progress
   - Collection distribution shown
7. **Review Results**:
   - Total files processed
   - Success/failure counts
   - Chunks imported
   - NPCs extracted
   - Files per collection

## GUI Screenshots (Text Description)

### Main Window Layout
```
┌─────────────────────────────────────────────────┐
│ File  Help                                      │
├─────────────────────────────────────────────────┤
│ Configuration                                   │
│ [Loaded ✓]               [Load/Reload Config]  │
├─────────────────────────────────────────────────┤
│ Collection Prefix                               │
│ Prefix: [game_____________] [Update Collections]│
│ Collections: game_npcs, game_rulebooks, ...     │
├─────────────────────────────────────────────────┤
│ Input Directory                                 │
│ [C:\path\to\files\_______________] [Browse...]  │
├─────────────────────────────────────────────────┤
│ Options                                         │
│ ☑ Include subdirectories (recursive)            │
│ ☑ Skip files already in database                │
│ ☑ Extract NPCs (requires Azure AI)              │
├─────────────────────────────────────────────────┤
│ [Start Import] [Stop] [View Stats] [Save Res.]  │
├─────────────────────────────────────────────────┤
│ Progress                                        │
│ [████████████████░░░░░░░░░░] 75%               │
│ ┌─────────────────────────────────────────┐   │
│ │ Processing file.md...                    │   │
│ │ Inserting 150 chunks...                  │   │
│ │ Found 3 NPCs, inserting...               │   │
│ │ [Log messages scroll here]               │   │
│ └─────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│ Status: Processing file 25/100                  │
└─────────────────────────────────────────────────┘
```

## Upgrade Instructions

### For Existing Installations

If you already have the repository installed:

1. **Backup Current GUI** (optional):
   ```cmd
   copy gui.py gui_old.py
   ```

2. **Replace GUI File**:
   - Copy the new `gui.py` from the outputs folder
   - Replace the existing `gui.py` in your installation

3. **No Other Changes Needed**:
   - Config files remain the same
   - Virtual environment doesn't need updates
   - All other files work with the new GUI

4. **Test**:
   ```cmd
   venv\Scripts\activate.bat
   python gui.py
   ```

### For New Installations

Just follow the normal setup process - the new GUI is included automatically.

## Technical Details

### Code Changes in gui.py

**Added Variables:**
```python
self.prefix_var = tk.StringVar(value="game")
self.collections_label = ttk.Label(...)
```

**New Methods:**
```python
def _update_collections_display(self)
def _update_prefix(self)
```

**Modified Methods:**
```python
def _load_config(self, env_file=None)
    # Now updates prefix_var from config
    
def _start_import(self)
    # Shows collection info in confirmation dialog
    
def _run_import(self, input_path)
    # Displays collection distribution in results
```

**Widget Structure:**
- Added LabelFrame for "Collection Prefix"
- Added Entry widget for prefix input
- Added Button for "Update Collections"
- Added Label for collections preview
- Increased window height from 700 to 750

### Configuration Flow

```
User Input (GUI)
    ↓
prefix_var.set(new_prefix)
    ↓
_update_prefix() called
    ↓
os.environ['QDRANT_COLLECTION_PREFIX'] = new_prefix
    ↓
_load_config() reloads Config
    ↓
config.qdrant_collection_prefix updated
    ↓
Collections recreated:
  - config.qdrant_collection_npcs
  - config.qdrant_collection_rulebooks
  - config.qdrant_collection_adventurepaths
    ↓
ImportProcessor uses new collection names
```

## FAQ

**Q: Can I use the old GUI?**
A: Yes, but it won't have the collection prefix configuration feature. You'd need to edit .env manually.

**Q: Do I need to re-import my data?**
A: No, existing data in Qdrant remains unchanged. The new GUI just makes it easier to create new collections with different prefixes.

**Q: What happens if I change the prefix mid-import?**
A: Don't do this. The import process uses the prefix from when it started. Changing it during import could cause confusion.

**Q: Can I have multiple prefixes in the same Qdrant instance?**
A: Yes! That's the whole point. Each prefix creates independent collections:
- `dnd_npcs`, `dnd_rulebooks`, `dnd_adventurepaths`
- `starwars_npcs`, `starwars_rulebooks`, `starwars_adventurepaths`

**Q: Is the _general collection ever used?**
A: No, based on the code. The `determine_collection()` method routes everything to either `_rulebooks` or `_adventurepaths`. The `_general` collection is defined in config but never actually used as a destination.

**Q: Should the code be fixed to actually use _general?**
A: That's up to the repo owner. Currently, "general" content goes to `_rulebooks` by default, which might be intentional.

## Recommendations for Repository Owner

1. **Consider Adding _general Collection**: 
   - Update `determine_collection()` to return `_general` as the default
   - Or remove `_general` from config entirely if not needed

2. **Update Documentation**:
   - COLLECTION_NAMING.md still mentions only `_general` and `_npcs`
   - Should document the actual three-collection structure

3. **Consider GUI Enhancements**:
   - Add validation for collection prefix format
   - Show warning if collections already exist
   - Add button to view existing collections
   - Add ability to test Qdrant connection from GUI

## Summary

The updated GUI provides:
- ✅ Easy collection prefix configuration
- ✅ Visual feedback on collections
- ✅ Better user experience
- ✅ Corrected documentation
- ✅ No breaking changes

All Windows setup files have been updated to reflect the correct collection structure (no `_general` collection mentioned).
