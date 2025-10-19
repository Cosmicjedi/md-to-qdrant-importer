# Quick Start Guide

Get up and running with MD to Qdrant Importer in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:

1. ✅ **Python 3.8+** installed
   ```bash
   python3 --version
   ```

2. ✅ **Qdrant running locally**
   ```bash
   # Test Qdrant connection
   curl http://localhost:6333/health
   
   # Expected response: {"title":"qdrant - vector search engine","version":"..."}
   ```

3. ✅ **Azure OpenAI credentials** (for NPC extraction)
   - Endpoint URL
   - API Key
   - Deployment name

## Installation (5 steps)

### Step 1: Clone and Enter Directory
```bash
git clone https://github.com/Cosmicjedi/md-to-qdrant-importer.git
cd md-to-qdrant-importer
```

### Step 2: Run Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Prompt you to create `.env` file

### Step 3: Configure Azure Credentials

Edit `.env` file and add your Azure details:

```bash
nano .env
```

**Required settings:**
```env
AZURE_ENDPOINT=https://your-service.openai.azure.com/
AZURE_API_KEY=your-actual-api-key-here
AZURE_DEPLOYMENT_NAME=gpt-4o
```

Save and exit (Ctrl+X, then Y, then Enter)

### Step 4: Prepare Input Files

Create input directory and add markdown files:

```bash
mkdir -p input_md_files
# Copy your MD files here, or use examples:
cp examples/*.md input_md_files/
```

### Step 5: Run the Importer

**Option A: GUI (Recommended for beginners)**
```bash
source venv/bin/activate
python gui.py
```

Then in the GUI:
1. Verify config is loaded (green checkmark)
2. Select input directory
3. Check desired options
4. Click "Start Import"
5. Watch progress in log window

**Option B: CLI (For automation)**
```bash
source venv/bin/activate
python cli.py ./input_md_files --stats
```

## Verify Import

Check that data was imported:

```bash
# View collections
curl http://localhost:6333/collections

# Count points in general content (default prefix: 'game')
curl http://localhost:6333/collections/game_general

# Count NPCs
curl http://localhost:6333/collections/game_npcs
```

## Next Steps

### Query Your Data

Python example:
```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# Search for content (using default prefix 'game')
results = client.search(
    collection_name="game_general",
    query_text="dragon fire breath",
    limit=5
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Text: {result.payload['text'][:200]}")
    print()
```

### Customize Settings

Edit `.env` to adjust:
- `QDRANT_COLLECTION_PREFIX`: Change collection naming (default: "game" → game_general, game_npcs)
- `CHUNK_SIZE`: Larger = fewer chunks, more context per chunk
- `CHUNK_OVERLAP`: Larger = more redundancy, better context preservation
- `EMBEDDING_MODEL`: Different models have different tradeoffs
- `ENABLE_NPC_EXTRACTION`: Disable to skip Azure AI calls

### Process More Files

1. Add more MD files to `input_md_files`
2. Run importer again (it will skip already-processed files)
3. Or use `--no-skip-existing` to reprocess

## Troubleshooting

### "Configuration errors: AZURE_API_KEY is required"
- Edit `.env` and add your actual Azure credentials
- Make sure there are no quotes around values

### "Connection refused" (Qdrant)
- Start Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
- Or check your Qdrant service status

### "No module named 'qdrant_client'"
- Activate virtual environment: `source venv/bin/activate`
- Or reinstall: `pip install -r requirements.txt`

### NPC extraction not working
- Verify Azure credentials are correct
- Check Azure API quotas/rate limits
- Look for API error messages in logs

### Out of memory
- Reduce `CHUNK_SIZE` in `.env`
- Process files in smaller batches
- Close other memory-intensive applications

## Examples

### CLI Examples

```bash
# Process with all options
python cli.py ./input_md_files --stats --output results.json

# Skip NPC extraction (faster, no Azure calls)
python cli.py ./input_md_files --no-npc-extraction

# Force reprocess all files
python cli.py ./input_md_files --no-skip-existing

# Non-recursive (only top-level directory)
python cli.py ./input_md_files --no-recursive
```

### Python Script Example

```python
from pathlib import Path
from config import get_config
from import_processor import ImportProcessor

# Load config
config = get_config()

# Create processor
processor = ImportProcessor(config)

# Process single file
result = processor.process_file(
    Path("./examples/goblin.md"),
    skip_if_exists=False,
    extract_npcs=True
)

print(f"Success: {result.success}")
print(f"Chunks: {result.chunks_imported}")
print(f"NPCs: {result.npcs_extracted}")
```

## Support

- **Issues**: https://github.com/Cosmicjedi/md-to-qdrant-importer/issues
- **Docs**: See README.md for detailed documentation
- **Examples**: Check `examples/` directory for sample files

## What's Next?

1. ✅ Import your rulebook markdown files
2. ✅ Build a semantic search interface
3. ✅ Create NPC lookup tools
4. ✅ Integrate with your campaign manager
5. ✅ Build RAG (Retrieval-Augmented Generation) apps

Happy importing! 🚀
