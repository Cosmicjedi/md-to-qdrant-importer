# Adventure Path Bug Fix Instructions

## Overview

This guide will walk you through fixing the adventure path routing bug in your md-to-qdrant-importer.

**Estimated Time:** 15-20 minutes

## Prerequisites

- Backup your Qdrant database (see Step 1)
- Python environment with all dependencies installed
- Access to your repository

---

## Step 1: Backup Your Data (5 minutes)

### Option A: Qdrant Snapshot

```bash
# Create a snapshot of your Qdrant data
curl -X POST "http://localhost:6333/collections/your_collection_name/snapshots"

# List available snapshots
curl "http://localhost:6333/collections/your_collection_name/snapshots"

# Download snapshot (replace {snapshot-name} with actual name)
curl "http://localhost:6333/collections/your_collection_name/snapshots/{snapshot-name}" \
  --output backup.snapshot
```

### Option B: Export Data via Script

```bash
# Run the backup script (if you have one)
python scripts/backup_qdrant.py --output ./backups/
```

---

## Step 2: Apply the Fix (5 minutes)

### Option A: Manual Code Changes

1. **Update `qdrant_handler.py`**:
   
   Add this method after the `_ensure_collections()` method (around line 40):
   
   ```python
   def is_adventure_path(self, file_path: Path) -> bool:
       """
       Check if a file is an adventure path.
       
       FIXED: Now checks for just "adventure" in the filename
       """
       filename_lower = file_path.name.lower()
       return "adventure" in filename_lower
   ```

2. **Update `determine_collection()` method** (around line 50):
   
   ```python
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

3. **Update `import_processor.py`**:

   In the `ImportResult` dataclass (around line 18), add this field:
   
   ```python
   skipped_npc_extraction: bool = False  # Track if NPC extraction was skipped
   ```

4. In the `process_file()` method (around line 75), add after file processing:
   
   ```python
   # Check if this is an adventure path
   is_adventure_path = self.qdrant.is_adventure_path(file_path)
   ```

5. Replace the NPC extraction section (around line 90) with:
   
   ```python
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

6. Update the return statement to include `skipped_npc_extraction=skipped_npc_extraction`

7. In `save_results()` method (around line 210), add to `output_data`:
   
   ```python
   'adventure_paths_skipped_npc': sum(1 for r in results if r.skipped_npc_extraction),
   ```

### Option B: Replace Files Completely

Copy the fixed files from the artifacts to your repository:

```bash
# Download the fixed files from the artifacts
# Then copy them to your repo:
cp qdrant_handler_fixed.py ./qdrant_handler.py
cp import_processor_fixed.py ./import_processor.py
```

---

## Step 3: Test the Fix (5 minutes)

### Quick Test

```bash
# Test with a single adventure file
python cli.py import --file "path/to/adventure-file.md"

# Check the output - it should show:
# - Routing to adventure_paths collection
# - Skipping NPC extraction message
```

### Verify in Qdrant Dashboard

1. Open Qdrant dashboard: http://localhost:6333/dashboard
2. Check the adventure_paths collection
3. Verify the adventure file appears there
4. Check the NPCs collection
5. Verify no new NPCs were added from the adventure file

---

## Step 4: Clean Up Existing Data (Optional, 10 minutes)

### Run Cleanup Script in Dry-Run Mode

```bash
# See what would be deleted
python cleanup_adventure_paths.py --dry-run
```

The script will show:
- Adventure path chunks in the rulebooks collection
- NPCs extracted from adventure paths

### Review the Output

Example output:
```
Found 5 misplaced adventure path files:

📁 Adventure - Shadows of the Empire.md
   Path: /path/to/file.md
   Chunks: 127

Total chunks to delete: 635
Total NPCs to delete: 23
```

### Execute Cleanup (if desired)

```bash
# ONLY run this after reviewing the dry-run output!
python cleanup_adventure_paths.py --execute
```

**⚠️ WARNING**: This permanently deletes data. Make sure you have backups!

---

## Step 5: Re-import Adventure Paths

After cleaning up the misplaced data:

```bash
# Re-import all adventure path files
python cli.py import --directory "./adventures/" --pattern "*.md"
```

---

## Verification Checklist

- [ ] Backup created
- [ ] Code changes applied
- [ ] Test import successful
- [ ] Adventure path routed to correct collection
- [ ] NPC extraction skipped for adventure paths
- [ ] Cleanup script run (if needed)
- [ ] Adventure paths re-imported
- [ ] Verified in Qdrant dashboard

---

## Troubleshooting

### Issue: Import still going to wrong collection

**Solution**: 
- Check that `is_adventure_path()` method exists in `qdrant_handler.py`
- Verify the method is being called in `determine_collection()`
- Check your file names contain "adventure"

### Issue: NPCs still being extracted

**Solution**:
- Verify the changes in `import_processor.py` were applied
- Check the log output for "Skipping NPC extraction" message
- Ensure `is_adventure_path` check happens before NPC extraction

### Issue: Cleanup script not finding files

**Solution**:
- Check your Qdrant connection settings in `.env`
- Verify collection names match your configuration
- Try running with `--dry-run` first to see detailed output

---

## Summary of Changes

### qdrant_handler.py
- ✅ Added `is_adventure_path()` helper method
- ✅ Fixed `determine_collection()` to check for "adventure" anywhere in filename
- ✅ Now properly routes adventure paths to adventure_paths collection

### import_processor.py
- ✅ Added `skipped_npc_extraction` field to track when NPC extraction is skipped
- ✅ Modified `process_file()` to skip NPC extraction for adventure paths
- ✅ Updated results reporting to show skipped NPC extractions

### New Files
- ✅ `cleanup_adventure_paths.py` - Utility to clean up misplaced data
- ✅ Documentation and instructions

---

## Need Help?

If you encounter issues:
1. Check the logs in the import results JSON
2. Review the Qdrant dashboard
3. Verify your `.env` configuration
4. Check that collection names match your config

## Next Steps

After successfully applying the fix:
1. Update your project README to document the fix
2. Consider adding a test case for adventure path detection
3. Add validation to prevent this issue in the future
