# Collection Naming Guide

## Overview

The MD to Qdrant Importer uses a **prefix-based naming pattern** for Qdrant collections to support multi-tenancy and better organization.

## Pattern

All collections are named with a configurable prefix:

```
{prefix}_general  - General chunked content
{prefix}_npcs     - Canonical NPC data
```

## Default Configuration

By default, the prefix is `"game"`, which creates:

- `game_general` - For all general markdown content
- `game_npcs` - For extracted NPC stat blocks

## Customizing the Prefix

### In `.env` File

```env
QDRANT_COLLECTION_PREFIX=game
```

Change `game` to any valid collection name prefix you want.

### Examples

**Campaign-specific collections:**
```env
QDRANT_COLLECTION_PREFIX=campaign_stormcrown
# Creates: campaign_stormcrown_general, campaign_stormcrown_npcs
```

**System-specific collections:**
```env
QDRANT_COLLECTION_PREFIX=dnd5e
# Creates: dnd5e_general, dnd5e_npcs
```

**Multi-tenant usage:**
```env
QDRANT_COLLECTION_PREFIX=user_12345
# Creates: user_12345_general, user_12345_npcs
```

## Use Cases

### 1. Multiple Campaigns

Separate data for different campaigns:

```bash
# Campaign 1
QDRANT_COLLECTION_PREFIX=campaign_winterfell
python cli.py ./campaigns/winterfell/

# Campaign 2
QDRANT_COLLECTION_PREFIX=campaign_sunspear
python cli.py ./campaigns/sunspear/
```

Result:
- `campaign_winterfell_general` and `campaign_winterfell_npcs`
- `campaign_sunspear_general` and `campaign_sunspear_npcs`

### 2. Multiple Game Systems

Organize by RPG system:

```bash
# D&D 5e content
QDRANT_COLLECTION_PREFIX=dnd5e
python cli.py ./systems/dnd5e/

# Pathfinder content
QDRANT_COLLECTION_PREFIX=pathfinder
python cli.py ./systems/pathfinder/
```

### 3. Shared vs Campaign-Specific

Use different prefixes for shared rulebooks vs campaign data:

```env
# For core rulebooks (shared)
QDRANT_COLLECTION_PREFIX=core

# For campaign-specific content
QDRANT_COLLECTION_PREFIX=campaign_current
```

Then query across collections:

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# Search core rulebooks
core_npcs = client.search(
    collection_name="core_npcs",
    query_text="ancient dragon",
    limit=5
)

# Search campaign NPCs
campaign_npcs = client.search(
    collection_name="campaign_current_npcs",
    query_text="ancient dragon",
    limit=5
)

# Combine results
all_npcs = core_npcs + campaign_npcs
```

## Querying with Prefixes

### Basic Search

```python
from qdrant_client import QdrantClient

prefix = "game"  # or load from config

client = QdrantClient(host="localhost", port=6333)

# Search general content
results = client.search(
    collection_name=f"{prefix}_general",
    query_text="combat rules",
    limit=10
)

# Search NPCs
npcs = client.search(
    collection_name=f"{prefix}_npcs",
    query_text="dragon",
    limit=10
)
```

### Filtering Canonical NPCs

```python
# Get only canonical (rulebook) NPCs
canonical_npcs = client.scroll(
    collection_name=f"{prefix}_npcs",
    scroll_filter={
        "must": [
            {"key": "canonical", "match": {"value": True}}
        ]
    }
)
```

### Cross-Campaign Queries

```python
# Search across multiple campaign collections
campaigns = ["winterfell", "sunspear", "kingslanding"]

all_results = []
for campaign in campaigns:
    results = client.search(
        collection_name=f"campaign_{campaign}_general",
        query_text="prophecy",
        limit=5
    )
    all_results.extend(results)
```

## Best Practices

### 1. Naming Conventions

✅ **Good prefixes:**
- `game` - Simple, generic
- `dnd5e` - Clear system identifier
- `campaign_lost_mines` - Descriptive, unique
- `user_johndoe` - Multi-tenant identifier

❌ **Avoid:**
- `my-campaign` - Hyphens (use underscores)
- `Campaign 2024` - Spaces (use underscores)
- Very long names (keep under 30 characters)

### 2. Consistency

- Use the same prefix for related imports
- Document your prefix choices
- Use environment-specific configs

### 3. Migration

When changing prefixes:

```bash
# Old collection
old_prefix="game"

# New collection
new_prefix="dnd5e_core"

# Option 1: Re-import with new prefix
QDRANT_COLLECTION_PREFIX=$new_prefix python cli.py ./data/

# Option 2: Copy in Qdrant (if supported)
# Use Qdrant's collection management API
```

## Configuration Management

### Multiple Environments

Create different `.env` files:

```bash
# .env.dev
QDRANT_COLLECTION_PREFIX=dev_game

# .env.staging
QDRANT_COLLECTION_PREFIX=staging_game

# .env.prod
QDRANT_COLLECTION_PREFIX=game
```

Then load appropriately:

```bash
# Development
cp .env.dev .env
python cli.py ./data/

# Production
cp .env.prod .env
python cli.py ./data/
```

### Programmatic Override

```python
from config import Config

# Override prefix programmatically
import os
os.environ['QDRANT_COLLECTION_PREFIX'] = 'custom_prefix'

config = Config()
print(config.qdrant_collection_general)  # custom_prefix_general
print(config.qdrant_collection_npcs)     # custom_prefix_npcs
```

## Collection Management

### List All Collections

```bash
curl http://localhost:6333/collections | jq '.result.collections[].name'
```

### View Collection Info

```bash
# Replace 'game' with your prefix
curl http://localhost:6333/collections/game_general
curl http://localhost:6333/collections/game_npcs
```

### Delete Collections

```bash
# Be careful - this is permanent!
curl -X DELETE http://localhost:6333/collections/game_general
curl -X DELETE http://localhost:6333/collections/game_npcs
```

## FAQ

**Q: Can I change the prefix after importing data?**
A: Yes, but you'll need to re-import the data. The prefix is part of the collection name and can't be renamed.

**Q: What's the default prefix?**
A: `"game"` - creating `game_general` and `game_npcs` collections.

**Q: Can I use the same prefix for different data?**
A: Not recommended. Each prefix should represent a distinct dataset to avoid confusion.

**Q: How do I share NPCs across campaigns?**
A: Import core rulebooks with a shared prefix (e.g., `"core"`), then query both `core_npcs` and `campaign_specific_npcs` collections.

**Q: Is there a limit to prefix length?**
A: Qdrant collection names are limited to 255 characters, but keep prefixes under 30 characters for readability.

**Q: Can I use the same Qdrant instance for multiple users?**
A: Yes! Use user-specific prefixes: `user_johndoe_general`, `user_janedoe_general`, etc.

## Summary

The prefix pattern provides:
- ✅ **Flexibility** - Organize data your way
- ✅ **Multi-tenancy** - Multiple users/campaigns on one Qdrant instance
- ✅ **Clarity** - Clear separation of datasets
- ✅ **Scalability** - Easy to add new collections
- ✅ **Simplicity** - Configurable via environment variable

Default setup works great, but the prefix system is there when you need it!
