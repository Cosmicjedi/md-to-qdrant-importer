# Adventure Path Fix - Technical Summary

## Problem Statement

The md-to-qdrant-importer had two related bugs affecting adventure path processing:

1. **Collection Routing Bug**: Adventure path files were being incorrectly routed to the `rulebooks` collection instead of the `adventure_paths` collection
2. **NPC Extraction Bug**: NPCs were being extracted from adventure paths, when they should only be extracted from rulebooks

## Root Cause Analysis

### Collection Routing Issue

**Location**: `qdrant_handler.py` - `determine_collection()` method

**Problem**: The original code only checked for exact matches like "adventure path" or "adventurepath":

```python
# ORIGINAL (BUGGY) CODE
def determine_collection(self, file_path: Path) -> str:
    filename_lower = file_path.name.lower()
    if 'adventure path' in filename_lower or 'adventurepath' in filename_lower:
        return self.config.qdrant_collection_adventurepaths
    else:
        return self.config.qdrant_collection_rulebooks
```

**Issue**: Files named like "Star Wars - Adventure.md" or "D&D Adventure.md" would fail the check because they only contain "adventure", not "adventure path" or "adventurepath".

### NPC Extraction Issue

**Location**: `import_processor.py` - `process_file()` method

**Problem**: NPCs were being extracted from all files without checking if they were adventure paths:

```python
# ORIGINAL (BUGGY) CODE
if extract_npcs and self.npc_extractor and self.config.enable_npc_extraction:
    npcs = self.npc_extractor.extract_npcs_from_chunks(chunks, str(file_path))
    if npcs:
        npcs_extracted = self.qdrant.insert_npcs(npcs)
```

**Issue**: Campaign-specific NPCs from adventure paths were being added to the general NPC collection, polluting it with characters that shouldn't be used as general references.

## Solution

### 1. Improved Adventure Path Detection

Added a dedicated helper method with broader detection:

```python
# NEW (FIXED) CODE
def is_adventure_path(self, file_path: Path) -> bool:
    """
    Check if a file is an adventure path.
    
    FIXED: Now checks for just "adventure" in the filename
    """
    filename_lower = file_path.name.lower()
    return "adventure" in filename_lower
```

**Benefits**:
- Catches all variations: "adventure", "adventure path", "adventurepath"
- Single source of truth for adventure path detection
- Easy to test and maintain

### 2. Fixed Collection Routing

Updated `determine_collection()` to use the new helper:

```python
# NEW (FIXED) CODE
def determine_collection(self, file_path: Path) -> str:
    """
    Determine which collection a file should go into.
    
    FIXED: Now properly routes adventure paths
    """
    if self.is_adventure_path(file_path):
        logger.info(f"Routing '{file_path.name}' to adventure paths collection")
        return self.config.qdrant_collection_adventurepaths
    else:
        return self.config.qdrant_collection_rulebooks
```

### 3. Conditional NPC Extraction

Modified the import processor to skip NPC extraction for adventure paths:

```python
# NEW (FIXED) CODE
# Check if this is an adventure path
is_adventure_path = self.qdrant.is_adventure_path(file_path)

# IMPORTANT: Skip NPC extraction for adventure paths
npcs_extracted = 0
skipped_npc_extraction = False

if is_adventure_path:
    self._update_progress(f"Skipping NPC extraction for adventure path: {file_path.name}")
    skipped_npc_extraction = True
elif extract_npcs and self.npc_extractor and self.config.enable_npc_extraction:
    # Only extract NPCs from rulebooks
    self._update_progress(f"Extracting NPCs from {file_path.name}...")
    npcs = self.npc_extractor.extract_npcs_from_chunks(chunks, str(file_path))
    
    if npcs:
        self._update_progress(f"Found {len(npcs)} NPCs, inserting...")
        npcs_extracted = self.qdrant.insert_npcs(npcs)
```

### 4. Tracking and Reporting

Added tracking for skipped NPC extractions:

```python
# In ImportResult dataclass
@dataclass
class ImportResult:
    # ... other fields ...
    skipped_npc_extraction: bool = False  # NEW: Track if NPC extraction was skipped

# In save_results() method
summary = {
    # ... other stats ...
    'adventure_paths_skipped_npc': sum(1 for r in results if r.skipped_npc_extraction),
}
```

## Files Modified

### 1. qdrant_handler.py

**Changes**:
- Added `is_adventure_path()` method
- Updated `determine_collection()` to use new detection logic
- Improved logging for adventure path routing

**Lines Modified**: ~10 lines added/changed

### 2. import_processor.py

**Changes**:
- Added `skipped_npc_extraction` field to `ImportResult`
- Modified `process_file()` to conditionally extract NPCs
- Updated `save_results()` to track skipped extractions
- Added progress messages for transparency

**Lines Modified**: ~15 lines added/changed

## New Files Created

### 1. cleanup_adventure_paths.py

**Purpose**: Utility script to identify and remove misplaced adventure path data

**Features**:
- Scans rulebooks collection for adventure path content
- Scans NPCs collection for adventure-specific NPCs
- Dry-run mode for safe preview
- Execute mode for actual deletion
- Detailed reporting

**Size**: ~250 lines

## Testing Recommendations

### Unit Tests

```python
def test_is_adventure_path():
    handler = QdrantHandler(config)
    
    # Should detect adventure paths
    assert handler.is_adventure_path(Path("Star Wars - Adventure.md"))
    assert handler.is_adventure_path(Path("D&D Adventure Path - Test.md"))
    assert handler.is_adventure_path(Path("adventure.md"))
    
    # Should NOT detect non-adventure paths
    assert not handler.is_adventure_path(Path("Core Rulebook.md"))
    assert not handler.is_adventure_path(Path("NPC Guide.md"))

def test_collection_routing():
    handler = QdrantHandler(config)
    
    # Adventure paths
    assert handler.determine_collection(Path("Adventure.md")) == config.qdrant_collection_adventurepaths
    
    # Rulebooks
    assert handler.determine_collection(Path("Rulebook.md")) == config.qdrant_collection_rulebooks

def test_npc_extraction_skip():
    processor = ImportProcessor(config)
    result = processor.process_file(Path("Test Adventure.md"), extract_npcs=True)
    
    assert result.skipped_npc_extraction == True
    assert result.npcs_extracted == 0
```

### Integration Tests

1. **Test Adventure Path Import**:
   ```bash
   python cli.py import --file "test_adventure.md"
   # Verify: routed to adventure_paths, no NPCs extracted
   ```

2. **Test Rulebook Import**:
   ```bash
   python cli.py import --file "test_rulebook.md"
   # Verify: routed to rulebooks, NPCs extracted if present
   ```

3. **Test Cleanup Script**:
   ```bash
   python cleanup_adventure_paths.py --dry-run
   # Verify: correctly identifies misplaced data
   ```

## Performance Impact

**Minimal**: 
- Added one additional method call per file (`is_adventure_path()`)
- Simple string operation - O(n) where n is filename length
- No database queries added
- No significant memory overhead

## Backward Compatibility

**Breaking Changes**: None

**Migration Required**: 
- Existing adventure path data in rulebooks collection should be cleaned up
- Existing adventure-specific NPCs should be removed
- Re-import adventure paths after applying fix

## Deployment Steps

1. **Backup** - Create Qdrant snapshot
2. **Apply Fix** - Update code files
3. **Test** - Verify with single file import
4. **Clean Up** - Run cleanup script in dry-run mode
5. **Execute Cleanup** - Delete misplaced data
6. **Re-import** - Re-import adventure path files
7. **Verify** - Check Qdrant dashboard

## Monitoring

Add logging to track:
- Number of files routed to each collection
- Number of times NPC extraction was skipped
- Any errors during cleanup

Example metrics:
```json
{
  "adventure_paths_imported": 15,
  "rulebooks_imported": 42,
  "npcs_extracted": 127,
  "npc_extractions_skipped": 15,
  "cleanup_chunks_deleted": 635,
  "cleanup_npcs_deleted": 23
}
```

## Future Improvements

1. **More Flexible Detection**: Allow configuration of keywords to detect adventure paths
2. **Validation**: Add pre-import validation to warn about potential misrouting
3. **Automated Tests**: Add CI tests for collection routing
4. **Configuration Option**: Allow disabling NPC extraction per file type in config
5. **Metadata Tags**: Add explicit "file_type" metadata field

## Related Issues

This fix addresses the following scenarios:

- ✅ Files with "adventure" in name routed correctly
- ✅ NPCs not extracted from adventure paths
- ✅ Campaign-specific characters kept separate
- ✅ Existing misplaced data can be cleaned up
- ✅ Import statistics track skipped extractions

## Version Compatibility

- **Python**: 3.8+
- **Qdrant**: 1.7.0+
- **Dependencies**: No new dependencies added

## Documentation Updates

Update the following docs:
- [ ] README.md - Add note about adventure path handling
- [ ] CONTRIBUTING.md - Add testing requirements for collection routing
- [ ] API.md - Document `is_adventure_path()` method
- [ ] CHANGELOG.md - Add entry for this fix
