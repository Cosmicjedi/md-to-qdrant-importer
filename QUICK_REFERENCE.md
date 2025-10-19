# Adventure Path Fix - Quick Reference

## TL;DR

Adventure paths were going to the wrong collection and having NPCs extracted when they shouldn't.

**Time to Fix**: ~15-20 minutes

---

## Quick Fix Guide

### 1. Backup (2 min)
```bash
# Create Qdrant snapshot
curl -X POST "http://localhost:6333/collections/your_collection/snapshots"
```

### 2. Apply Fix (5 min)

**Option A**: Use the fixed files
```bash
cp qdrant_handler_fixed.py ./qdrant_handler.py
cp import_processor_fixed.py ./import_processor.py
```

**Option B**: Manual edits - See `FIX_INSTRUCTIONS.md`

### 3. Test (3 min)
```bash
# Test single file
python cli.py import --file "Test Adventure.md"

# Should see:
# ✓ "Routing 'Test Adventure.md' to adventure paths collection"
# ✓ "Skipping NPC extraction for adventure path"
```

### 4. Cleanup Misplaced Data (10 min)
```bash
# Preview what will be deleted
python cleanup_adventure_paths.py --dry-run

# Actually delete (after reviewing!)
python cleanup_adventure_paths.py --execute
```

### 5. Re-import (varies)
```bash
# Re-import your adventure paths
python cli.py import --directory "./adventures/"
```

---

## What Changed?

### Before (Buggy):
```python
# Only checked for exact phrases
if 'adventure path' in filename or 'adventurepath' in filename:
    # Route to adventure_paths
```

❌ Missed files like "D&D Adventure.md"  
❌ Extracted NPCs from all files

### After (Fixed):
```python
# Checks for "adventure" anywhere in filename
if 'adventure' in filename:
    # Route to adventure_paths
    # Skip NPC extraction
```

✅ Catches all adventure file variations  
✅ Skips NPC extraction for adventures

---

## Files Included

| File | Purpose |
|------|---------|
| `qdrant_handler_fixed.py` | Fixed collection routing |
| `import_processor_fixed.py` | Fixed NPC extraction |
| `cleanup_adventure_paths.py` | Remove misplaced data |
| `FIX_INSTRUCTIONS.md` | Detailed step-by-step guide |
| `ADVENTURE_PATH_FIX_SUMMARY.md` | Technical details |
| `GITHUB_ISSUE.md` | GitHub issue template |

---

## Verification Checklist

After applying the fix:

- [ ] Backup created
- [ ] Code files replaced/updated
- [ ] Test import works correctly
- [ ] Adventure path routed to `adventure_paths` collection
- [ ] NPC extraction skipped (see "Skipping NPC extraction" message)
- [ ] Cleanup script run (dry-run first!)
- [ ] Misplaced data removed
- [ ] Adventure paths re-imported
- [ ] Checked Qdrant dashboard:
  - [ ] Adventure paths in correct collection
  - [ ] No new adventure-specific NPCs in NPC collection

---

## Common Issues

### "Import still going to wrong collection"
→ Check: Did you update `qdrant_handler.py`?  
→ Check: Does filename contain "adventure"?  
→ Run: `grep -n "is_adventure_path" qdrant_handler.py`

### "NPCs still being extracted"
→ Check: Did you update `import_processor.py`?  
→ Check: Look for "Skipping NPC extraction" in logs  
→ Run: `grep -n "skipped_npc_extraction" import_processor.py`

### "Cleanup script finds nothing"
→ Good! That means no misplaced data  
→ Or: Check your collection names in `.env`

---

## Quick Commands

```bash
# Show what files would be deleted
python cleanup_adventure_paths.py --dry-run

# Actually delete misplaced data
python cleanup_adventure_paths.py --execute

# Import single adventure
python cli.py import --file "path/to/adventure.md"

# Import all adventures
python cli.py import --directory "./adventures/"

# Check Qdrant collections
curl http://localhost:6333/collections
```

---

## Expected Results

### Import Output (Fixed)
```
Processing: D&D Adventure - Dragon Heist.md
Routing 'D&D Adventure - Dragon Heist.md' to adventure paths collection
Generating embeddings for 127 chunks...
Inserting chunks into Qdrant...
Skipping NPC extraction for adventure path: D&D Adventure - Dragon Heist.md
✓ Success: 127 chunks imported to adventure_paths
✓ NPCs extracted: 0 (skipped)
```

### Cleanup Output
```
Found 15 misplaced adventure path files:

📁 D&D Adventure - Dragon Heist.md
   Path: /data/adventures/dragon-heist.md
   Chunks: 127

Total chunks to delete: 1,247
Total NPCs to delete: 47

✓ Cleanup complete!
```

---

## Need More Details?

- **Step-by-step instructions**: See `FIX_INSTRUCTIONS.md`
- **Technical details**: See `ADVENTURE_PATH_FIX_SUMMARY.md`
- **GitHub issue template**: See `GITHUB_ISSUE.md`

---

## Support

If you run into issues:
1. Check the logs in import results JSON
2. Verify `.env` configuration
3. Check Qdrant dashboard: http://localhost:6333/dashboard
4. Review `FIX_INSTRUCTIONS.md` troubleshooting section

---

## Success Criteria

You'll know it's working when:
- ✅ Adventure files route to `adventure_paths` collection
- ✅ "Skipping NPC extraction" appears in logs
- ✅ No adventure-specific NPCs in general NPC collection
- ✅ Qdrant dashboard shows data in correct collections

---

**Remember**: Always run cleanup in `--dry-run` mode first!
