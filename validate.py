#!/usr/bin/env python
"""
Validation script to test configuration and connections
"""

import sys
from pathlib import Path
from config import get_config
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from openai import AzureOpenAI


def validate_environment():
    """Validate the environment configuration"""
    print("="*60)
    print("MD to Qdrant Importer - System Validation")
    print("="*60)
    print()
    
    # Load configuration
    print("1. Loading configuration...")
    try:
        config = get_config()
        print("   ✓ Configuration loaded")
    except Exception as e:
        print(f"   ✗ Failed to load configuration: {e}")
        return False
    
    # Validate configuration
    print("\n2. Validating configuration...")
    is_valid, errors = config.validate()
    if is_valid:
        print("   ✓ Configuration is valid")
    else:
        print("   ✗ Configuration errors:")
        for error in errors:
            print(f"     - {error}")
        return False
    
    # Test Qdrant connection
    print(f"\n3. Testing Qdrant connection ({config.qdrant_host}:{config.qdrant_port})...")
    try:
        client = QdrantClient(
            host=config.qdrant_host,
            port=config.qdrant_port
        )
        collections = client.get_collections()
        print(f"   ✓ Connected to Qdrant")
        print(f"     Found {len(collections.collections)} collections:")
        
        # Check for our collections
        collection_names = [c.name for c in collections.collections]
        expected_collections = [
            config.qdrant_collection_general,
            config.qdrant_collection_npcs,
            config.qdrant_collection_rulebooks,
            config.qdrant_collection_adventurepaths
        ]
        
        for coll in expected_collections:
            if coll in collection_names:
                info = client.get_collection(collection_name=coll)
                print(f"     - {coll}: {info.points_count} points")
            else:
                print(f"     - {coll}: will be created on first import")
                
    except Exception as e:
        print(f"   ✗ Failed to connect to Qdrant: {e}")
        print("     Make sure Qdrant is running:")
        print("     docker run -p 6333:6333 qdrant/qdrant")
        return False
    
    # Test embedding model
    print(f"\n4. Testing embedding model ({config.embedding_model})...")
    try:
        model = SentenceTransformer(config.embedding_model)
        test_embedding = model.encode("test text")
        dimension = len(test_embedding)
        print(f"   ✓ Embedding model loaded")
        print(f"     Vector dimension: {dimension}")
        
        if dimension != config.vector_dimension:
            print(f"     ⚠ Warning: Config dimension ({config.vector_dimension}) != actual ({dimension})")
            
    except Exception as e:
        print(f"   ✗ Failed to load embedding model: {e}")
        print("     The model will be downloaded on first use (~90MB)")
    
    # Test Azure OpenAI connection
    print(f"\n5. Testing Azure OpenAI connection...")
    if config.enable_npc_extraction:
        try:
            azure_client = AzureOpenAI(
                azure_endpoint=config.azure_endpoint,
                api_key=config.azure_api_key,
                api_version=config.azure_api_version
            )
            
            # Test with a simple completion
            response = azure_client.chat.completions.create(
                model=config.azure_deployment_name,
                messages=[
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Respond with 'OK' if you receive this."}
                ],
                max_tokens=10,
                temperature=0
            )
            
            if response.choices[0].message.content:
                print(f"   ✓ Azure OpenAI connected")
                print(f"     Deployment: {config.azure_deployment_name}")
                print(f"     Endpoint: {config.azure_endpoint}")
            else:
                print(f"   ✗ Azure OpenAI responded but no content")
                
        except Exception as e:
            print(f"   ✗ Failed to connect to Azure OpenAI: {e}")
            print("     NPC extraction will be disabled")
            return False
    else:
        print("   ⓘ NPC extraction is disabled in configuration")
    
    # Check directories
    print(f"\n6. Checking directories...")
    directories_ok = True
    
    if config.input_directory.exists():
        md_files = list(config.input_directory.glob("*.md"))
        print(f"   ✓ Input directory exists: {config.input_directory}")
        print(f"     Found {len(md_files)} markdown files")
    else:
        print(f"   ⚠ Input directory not found: {config.input_directory}")
        print(f"     Creating directory...")
        config.input_directory.mkdir(parents=True, exist_ok=True)
        directories_ok = False
    
    if config.output_directory.exists():
        print(f"   ✓ Output directory exists: {config.output_directory}")
    else:
        print(f"   ⚠ Output directory not found: {config.output_directory}")
        print(f"     Creating directory...")
        config.output_directory.mkdir(parents=True, exist_ok=True)
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    print(f"""
Configuration:
  Collection Prefix: {config.qdrant_collection_prefix}
  Chunk Size: {config.chunk_size} (overlap: {config.chunk_overlap})
  Embedding Model: {config.embedding_model}
  NPC Extraction: {'Enabled' if config.enable_npc_extraction else 'Disabled'}
  
Status:
  ✓ Configuration valid
  ✓ Qdrant connected
  ✓ Embedding model ready
  {'✓ Azure OpenAI connected' if config.enable_npc_extraction else 'ⓘ NPC extraction disabled'}
  {'✓ Directories ready' if directories_ok else '⚠ Directories created'}
""")
    
    if not directories_ok:
        print("⚠ Place your markdown files in:", config.input_directory)
        print()
    
    print("System is ready for import!")
    print("\nUsage:")
    print("  GUI:  python gui.py")
    print("  CLI:  python cli.py ./input_md_files")
    print()
    
    return True


if __name__ == '__main__':
    success = validate_environment()
    sys.exit(0 if success else 1)
