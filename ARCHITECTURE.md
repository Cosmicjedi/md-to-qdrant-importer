# Architecture Documentation

## System Overview

MD to Qdrant Importer is a modular Python application that processes markdown files, chunks them semantically, generates vector embeddings, extracts structured NPC data, and stores everything in Qdrant vector database.

```
┌─────────────────┐
│  Markdown Files │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│           Import Processor (Coordinator)        │
└──┬──────────────────────────────────────────┬──┘
   │                                           │
   ▼                                           ▼
┌──────────────────┐                    ┌──────────────┐
│ Text Processor   │                    │ NPC Extractor│
│ - Load files     │                    │ - Azure AI   │
│ - Chunk text     │                    │ - Patterns   │
│ - Extract meta   │                    │ - Validation │
└──────┬───────────┘                    └──────┬───────┘
       │                                       │
       ▼                                       ▼
┌──────────────────────────────────────────────────┐
│              Qdrant Handler                      │
│  - Embeddings (SentenceTransformers)            │
│  - Vector storage                                │
│  - Dual collections (content + NPCs)            │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  Qdrant Database│
         │  ┌────────────┐ │
         │  │game_content│ │
         │  └────────────┘ │
         │  ┌────────────┐ │
         │  │    npcs    │ │
         │  └────────────┘ │
         └─────────────────┘
```

## Component Architecture

### 1. Configuration Layer (`config.py`)

**Responsibilities:**
- Load environment variables from `.env`
- Validate configuration
- Provide typed access to settings
- Manage default values

**Key Classes:**
- `Config`: Main configuration container

**Design Decisions:**
- Singleton pattern for global config access
- Lazy loading with `get_config()`
- Validation separate from loading

### 2. Text Processing Layer (`text_processor.py`)

**Responsibilities:**
- Load markdown files
- Split text into semantic chunks
- Extract markdown metadata
- Handle file discovery

**Key Classes:**
- `TextChunker`: Intelligent text splitting
- `MarkdownProcessor`: File I/O and orchestration

**Chunking Strategy:**
1. Prefer paragraph boundaries (double newlines)
2. Fall back to sentence boundaries
3. Final fallback to character count
4. Always maintain overlap for context

**Design Decisions:**
- Preserve markdown structure when possible
- Configurable chunk size and overlap
- Metadata extraction for filtering

### 3. NPC Extraction Layer (`npc_extractor.py`)

**Responsibilities:**
- Detect potential NPC stat blocks
- Extract structured data via Azure AI
- Validate and score extractions
- Store with canonical flag

**Key Classes:**
- `NPCExtractor`: Main extraction logic
- `NPCData`: Structured NPC representation (dataclass)

**Extraction Pipeline:**
```
Text Chunk
    │
    ▼
Pattern Pre-Filter (heuristic)
    │ (2+ patterns matched)
    ▼
Azure OpenAI Extraction
    │
    ▼
Confidence Threshold Check
    │ (>= 0.7)
    ▼
Structured NPCData
```

**Design Decisions:**
- Pre-filter with regex to reduce API calls
- JSON-mode for structured output
- Low temperature (0.1) for consistency
- Configurable confidence threshold

### 4. Qdrant Integration Layer (`qdrant_handler.py`)

**Responsibilities:**
- Manage Qdrant connections
- Generate embeddings
- Create/manage collections
- Insert points (chunks and NPCs)
- Query existing data

**Key Classes:**
- `QdrantHandler`: Main database interface

**Data Model:**

**{prefix}_general collection (default: game_general):**
```python
{
    "id": "uuid",
    "vector": [384 floats],  # from sentence transformer
    "payload": {
        "text": "chunk content",
        "chunk_index": 0,
        "total_chunks": 10,
        "source_file": "dragon.md",
        "file_path": "/path/to/dragon.md",
        # ... file metadata
    }
}
```

**{prefix}_npcs collection (default: game_npcs):**
```python
{
    "id": "uuid",
    "vector": [384 floats],  # from NPC description
    "payload": {
        "name": "Ancient Red Dragon",
        "npc_type": "creature",
        "canonical": true,
        "attributes": {"STR": 30, ...},
        "challenge_rating": "24",
        # ... full NPC data
    }
}
```

**Design Decisions:**
- Separate collections for different data types
- Configurable collection prefix for multi-tenancy
- REST API for local connections (gRPC for production)
- Batch embedding for performance
- UUID-based IDs for uniqueness

### 5. Import Coordination Layer (`import_processor.py`)

**Responsibilities:**
- Orchestrate entire import pipeline
- Coordinate between components
- Track progress and results
- Generate statistics

**Key Classes:**
- `ImportProcessor`: Main pipeline coordinator
- `ImportResult`: Result tracking (dataclass)

**Processing Flow:**
```
For each markdown file:
    1. Check if already processed (optional)
    2. Load and chunk text
    3. Generate embeddings
    4. Insert chunks to {prefix}_general
    5. Extract NPCs (if enabled)
    6. Insert NPCs to {prefix}_npcs collection
    7. Record result
```

**Design Decisions:**
- Progress callbacks for UI updates
- Parallel-ready (currently synchronous)
- Result aggregation for reporting
- Error isolation per-file

### 6. User Interface Layer

#### GUI (`gui.py`)

**Responsibilities:**
- Provide user-friendly interface
- Handle user interactions
- Display progress and logs
- Configuration management

**Key Components:**
- Tkinter main window
- Configuration panel
- Options checkboxes
- Progress bar and log view
- Statistics viewer

**Threading Model:**
- UI thread: Tkinter event loop
- Worker thread: Import processing
- Communication via callbacks

#### CLI (`cli.py`)

**Responsibilities:**
- Command-line interface
- Scriptable/automatable
- Minimal dependencies on GUI libraries

**Features:**
- Argument parsing
- Progress output
- Results export
- Statistics display

## Data Flow

### Import Flow (Detailed)

```
┌──────────────┐
│ User Input   │ (directory selection)
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│ Find Markdown Files          │
│ - Recursive glob             │
│ - Filter .md, .markdown      │
└──────┬───────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ For Each File:                         │
│                                        │
│  ┌──────────────────────────────┐    │
│  │ Check if exists (optional)   │    │
│  └──────┬───────────────────────┘    │
│         │ if not exists              │
│         ▼                             │
│  ┌──────────────────────────────┐    │
│  │ Load File                    │    │
│  │ - Read UTF-8                 │    │
│  │ - Extract metadata           │    │
│  └──────┬───────────────────────┘    │
│         │                             │
│         ▼                             │
│  ┌──────────────────────────────┐    │
│  │ Chunk Text                   │    │
│  │ - Smart boundaries           │    │
│  │ - Overlap preservation       │    │
│  └──────┬───────────────────────┘    │
│         │                             │
│         ▼                             │
│  ┌──────────────────────────────┐    │
│  │ Generate Embeddings          │    │
│  │ - Batch encode               │    │
│  │ - SentenceTransformer        │    │
│  └──────┬───────────────────────┘    │
│         │                             │
│         ▼                             │
│  ┌──────────────────────────────┐    │
│  │ Insert to {prefix}_general   │    │
│  │ - Create points              │    │
│  │ - Upsert batch               │    │
│  └──────┬───────────────────────┘    │
│         │                             │
│         ▼                             │
│  ┌──────────────────────────────┐    │
│  │ Extract NPCs (if enabled)    │    │
│  │ - Pattern filter             │    │
│  │ - Azure AI call              │    │
│  │ - Parse JSON                 │    │
│  └──────┬───────────────────────┘    │
│         │                             │
│         ▼                             │
│  ┌──────────────────────────────┐    │
│  │ Insert NPCs to {prefix}_npcs │    │
│  │ - Embed descriptions         │    │
│  │ - Mark canonical             │    │
│  └──────┬───────────────────────┘    │
│         │                             │
│         ▼                             │
│  ┌──────────────────────────────┐    │
│  │ Record Result                │    │
│  └──────────────────────────────┘    │
│                                        │
└────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Aggregate Results            │
│ - Success/failure counts     │
│ - Total chunks/NPCs          │
│ - Processing times           │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Generate Report              │
│ - JSON export (optional)     │
│ - Statistics display         │
└──────────────────────────────┘
```

## Extension Points

### Adding New Extraction Types

To add extraction for spells, items, etc.:

1. Create new extractor class similar to `NPCExtractor`
2. Define dataclass for structured data
3. Add pattern matching for pre-filtering
4. Create Azure AI prompt for extraction
5. Add to import processor pipeline

Example:
```python
class SpellExtractor:
    def extract_spell(self, text: str) -> Optional[SpellData]:
        # Similar pattern to NPC extraction
        pass
```

### Adding New Embedding Models

To use different embedding models:

1. Update `EMBEDDING_MODEL` in `.env`
2. Ensure `VECTOR_DIMENSION` matches model output
3. Re-create collections if dimension changes

### Adding New Data Sources

To support additional file formats:

1. Extend `MarkdownProcessor` or create new processor
2. Implement text extraction
3. Plug into `ImportProcessor` pipeline

## Performance Considerations

### Bottlenecks

1. **Azure AI API Calls** (NPC extraction)
   - Rate limited by Azure
   - ~2-5 seconds per call
   - Mitigated by pre-filtering

2. **Embedding Generation**
   - CPU-bound without GPU
   - ~100 chunks/second on CPU
   - Can batch for efficiency

3. **File I/O**
   - Generally not limiting
   - Async I/O possible for large batches

### Optimization Strategies

1. **Batch Processing**
   - Embed multiple chunks at once
   - Upsert points in batches

2. **Parallel Processing** (future)
   - Process multiple files concurrently
   - Thread pool for file loading
   - Process pool for embedding

3. **Caching**
   - Skip already-processed files
   - Cache embeddings if reprocessing

## Security Considerations

### Sensitive Data

- `.env` file contains API keys
- Never commit to version control
- Use environment variables in production

### Input Validation

- File paths validated
- Markdown sanitization not required (vector DB)
- API inputs validated by Azure

### Network Security

- Qdrant: localhost only by default
- Azure: HTTPS enforced
- No authentication for local Qdrant

## Testing Strategy

### Unit Tests (future)

```python
# test_chunker.py
def test_chunk_text():
    chunker = TextChunker(chunk_size=100, overlap=20)
    text = "..." * 200
    chunks = chunker.chunk_text(text)
    assert len(chunks) > 1
    # Verify overlap
```

### Integration Tests

```python
# test_import.py
def test_full_import():
    processor = ImportProcessor(config)
    results = processor.process_file(test_file)
    assert results.success
    assert results.chunks_imported > 0
```

### Validation Script

`validate.py` provides runtime validation:
- Dependency checks
- Configuration validation
- Service connectivity
- Directory structure

## Deployment

### Local Development

```bash
python gui.py
```

### Server Deployment

```bash
# Use CLI for automation
python cli.py /path/to/files --output results.json
```

### Docker (future)

```dockerfile
FROM python:3.11
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "cli.py", "/data"]
```

## Future Enhancements

1. **Parallel Processing**
   - Multi-threaded file processing
   - Async Azure API calls

2. **Incremental Updates**
   - Watch directory for changes
   - Process only modified files

3. **Web Interface**
   - FastAPI backend
   - React frontend
   - REST API for queries

4. **Advanced NPC Features**
   - Relationship extraction
   - Location associations
   - Campaign-specific variants

5. **Query Interface**
   - Semantic search UI
   - Filter by metadata
   - NPC stat lookup

6. **Monitoring**
   - Prometheus metrics
   - Import statistics
   - Error tracking

## Conclusion

This architecture provides:
- ✅ Modularity: Easy to extend
- ✅ Testability: Clear interfaces
- ✅ Maintainability: Well-organized code
- ✅ Scalability: Batch-ready design
- ✅ Usability: GUI and CLI options
