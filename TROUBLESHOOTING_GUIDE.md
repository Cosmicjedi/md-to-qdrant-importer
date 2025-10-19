# Troubleshooting Guide: Collection Prefix Issue

## The Problem You're Seeing

You're seeing both `game_*` collections AND `swd6_knowledge_*` collections in your Qdrant database, even though you only want the `swd6_knowledge_*` collections.

## Why This Is Happening

There are two possible reasons:

### Reason 1: The Fix Hasn't Been Applied Yet (Most Likely)
The `game_*` collections you're seeing were created **before** the fix was applied. The fix prevents new unwanted collections from being created, but doesn't delete existing ones.

### Reason 2: The GUI Wasn't Restarted After Applying the Fix
Even if you applied the fix, if you didn't completely restart the GUI application, it's still using the old code in memory.

## Step-by-Step Solution

### Step 1: Verify the Fix Is Applied

Check your `config.py` file. Look for these lines (around line 19-22):

**INCORRECT (Old Code)**:
```python
if env_file:
    load_dotenv(env_file, override=True)  # ❌ Wrong!
else:
    load_dotenv(override=True)            # ❌ Wrong!
```

**CORRECT (Fixed Code)**:
```python
if env_file:
    load_dotenv(env_file, override=False)  # ✅ Correct!
else:
    load_dotenv(override=False)            # ✅ Correct!
```

If your code says `override=True`, the fix hasn't been applied yet. Apply it by:
- Merging Pull Request #2, OR
- Manually changing `override=True` to `override=False` in both places

### Step 2: Completely Restart the GUI Application

**Critical**: You MUST restart the application for the fix to take effect!

1. **Close** the GUI completely (don't just minimize it)
2. **Wait** 5 seconds
3. **Start** the GUI again with `python gui.py` or `start_gui.bat`

### Step 3: Delete the Old `game_*` Collections

The `game_*` collections you're seeing are from before the fix. Delete them using the cleanup script:

```bash
# First, list all collections to see what you have
python cleanup_collections.py --list

# Preview what will be deleted (safe - doesn't actually delete)
python cleanup_collections.py game --dry-run

# Actually delete the game_* collections
python cleanup_collections.py game
```

**What the cleanup script will do**:
1. Find all collections starting with `game_`
2. Show you how many points (data) each has
3. Ask for confirmation before deleting
4. Delete the collections permanently

**Sample Output**:
```
Found 3 collection(s) with prefix 'game_':
  - game_npcs (8 points)
  - game_rulebooks (8 points)
  - game_adventurepaths (8 points)

⚠️  WARNING: This will permanently delete these collections and all their data!
Type 'yes' to confirm deletion: yes

Deleting collections...
  ✓ Deleted: game_npcs
  ✓ Deleted: game_rulebooks
  ✓ Deleted: game_adventurepaths

✓ Cleanup complete!
```

### Step 4: Verify the Fix Works

Now test that the fix is working:

1. Open the GUI
2. Change the prefix to something new (e.g., "test_prefix")
3. Click "Update Collections"
4. Run `python cleanup_collections.py --list`
5. You should see ONLY:
   - `test_prefix_npcs`
   - `test_prefix_rulebooks`
   - `test_prefix_adventurepaths`
6. You should NOT see any `game_*` collections

### Step 5: Set Your Desired Prefix

Once you've verified the fix works:

1. In the GUI, set the prefix to `swd6_knowledge`
2. Click "Update Collections"
3. Import your data

## Common Mistakes

### ❌ Mistake 1: Not Restarting the GUI
**Problem**: You applied the fix but didn't restart the GUI application.
**Solution**: Close the GUI completely and restart it.

### ❌ Mistake 2: Only Changing the Prefix, Not Applying the Fix
**Problem**: You changed the prefix in the GUI but didn't fix the code.
**Solution**: Apply the fix in `config.py` first, THEN change the prefix.

### ❌ Mistake 3: Expecting Old Collections to Be Deleted Automatically
**Problem**: You think the fix will delete existing `game_*` collections.
**Solution**: Use the cleanup script to manually delete old collections.

### ❌ Mistake 4: Not Using the Cleanup Script Correctly
**Problem**: Running the script without understanding what it does.
**Solution**: Always run with `--dry-run` first to preview what will be deleted.

## Verification Checklist

Use this checklist to ensure everything is working:

- [ ] `config.py` has `override=False` (not `override=True`)
- [ ] GUI application was completely restarted after applying fix
- [ ] Cleanup script was run to delete old `game_*` collections
- [ ] Test with a new prefix shows only that prefix's collections are created
- [ ] No unwanted `game_*` collections appear when changing prefix
- [ ] Your desired `swd6_knowledge_*` collections exist and contain data

## Quick Reference Commands

```bash
# Check what collections exist
python cleanup_collections.py --list

# Preview deletion (safe - doesn't actually delete)
python cleanup_collections.py game --dry-run

# Delete game_* collections
python cleanup_collections.py game

# Start the GUI
python gui.py
# OR on Windows:
start_gui.bat
```

## Expected Final State

After completing all steps, you should have:

**Collections in Qdrant**:
- `swd6_knowledge_npcs` ✓
- `swd6_knowledge_rulebooks` ✓
- `swd6_knowledge_adventurepaths` ✓

**Collections NOT in Qdrant**:
- `game_npcs` ✗
- `game_rulebooks` ✗
- `game_adventurepaths` ✗

## Still Having Issues?

If you're still seeing the problem after following all these steps:

1. **Check the code**: Open `config.py` and verify it says `override=False`
2. **Check the .env file**: Look for `QDRANT_COLLECTION_PREFIX=` - what does it say?
3. **Check running processes**: Make sure there's no old GUI process still running
4. **List collections**: Run `python cleanup_collections.py --list` and share the output
5. **Check the PR**: Make sure PR #2 is merged into main

## Technical Details

**Why does this happen?**

When `load_dotenv(override=True)` is used, it loads the `.env` file and overwrites any environment variables that were set programmatically. So when the GUI sets `os.environ['QDRANT_COLLECTION_PREFIX'] = 'swd6_knowledge'`, and then the config reloads with `override=True`, it gets overwritten back to `game` from the `.env` file.

**Why doesn't the fix delete old collections?**

The fix only changes HOW collections are created going forward. It doesn't affect collections that already exist in the database. Those need to be manually deleted using the cleanup script.

**Is it safe to delete the game_* collections?**

Yes, IF you don't need that data. The cleanup script shows you how many points are in each collection before deleting. If you see important data, you may want to export it first, or rename the collections instead of deleting them.

## Need Help?

If you're still stuck:
1. Run `python cleanup_collections.py --list` and note the output
2. Check your `config.py` file and note what it says for `override=`
3. Open an issue on GitHub with this information
