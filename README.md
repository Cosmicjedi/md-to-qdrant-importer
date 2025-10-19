# MD to Qdrant Importer

A GUI application for bulk importing markdown files into Qdrant vector database with intelligent NPC extraction using Azure AI services.

## Features

- 🚀 **Bulk Import**: Process entire directories of markdown files
- 🧠 **Intelligent Chunking**: Semantic text splitting with configurable overlap
- 🎭 **NPC Extraction**: Automatically detect and extract NPC stat blocks using Azure OpenAI
- 📦 **Four Collections**: Separate storage for general content, NPCs, rulebooks, and adventure paths
- 🎲 **Star Wars D6 Optimized**: Special handling for rulebooks and adventure path content
- 🏷️ **Prefix Pattern**: Configurable collection naming for multi-tenancy ({prefix}_general, {prefix}_npcs, {prefix}_rulebooks, {prefix}_adventurepaths)
- 🔍 **Vector Embeddings**: Semantic search using sentence transformers
- 💾 **Skip Duplicates**: Avoid reprocessing already imported files
- 📊 **Progress Tracking**: Real-time progress updates and detailed logging
- 🖥️ **User-Friendly GUI**: Easy-to-use graphical interface

## Prerequisites

- Python 3.8 or higher
- Qdrant database running locally (default: `localhost:6333`)
- Azure OpenAI or Azure AI Services account (for NPC extraction)

## Installation

1. **Clone the repository**:
```bash
git clone https://github.com/Cosmicjedi/md-to-qdrant-importer.git
cd md-to-qdrant-importer
```

2. **Create virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.template .env
```

Edit `.env` and add your Azure credentials:
```env
AZURE_ENDPOINT=https://your-service.openai.azure.com/
AZURE_API_KEY=your-api-key-here
AZURE_DEPLOYMENT_NAME=gpt-4o
```

## Quick Start

1. **Ensure Qdrant is running**:
```bash
# Check if Qdrant is accessible
curl http://localhost:6333/health
```

2. **Prepare your markdown files**:
   - Place markdown files in the `input_md_files` directory (or configure a custom path)

3. **Launch the GUI**:
```bash
python gui.py
```

4. **Import workflow**:
   - Load/verify configuration (should auto-load from `.env`)
   - Select input directory containing markdown files
   - Configure options:
     - Include subdirectories (recursive)
     - Skip existing files
     - Extract NPCs (requires Azure AI)
   - Click "Start Import"
   - Monitor progress in the log window

## Configuration

All settings are configured in the `.env` file. See `.env.template` for available options.

### Key Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `AZURE_ENDPOINT` | Azure OpenAI endpoint | Required |
| `AZURE_API_KEY` | Azure API key | Required |
| `AZURE_DEPLOYMENT_NAME` | Model deployment name | `gpt-4o` |
| `QDRANT_HOST` | Qdrant server host | `localhost` |
| `QDRANT_PORT` | Qdrant REST API port | `6333` |
| `QDRANT_COLLECTION_PREFIX` | Prefix for collection names | `game` |
| `CHUNK_SIZE` | Text chunk size (characters) | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `ENABLE_NPC_EXTRACTION` | Enable AI-powered NPC extraction | `true` |

### Collections

The importer creates **four** collections in Qdrant using a configurable prefix:

1. **{prefix}_general**: General markdown content that doesn't fit other categories (default: `game_general`)
2. **{prefix}_npcs**: Canonical NPCs extracted from rulebooks with structured metadata (default: `game_npcs`)
3. **{prefix}_rulebooks**: Star Wars D6 rulebook content and game system rules (default: `game_rulebooks`)
4. **{prefix}_adventurepaths**: Star Wars D6 adventure path content (default: `game_adventurepaths`)

**Automatic Classification:**
Files are automatically routed to the appropriate collection based on filename:
- Files with "adventure path" in the name → `{prefix}_adventurepaths`
- Files with "rulebook", "rules", "handbook", "guide", etc. → `{prefix}_rulebooks`
- All other content → `{prefix}_general`
- NPCs are extracted and stored separately in `{prefix}_npcs` regardless of source file

You can customize the prefix by setting `QDRANT_COLLECTION_PREFIX` in your `.env` file.

## NPC Extraction

When enabled, the importer uses Azure OpenAI to:

1. **Detect** potential NPC stat blocks in text
2. **Extract** structured data:
   - Name, type, alignment, size
   - Attributes (STR, DEX, CON, INT, WIS, CHA)
   - Combat stats (AC, HP, CR, speed)
   - Skills, saving throws, abilities, actions
3. **Store** in dedicated `npcs` collection with `canonical: true` metadata

### NPC Detection Heuristics

The system uses pattern matching for efficient pre-filtering:
- Challenge Rating mentions
- Armor Class/Hit Points
- Attribute arrays
- Size/creature type descriptors

## Usage Examples

### Command Line (Advanced)

You can also import via Python script:

```python
from pathlib import Path
from config import get_config
from import_processor import ImportProcessor

# Load config
config = get_config()

# Create processor
processor = ImportProcessor(config)

# Process directory
results = processor.process_directory(
    directory=Path("./input_md_files"),
    recursive=True,
    skip_existing=True,
    extract_npcs=True
)

# Save results
processor.save_results(results, Path("./output_logs/results.json"))

# Get stats
stats = processor.get_stats()
print(stats)
```

### Querying Qdrant

After import, query your data:

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# Search for NPCs (using default prefix 'game')
results = client.search(
    collection_name="game_npcs",
    query_vector=embedding_model.encode("stormtrooper"),
    limit=10
)

# Search rulebooks
rulebook_results = client.search(
    collection_name="game_rulebooks",
    query_vector=embedding_model.encode("combat rules"),
    limit=5
)

# Search adventure paths
adventure_results = client.search(
    collection_name="game_adventurepaths",
    query_vector=embedding_model.encode("shadows of the empire"),
    limit=5
)

# Filter canonical NPCs
results = client.scroll(
    collection_name="game_npcs",
    scroll_filter={
        "must": [
            {"key": "canonical", "match": {"value": True}},
            {"key": "challenge_rating", "range": {"gte": 5}}
        ]
    }
)
```

## Troubleshooting

### Qdrant Connection Issues

```bash
# Check Qdrant is running
curl http://localhost:6333/health

# View collections
curl http://localhost:6333/collections
```

### Azure API Errors

- Verify `AZURE_ENDPOINT` includes the full URL with protocol
- Check `AZURE_API_KEY` is valid
- Ensure `AZURE_DEPLOYMENT_NAME` matches your deployed model
- Check API quotas and rate limits

### Import Failures

- Check log output for specific errors
- Verify markdown files are UTF-8 encoded
- Ensure sufficient disk space for embeddings
- Review chunk size settings for very large files

### Memory Issues

For large batches:
- Reduce `CHUNK_SIZE`
- Process files in smaller batches
- Increase system RAM or use swap

## Project Structure

```
md-to-qdrant-importer/
├── config.py              # Configuration loader
├── text_processor.py      # Text chunking and markdown processing
├── npc_extractor.py       # Azure AI-powered NPC extraction
├── qdrant_handler.py      # Qdrant database operations
├── import_processor.py    # Main import pipeline coordinator
├── gui.py                 # Tkinter GUI application
├── requirements.txt       # Python dependencies
├── .env.template          # Configuration template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black *.py
flake8 *.py
```

## Performance

Typical import speeds (on standard hardware):

- **Chunking**: ~1000 chunks/second
- **Embedding**: ~100 chunks/second (CPU), ~500 chunks/second (GPU)
- **NPC Extraction**: ~2-5 NPCs/minute (depends on Azure AI response time)

## Limitations

- NPC extraction requires Azure OpenAI API calls (costs apply)
- Large files may require significant memory for embedding
- First run downloads sentence transformer model (~90MB)

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Acknowledgments

- [Qdrant](https://qdrant.tech/) - Vector database
- [Sentence Transformers](https://www.sbert.net/) - Embeddings
- [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) - NPC extraction
- Built for the Nerdbuntu project

## Support

For issues and questions:
- GitHub Issues: https://github.com/Cosmicjedi/md-to-qdrant-importer/issues
- Discussions: https://github.com/Cosmicjedi/md-to-qdrant-importer/discussions
