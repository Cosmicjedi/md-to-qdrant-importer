# Star Wars D6 Content Guide

## Overview

The MD to Qdrant Importer includes special handling for **Star Wars D6 RPG** content, with dedicated collections for rulebooks and adventure paths.

## Collection Structure

The importer creates four collections optimized for Star Wars D6 content:

### 1. `{prefix}_rulebooks`
**Purpose**: Store core rulebook content and game system rules

**Content Types:**
- Core rulebooks (1st Edition, 2nd Edition R&E, etc.)
- Sourcebooks (Galaxy Guide series)
- Rules compendiums
- Equipment guides
- Vehicle/starship guides
- Character creation rules
- Combat and skill rules

**Automatic Detection:**
Files containing these keywords in the filename are automatically routed here:
- "rulebook"
- "core rules"
- "rules"
- "handbook"
- "guide"
- "manual"
- "compendium"

### 2. `{prefix}_adventurepaths`
**Purpose**: Store adventure path and campaign content

**Content Types:**
- Full adventure paths (multi-session campaigns)
- Single adventures
- Campaign frameworks
- Adventure hooks and seeds
- NPC encounters for adventures
- Location descriptions for adventures
- Plot outlines and story arcs

**Automatic Detection:**
Files containing "adventure path" or "adventurepath" in the filename are automatically routed here.

### 3. `{prefix}_npcs`
**Purpose**: Store extracted NPC stat blocks

**Content Types:**
- Named NPCs with full stats
- Generic NPCs (Stormtrooper, Rebel Soldier)
- Alien species templates
- Droid templates
- Vehicle/creature stats

**Automatic Detection:**
NPCs are extracted from ANY source file (rulebook, adventure path, or general) using Azure AI.

### 4. `{prefix}_general`
**Purpose**: Catch-all for other content

**Content Types:**
- House rules
- Campaign notes
- Session summaries
- Custom content
- Lore documents
- Player handouts

## File Naming Conventions

To ensure proper automatic classification, use these naming patterns:

### Rulebooks
```
star_wars_d6_rulebook_combat.md
2nd_edition_rulebook_force_powers.md
galaxy_guide_1_rulebook.md
rules_compendium_vehicles.md
```

### Adventure Paths
```
shadows_of_the_empire_adventure_path.md
star_wars_d6_adventure_path_dark_forces.md
beginners_adventure_path.md
```

### General Content
```
campaign_notes_session_1.md
custom_force_powers.md
house_rules.md
player_handout_tatooine.md
```

## Example Files

The `examples/` directory includes Star Wars D6 content:

1. **star_wars_d6_rulebook_combat.md** - Example rulebook content (combat system)
2. **star_wars_d6_adventure_path_shadows.md** - Example adventure path (Shadows of the Empire)
3. **goblin.md** - Generic NPC example (replace with Star Wars NPCs for your game)

## Querying Star Wars D6 Content

### Search Rulebooks

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# Find combat rules
combat_rules = client.search(
    collection_name="game_rulebooks",
    query_text="blaster combat attack roll",
    limit=5
)

# Find Force power rules
force_rules = client.search(
    collection_name="game_rulebooks",
    query_text="Force points dark side",
    limit=5
)

# Find vehicle rules
vehicle_rules = client.search(
    collection_name="game_rulebooks",
    query_text="starfighter scale damage",
    limit=5
)
```

### Search Adventure Paths

```python
# Find adventure with specific themes
adventure = client.search(
    collection_name="game_adventurepaths",
    query_text="bounty hunter chase imperial",
    limit=3
)

# Find adventures by location
tatooine_adventures = client.search(
    collection_name="game_adventurepaths",
    query_text="tatooine desert cantina",
    limit=5
)

# Find adventures by difficulty
beginner_adventures = client.search(
    collection_name="game_adventurepaths",
    query_text="beginning characters starting adventure",
    limit=3
)
```

### Search NPCs

```python
# Find specific NPC type
stormtroopers = client.search(
    collection_name="game_npcs",
    query_text="stormtrooper imperial soldier",
    limit=10
)

# Find Force users
jedi = client.search(
    collection_name="game_npcs",
    query_text="jedi knight force powers lightsaber",
    limit=5
)

# Filter by challenge rating equivalent
powerful_npcs = client.scroll(
    collection_name="game_npcs",
    scroll_filter={
        "must": [
            {"key": "canonical", "match": {"value": True}},
            # Assuming attribute totals stored
            {"key": "total_attributes", "range": {"gte": 18}}
        ]
    }
)
```

### Cross-Collection Queries

```python
# Find all content related to a topic
def search_all_collections(query_text, limit=5):
    collections = [
        "game_general",
        "game_npcs", 
        "game_rulebooks",
        "game_adventurepaths"
    ]
    
    all_results = []
    for collection in collections:
        try:
            results = client.search(
                collection_name=collection,
                query_text=query_text,
                limit=limit
            )
            all_results.extend([(r, collection) for r in results])
        except:
            continue
    
    # Sort by score
    all_results.sort(key=lambda x: x[0].score, reverse=True)
    return all_results[:limit]

# Example: Find everything about Boba Fett
boba_fett_content = search_all_collections("Boba Fett bounty hunter")
```

## Organizing Your Content

### Recommended Directory Structure

```
star_wars_d6/
├── rulebooks/
│   ├── 1st_edition_rulebook.md
│   ├── 2nd_edition_revised_rulebook.md
│   ├── galaxy_guide_1_rulebook.md
│   └── sourcebook_starships_rulebook.md
│
├── adventures/
│   ├── shadows_of_the_empire_adventure_path.md
│   ├── dark_forces_adventure_path.md
│   └── tattooine_manhunt_adventure_path.md
│
├── campaigns/
│   ├── my_campaign_notes.md
│   └── session_summaries.md
│
└── custom/
    ├── house_rules.md
    └── custom_npcs.md
```

### Bulk Import Example

```bash
# Import all Star Wars D6 content
python cli.py ./star_wars_d6/ --stats

# Or use GUI and point to the directory
python gui.py
# Select: ./star_wars_d6/
# Enable NPC Extraction: ✓
# Start Import
```

## Content Type Metadata

Each imported chunk includes metadata indicating its content type:

```json
{
  "text": "Combat rounds are divided into...",
  "content_type": "rulebook",
  "source_file": "star_wars_d6_rulebook_combat.md",
  "chunk_index": 0,
  "total_chunks": 45,
  // ... other metadata
}
```

**Content Types:**
- `"rulebook"` - From rulebook collection
- `"adventure_path"` - From adventure path collection
- `"npc"` - From NPC collection
- `"general"` - From general collection

## Advanced Use Cases

### Building a Game Master Assistant

```python
class StarWarsGMAssistant:
    def __init__(self, client, prefix="game"):
        self.client = client
        self.prefix = prefix
    
    def quick_rule_lookup(self, query):
        """Look up a rule quickly"""
        return self.client.search(
            collection_name=f"{self.prefix}_rulebooks",
            query_text=query,
            limit=3
        )
    
    def find_adventure_by_theme(self, theme, difficulty="moderate"):
        """Find adventure matching theme and difficulty"""
        query = f"{theme} {difficulty} adventure"
        return self.client.search(
            collection_name=f"{self.prefix}_adventurepaths",
            query_text=query,
            limit=5
        )
    
    def random_encounter(self, location):
        """Get NPCs appropriate for a location"""
        return self.client.search(
            collection_name=f"{self.prefix}_npcs",
            query_text=location,
            limit=10
        )
    
    def prep_session(self, theme, location, difficulty):
        """Prepare a session with relevant content"""
        return {
            'adventure': self.find_adventure_by_theme(theme, difficulty),
            'npcs': self.random_encounter(location),
            'rules': self.quick_rule_lookup(f"{theme} rules")
        }

# Usage
gm = StarWarsGMAssistant(client)
session = gm.prep_session("bounty hunter", "mos eisley", "moderate")
```

### Campaign Management

```python
# Track which content is used in your campaign
def tag_content_for_campaign(point_id, campaign_name):
    """Add campaign tag to existing content"""
    client.set_payload(
        collection_name="game_general",
        payload={
            "campaigns": [campaign_name]
        },
        points=[point_id]
    )

# Query content used in specific campaign
campaign_content = client.scroll(
    collection_name="game_adventurepaths",
    scroll_filter={
        "must": [
            {"key": "campaigns", "match": {"value": "rebellion_era"}}
        ]
    }
)
```

## Tips for Best Results

### 1. Consistent Naming
Use clear, consistent file naming patterns:
- ✅ `star_wars_d6_rulebook_chapter1.md`
- ✅ `adventure_path_tatooine_escape.md`
- ❌ `stuff.md`
- ❌ `temp_notes_2.md`

### 2. Structured Content
Keep markdown well-structured with headers:
```markdown
# Main Topic

## Subtopic 1

Content here...

## Subtopic 2

More content...
```

### 3. NPC Stat Blocks
Format NPCs clearly for better extraction:
```markdown
# Stormtrooper

**Attributes:**
- DEX: 3D
- KNO: 2D
- MEC: 2D
- PER: 2D
- STR: 3D
- TEC: 2D

**Skills:**
- Blaster: 4D
- Dodge: 4D
- Brawling: 4D

**Equipment:**
- Stormtrooper armor (+2D physical, +1D energy)
- Blaster rifle (5D damage)
```

### 4. Metadata in Files
Consider adding metadata at the top of files:
```markdown
---
type: rulebook
edition: 2nd Revised & Expanded
chapter: Combat
difficulty: core rules
---

# Combat Rules

...
```

## Troubleshooting

### Content Goes to Wrong Collection

**Problem**: Rulebook content going to general collection

**Solution**: Ensure filename contains keywords like "rulebook", "rules", "handbook", etc.

**Manual Override**: You can manually move content between collections using Qdrant API

### NPCs Not Extracted

**Problem**: NPC stat blocks not detected

**Solution**: 
1. Check Azure AI configuration
2. Verify NPC stat blocks are clearly formatted
3. Review confidence threshold in `.env`
4. Check logs for extraction attempts

### Search Not Finding Content

**Problem**: Queries not returning expected results

**Solution**:
1. Try broader search terms
2. Search across all collections
3. Check content was actually imported
4. Verify embeddings are working

## Summary

The four-collection system provides:
- ✅ **Organization** - Content automatically categorized
- ✅ **Performance** - Targeted searches in specific collections
- ✅ **Flexibility** - Mix rulebooks, adventures, and custom content
- ✅ **Scalability** - Easy to add more Star Wars D6 content

Perfect for Game Masters running Star Wars D6 campaigns! 🎲✨
