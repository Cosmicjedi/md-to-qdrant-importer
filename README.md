# MD to Qdrant Importer with Intelligent NPC Extraction

A comprehensive tool for importing markdown files from MarkItDown into Qdrant vector database with AI-powered NPC extraction for RAG (Retrieval-Augmented Generation) applications.

## ✨ Features

- **Bulk Markdown Import**: Process entire directories of markdown files
- **Intelligent NPC Extraction**: Uses Azure OpenAI to identify and extract NPC stat blocks
- **Smart Collection Routing**: Automatically categorizes content into appropriate collections
- **Canonical NPC Storage**: Keeps rulebook NPCs separate with `canonical: true` metadata
- **Multiple Game System Support**: D&D, Pathfinder, Star Wars D6, and more
- **Chunking & Overlap**: Configurable text chunking for optimal retrieval
- **GUI & CLI**: Both graphical and command-line interfaces
- **Windows Compatible**: Full Windows support with cross-platform compatibility

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Qdrant running locally (no API key needed for local)
- Azure OpenAI account with deployed model
- MarkItDown output directory with `.md` files

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Cosmicjedi/md-to-qdrant-importer.git
cd md-to-qdrant-importer
```

2. Run the setup script:
```bash
# Linux/Mac
./setup.sh

# Windows
python setup.sh
```

3. Follow the prompts to enter your Azure OpenAI credentials

### Usage

#### GUI Mode
```bash
python gui.py
```

#### CLI Mode
```bash
# Process a directory
python cli.py ./input_md_files

# Process a single file
python cli.py ./path/to/file.md

# Advanced options
python cli.py ./input_md_files --skip-existing --verbose
```

## 🎯 Implementation Strategy

The tool implements intelligent NPC extraction that:

1. **Chunks and indexes** markdown files into Qdrant
2. **Uses Azure AI services** to identify NPC stat blocks in text
3. **Extracts structured NPC data** (name, attributes, skills, etc.)
4. **Stores in dedicated collection** with `canonical: true` metadata
5. **Keeps separate** from campaign-specific NPCs

## 📁 Collections Created

Based on your `QDRANT_COLLECTION_PREFIX` (default: `game`):

- `game_general` - General game content
- `game_npcs` - Extracted NPC stat blocks (canonical: true)
- `game_rulebooks` - Core rulebook content  
- `game_adventurepaths` - Adventure and campaign content

## ⚙️ Configuration

Edit `.env` file (created from `.env.template`):

```env
# Azure AI Configuration
AZURE_ENDPOINT=https://your-service.openai.azure.com/
AZURE_API_KEY=your-api-key-here
AZURE_DEPLOYMENT_NAME=gpt-4o

# Qdrant Configuration (local, no auth)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Processing Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# NPC Extraction
ENABLE_NPC_EXTRACTION=true
NPC_CONFIDENCE_THRESHOLD=0.7
```

## 🤖 NPC Extraction

The AI-powered NPC extractor identifies and extracts:

### Universal RPG Stats
- Name, description, level
- Hit points, armor class
- Six attributes (STR, DEX, CON, INT, WIS, CHA)
- Skills, abilities, equipment
- Attacks, resistances, immunities

### D&D/Pathfinder Specific
- Challenge rating (CR)
- Experience points
- Alignment, size, creature type

### Star Wars D6 Specific  
- Force sensitivity
- Force points, Dark Side points
- Character points

### Metadata
- Source file and page
- Canonical flag (true for rulebooks)
- Game system detection
- Confidence score

## 📊 How It Works

1. **Text Processing**
   - Reads markdown files
   - Extracts metadata and structure
   - Chunks text with configurable overlap

2. **Content Classification**
   - Analyzes filenames and content
   - Routes to appropriate collection
   - Detects rulebooks vs adventures

3. **NPC Extraction** 
   - Identifies potential NPC chunks
   - Sends to Azure OpenAI for analysis
   - Extracts structured data
   - Validates confidence threshold

4. **Vector Storage**
   - Generates embeddings (Sentence Transformers)
   - Stores in Qdrant with metadata
   - Maintains source file references

## 📝 Example Workflow

```bash
# 1. Setup environment
./setup.sh

# 2. Place markdown files in input directory
cp ~/markitdown/output/*.md ./input_md_files/

# 3. Run import with NPC extraction
python cli.py ./input_md_files --verbose

# 4. Check results
cat ./output_logs/import_log_*.json
```

## 🔍 Querying Qdrant

After import, query your collections:

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# Search for NPCs
results = client.search(
    collection_name="game_npcs",
    query_vector=embedding,
    filter={
        "must": [
            {"key": "canonical", "match": {"value": True}},
            {"key": "challenge_rating", "range": {"gte": "5"}}
        ]
    }
)
```

## 📈 Performance

- **Chunking**: 1000 chars with 200 char overlap (configurable)
- **Embeddings**: all-MiniLM-L6-v2 (384 dimensions)
- **Processing**: ~10-20 files/minute with NPC extraction
- **Storage**: ~1-2MB per 100 pages of content

## 🛠️ Troubleshooting

### Qdrant Connection Failed
```bash
# Start Qdrant locally
docker run -p 6333:6333 qdrant/qdrant
```

### Azure OpenAI Errors
- Verify endpoint URL includes `https://`
- Check API key is valid
- Ensure deployment name matches your Azure setup

### No NPCs Found
- Lower `NPC_CONFIDENCE_THRESHOLD` in `.env`
- Check content has stat blocks
- Verify Azure AI connection

## 📦 Dependencies

- `qdrant-client` - Vector database client
- `sentence-transformers` - Embeddings generation  
- `openai` - Azure OpenAI API
- `python-dotenv` - Environment management
- `customtkinter` - Modern GUI framework

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- Built for the Nerdbuntu project
- Designed for MarkItDown output processing
- Optimized for tabletop RPG content

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Cosmicjedi/md-to-qdrant-importer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Cosmicjedi/md-to-qdrant-importer/discussions)

---

**Remember**: Qdrant must be running before using this tool. The NPC extraction requires valid Azure OpenAI credentials.
