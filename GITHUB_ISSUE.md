# Bug: Adventure Paths Incorrectly Routed to Rulebooks Collection

## Summary

Adventure path files are being routed to the `rulebooks` collection instead of the `adventure_paths` collection, and NPCs are being extracted from adventure paths when they shouldn't be.

## Environment

- **Version**: [Current version]
- **Python**: 3.x
- **Qdrant**: 1.7.0+
- **OS**: [Your OS]

## Description

### Bug 1: Collection Routing

Adventure path files with names like "Star Wars - Adventure.md" or "D&D Adventure.md" are being incorrectly routed to the `rulebooks` collection instead of `adventure_paths`.

**Root Cause**: The `determine_collection()` method in `qdrant_handler.py` only checks for exact phrases "adventure path" or "adventurepath", missing files that simply contain "adventure".

### Bug 2: NPC Extraction from Adventure Paths

NPCs are being extracted from adventure paths and added to the general NPCs collection. This is problematic because:
- Adventure paths contain campaign-specific characters
- These NPCs aren't meant for general reference
- Pollutes the NPC collection with context-specific characters

## Steps to Reproduce

1. Create a file named "Test Adventure.md" with NPC content
2. Run: `python cli.py import --file "Test Adventure.md"`
3. Check Qdrant dashboard
4. Observe:
   - File appears in `rulebooks` collection (wrong!)
   - NPCs appear in `npcs` collection (wrong!)

## Expected Behavior

1. Files with "adventure" in the name should route to `adventure_paths` collection
2. NPC extraction should be skipped for adventure paths
3. Campaign-specific characters should stay with their adventure path data

## Actual Behavior

1. Adventure files route to `rulebooks` collection
2. NPCs are extracted from adventure paths
3. Campaign characters pollute the general NPC collection

## Impact

- **Severity**: Medium
- **Affected Users**: Anyone importing adventure paths
- **Data Quality**: Misplaced data in collections
- **Workaround**: Manual cleanup and re-import required

## Solution

See the attached PR for fixes to:
1. `qdrant_handler.py` - Improved adventure path detection
2. `import_processor.py` - Conditional NPC extraction
3. `cleanup_adventure_paths.py` - Utility to clean up existing data

### Key Changes

**qdrant_handler.py**:
```python
def is_adventure_path(self, file_path: Path) -> bool:
    """Check if a file is an adventure path"""
    filename_lower = file_path.name.lower()
    return "adventure" in filename_lower  # More permissive check
```

**import_processor.py**:
```python
# Skip NPC extraction for adventure paths
if is_adventure_path:
    skipped_npc_extraction = True
elif extract_npcs and self.npc_extractor:
    # Only extract NPCs from rulebooks
    npcs_extracted = self.qdrant.insert_npcs(npcs)
```

## Testing

### Test Cases

1. **Adventure Path Detection**
   ```python
   assert is_adventure_path(Path("Adventure.md")) == True
   assert is_adventure_path(Path("D&D Adventure Path.md")) == True
   assert is_adventure_path(Path("Rulebook.md")) == False
   ```

2. **Collection Routing**
   - Import "Test Adventure.md" → Should go to `adventure_paths`
   - Import "Core Rulebook.md" → Should go to `rulebooks`

3. **NPC Extraction**
   - Import adventure with NPCs → No NPCs extracted
   - Import rulebook with NPCs → NPCs extracted normally

### Manual Testing

```bash
# Test adventure path import
python cli.py import --file "Test Adventure.md"
# Expected: Routes to adventure_paths, skips NPC extraction

# Test rulebook import
python cli.py import --file "Core Rulebook.md"
# Expected: Routes to rulebooks, extracts NPCs

# Clean up misplaced data
python cleanup_adventure_paths.py --dry-run
python cleanup_adventure_paths.py --execute
```

## Rollback Plan

If issues arise:
1. Restore Qdrant snapshot from before applying fix
2. Revert code changes
3. Document any new issues discovered

## Migration Required

1. **Backup**: Create Qdrant snapshot
2. **Apply Fix**: Update code files
3. **Clean Up**: Run cleanup script to remove misplaced data
4. **Re-import**: Re-import all adventure path files

## Related Files

- `qdrant_handler.py` - Collection routing logic
- `import_processor.py` - NPC extraction logic  
- `cleanup_adventure_paths.py` - Cleanup utility (new file)
- `FIX_INSTRUCTIONS.md` - Step-by-step fix guide
- `ADVENTURE_PATH_FIX_SUMMARY.md` - Technical details

## Additional Context

### Files Affected

Example misplaced files:
- "Star Wars - Adventure in the Outer Rim.md" → went to rulebooks
- "D&D Adventure - Dragon Heist.md" → went to rulebooks
- "Shadowrun Adventure.md" → went to rulebooks

### NPC Collection Pollution

Example adventure-specific NPCs incorrectly added:
- Campaign villains
- Quest-specific allies
- Location-specific characters

### Cleanup Script Output

```
Found 15 misplaced adventure path files
Total chunks to delete: 1,247
Total NPCs to delete: 47
```

## Checklist

- [x] Bug identified and reproduced
- [x] Root cause analyzed
- [x] Fix implemented and tested
- [x] Cleanup utility created
- [x] Documentation written
- [ ] PR submitted
- [ ] Tests added
- [ ] CHANGELOG updated

## Questions?

Contact: [Your contact info]

## Labels

- `bug`
- `data-quality`
- `qdrant`
- `collection-routing`
- `npc-extraction`

## Milestone

- Target: v1.x.x (next patch release)
