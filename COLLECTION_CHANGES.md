# Collection Structure Update - Removed _general Collection

## Summary of Changes

Per your requirement, I've removed the `_general` collection and made `_rulebooks` the default destination for all content that doesn't match adventure paths or NPCs.

## Files Modified

### 1. config.py
**Removed:**
```python
self.qdrant_collection_general = f"{self.qdrant_collection_prefix}_general"
```

**Result:** Only 3 collections are now defined:
- `{prefix}_npcs`
- `{prefix}_rulebooks`
- `{prefix}_adventurepaths`

### 2. qdrant_handler.py

**Changed `_ensure_collections()` method:**
```python
# OLD - Created 4 collections including _general
required_collections = [
    (self.config.qdrant_collection_general, "general content"),
    (self.config.qdrant_collection_npcs, "NPCs"),
    (self.config.qdrant_collection_rulebooks, "rulebooks"),
    (self.config.qdrant_collection_adventurepaths, "adventure paths"),
]

# NEW - Creates only 3 collections
required_collections = [
    (self.config.qdrant_collection_npcs, "NPCs"),
    (self.config.qdrant_collection_rulebooks, "rulebooks"),
    (self.config.qdrant_collection_adventurepaths, "adventure paths"),
]
```

**Changed `determine_collection()` method:**
```python
# OLD - Default to _general
def determine_collection(self, file_path: Path, metadata: Dict[str, Any]) -> str:
    filename_lower = file_path.name.lower()
    
    if 'adventure path' in filename_lower or 'adventurepath' in filename_lower:
        return self.config.qdrant_collection_adventurepaths
    
    rulebook_patterns = ['rulebook', 'core rules', 'rules', 'handbook', 'guide', 'manual', 'compendium']
    if any(pattern in filename_lower for pattern in rulebook_patterns):
        return self.config.qdrant_collection_rulebooks
    
    return self.config.qdrant_collection_general  # ← Old default

# NEW - Default to _rulebooks
def determine_collection(self, file_path: Path, metadata: Dict[str, Any]) -> str:
    filename_lower = file_path.name.lower()
    
    # Check for adventure path indicator in filename
    if 'adventure path' in filename_lower or 'adventurepath' in filename_lower:
        return self.config.qdrant_collection_adventurepaths
    
    # Everything else defaults to rulebooks
    return self.config.qdrant_collection_rulebooks  # ← New default
```

**Updated `_get_content_type_from_collection()` method:**
```python
# OLD
def _get_content_type_from_collection(self, collection_name: str) -> str:
    if collection_name == self.config.qdrant_collection_rulebooks:
        return "rulebook"
    elif collection_name == self.config.qdrant_collection_adventurepaths:
        return "adventure_path"
    elif collection_name == self.config.qdrant_collection_npcs:
        return "npc"
    else:
        return "general"  # Old default

# NEW
def _get_content_type_from_collection(self, collection_name: str) -> str:
    if collection_name == self.config.qdrant_collection_rulebooks:
        return "rulebook"
    elif collection_name == self.config.qdrant_collection_adventurepaths:
        return "adventure_path"
    elif collection_name == self.config.qdrant_collection_npcs:
        return "npc"
    else:
        return "rulebook"  # New default
```

**Updated `insert_chunks()` method:**
```python
# OLD
if not chunks:
    return 0, self.config.qdrant_collection_general

# NEW
if not chunks:
    return 0, self.config.qdrant_collection_rulebooks
```

**Updated `check_file_exists()` method:**
```python
# OLD - Only checked _general collection
def check_file_exists(self, file_path: Path) -> bool:
    try:
        result = self.client.scroll(
            collection_name=self.config.qdrant_collection_general,
            scroll_filter=Filter(...)
        )
        return len(result[0]) > 0
    except Exception:
        return False

# NEW - Checks both _rulebooks and _adventurepaths
def check_file_exists(self, file_path: Path) -> bool:
    for collection_name in [
        self.config.qdrant_collection_rulebooks,
        self.config.qdrant_collection_adventurepaths
    ]:
        try:
            result = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(...)
            )
            if len(result[0]) > 0:
                return True
        except Exception:
            continue
    return False
```

**Updated `delete_by_file()` method:**
```python
# OLD - Default to _general
if collection_name is None:
    collection_name = self.config.qdrant_collection_general

# NEW - Check both collections if not specified
if collection_name:
    collections_to_check = [collection_name]
else:
    collections_to_check = [
        self.config.qdrant_collection_rulebooks,
        self.config.qdrant_collection_adventurepaths
    ]
```

### 3. import_processor.py

**Changed `get_stats()` method:**
```python
# OLD - Included _general
def get_stats(self) -> Dict[str, Any]:
    general_stats = self.qdrant.get_collection_stats(
        self.config.qdrant_collection_general
    )
    npc_stats = self.qdrant.get_collection_stats(...)
    rulebook_stats = self.qdrant.get_collection_stats(...)
    adventurepath_stats = self.qdrant.get_collection_stats(...)
    
    return {
        'general_content': general_stats,
        'npcs': npc_stats,
        'rulebooks': rulebook_stats,
        'adventure_paths': adventurepath_stats,
        'timestamp': datetime.now().isoformat()
    }

# NEW - Only 3 collections
def get_stats(self) -> Dict[str, Any]:
    npc_stats = self.qdrant.get_collection_stats(
        self.config.qdrant_collection_npcs
    )
    rulebook_stats = self.qdrant.get_collection_stats(
        self.config.qdrant_collection_rulebooks
    )
    adventurepath_stats = self.qdrant.get_collection_stats(
        self.config.qdrant_collection_adventurepaths
    )
    
    return {
        'npcs': npc_stats,
        'rulebooks': rulebook_stats,
        'adventure_paths': adventurepath_stats,
        'timestamp': datetime.now().isoformat()
    }
```

## New Collection Routing Logic

**Simple 2-step routing:**

```
1. Check filename for "adventure path" or "adventurepath"
   → YES: Route to {prefix}_adventurepaths
   → NO: Continue to step 2

2. Route to {prefix}_rulebooks (default for everything else)
```

**Examples:**

| Filename | Collection |
|----------|------------|
| `star_wars_adventure_path_01.md` | `game_adventurepaths` |
| `Adventure Path - Lost Mines.md` | `game_adventurepaths` |
| `Core Rulebook.md` | `game_rulebooks` |
| `D&D 5e Players Handbook.md` | `game_rulebooks` |
| `NPC Compendium.md` | `game_rulebooks` |
| `random_notes.md` | `game_rulebooks` |
| `character_backstory.md` | `game_rulebooks` |
| `session_notes.md` | `game_rulebooks` |

**Note:** The old code checked for rulebook patterns (like "rulebook", "handbook", "guide") but that's now unnecessary since everything defaults to `_rulebooks` anyway.

## Collection Structure

### Final Collections (Only 3)

```
{prefix}_npcs
  ├─ Extracted NPC stat blocks
  ├─ canonical: true for rulebook NPCs
  └─ Source file references

{prefix}_rulebooks (DEFAULT)
  ├─ Core rulebooks
  ├─ Character options
  ├─ Rules expansions
  ├─ Monster manuals
  ├─ Equipment lists
  ├─ Session notes
  ├─ Random documents
  └─ Everything that isn't an adventure path

{prefix}_adventurepaths
  ├─ Adventure modules
  ├─ Campaigns
  └─ Adventure paths
```

## Benefits of This Change

1. **Simpler Structure** - Only 3 collections instead of 4
2. **Clear Purpose** - No ambiguity about what goes where
3. **Less Confusion** - No need to differentiate "general" vs "rulebooks"
4. **Easier Queries** - Fewer collections to search
5. **Better Organization** - Clear distinction between adventures and everything else

## Migration Guide

### For Existing Databases

If you have data in the old `_general` collection:

**Option 1: Leave it as-is**
- The old `_general` collection will remain in Qdrant
- New imports will go to `_rulebooks` or `_adventurepaths`
- You'll have 4 collections temporarily

**Option 2: Migrate data**
```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
prefix = "game"

# Get all points from _general
points = client.scroll(
    collection_name=f"{prefix}_general",
    limit=10000
)

# Move to _rulebooks (if not adventure paths)
# This is manual - you'd need to:
# 1. Read points from _general
# 2. Check if they should be in _adventurepaths
# 3. Insert into appropriate collection
# 4. Delete from _general
```

**Option 3: Re-import**
- Delete the old `_general` collection
- Re-run imports with new code
- Everything will go to correct collection

### For New Installations

No migration needed - just use the new code!

## Testing Checklist

After applying these changes:

- [ ] Only 3 collections are created (_npcs, _rulebooks, _adventurepaths)
- [ ] Adventure path files go to _adventurepaths
- [ ] All other files go to _rulebooks
- [ ] NPCs extracted to _npcs collection
- [ ] check_file_exists() works correctly
- [ ] get_stats() returns 3 collections
- [ ] GUI shows correct 3 collections
- [ ] No references to _general in code

## Code Verification

**Search for any remaining references:**
```bash
# Should return NO results
grep -r "collection_general" *.py
grep -r "_general" *.py
```

All references have been removed from:
- config.py
- qdrant_handler.py
- import_processor.py
- gui.py (already updated earlier)

## Documentation Updates Needed

The following documentation should be updated in the repository:

1. **README.md** - Update collection list
2. **COLLECTION_NAMING.md** - Remove _general references
3. **.env.template** - Update collection comments
4. **QUICKSTART.md** - Update collection examples
5. **ARCHITECTURE.md** - Update system diagrams

## Summary

**Before:**
- 4 collections: _general (default), _npcs, _rulebooks, _adventurepaths
- Complex routing logic
- Unclear what goes to "general" vs "rulebooks"

**After:**
- 3 collections: _npcs, _rulebooks (default), _adventurepaths
- Simple routing logic
- Clear: adventures go to _adventurepaths, everything else to _rulebooks

The change simplifies the architecture and makes the system easier to understand and maintain.
