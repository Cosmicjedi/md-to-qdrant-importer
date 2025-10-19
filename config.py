"""
Configuration loader for MD to Qdrant Importer
Loads environment variables and provides configuration to the application
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Application configuration loaded from environment variables"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            env_file: Path to .env file (optional, defaults to .env in current directory)
        """
        if env_file:
            load_dotenv(env_file, override=True)
        else:
            load_dotenv(override=True)
        
        # Azure AI Configuration
        self.azure_endpoint = os.getenv('AZURE_ENDPOINT', '')
        self.azure_api_key = os.getenv('AZURE_API_KEY', '')
        self.azure_api_version = os.getenv('AZURE_API_VERSION', '2024-02-15-preview')
        self.azure_deployment_name = os.getenv('AZURE_DEPLOYMENT_NAME', 'gpt-4o')
        
        # Qdrant Configuration
        self.qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
        self.qdrant_port = int(os.getenv('QDRANT_PORT', '6333'))
        self.qdrant_grpc_port = int(os.getenv('QDRANT_GRPC_PORT', '6334'))
        
        # Collection naming with prefix pattern
        self.qdrant_collection_prefix = os.getenv('QDRANT_COLLECTION_PREFIX', 'game')
        self.qdrant_collection_npcs = f"{self.qdrant_collection_prefix}_npcs"
        self.qdrant_collection_rulebooks = f"{self.qdrant_collection_prefix}_rulebooks"
        self.qdrant_collection_adventurepaths = f"{self.qdrant_collection_prefix}_adventurepaths"
        
        # Directory paths
        self.input_directory = Path(os.getenv('INPUT_DIRECTORY', './input_md_files'))
        self.output_directory = Path(os.getenv('OUTPUT_DIRECTORY', './output_logs'))
        
        # Processing settings
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '1000'))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '200'))
        self.max_concepts = int(os.getenv('MAX_CONCEPTS', '10'))
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.vector_dimension = int(os.getenv('VECTOR_DIMENSION', '384'))
        
        # NPC Extraction settings
        self.enable_npc_extraction = os.getenv('ENABLE_NPC_EXTRACTION', 'true').lower() == 'true'
        self.npc_confidence_threshold = float(os.getenv('NPC_CONFIDENCE_THRESHOLD', '0.7'))
        
        # Create directories if they don't exist
        self.input_directory.mkdir(parents=True, exist_ok=True)
        self.output_directory.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.azure_endpoint:
            errors.append("AZURE_ENDPOINT is required")
        if not self.azure_api_key:
            errors.append("AZURE_API_KEY is required")
        if not self.azure_deployment_name:
            errors.append("AZURE_DEPLOYMENT_NAME is required")
        
        if self.chunk_size <= 0:
            errors.append("CHUNK_SIZE must be positive")
        if self.chunk_overlap < 0:
            errors.append("CHUNK_OVERLAP must be non-negative")
        if self.chunk_overlap >= self.chunk_size:
            errors.append("CHUNK_OVERLAP must be less than CHUNK_SIZE")
        
        return len(errors) == 0, errors
    
    def __str__(self) -> str:
        """String representation of config (safe for logging)"""
        return f"""Configuration:
  Azure Endpoint: {self.azure_endpoint}
  Azure Deployment: {self.azure_deployment_name}
  Qdrant: {self.qdrant_host}:{self.qdrant_port}
  Collection Prefix: {self.qdrant_collection_prefix}
  Collections:
    - {self.qdrant_collection_npcs}
    - {self.qdrant_collection_rulebooks}
    - {self.qdrant_collection_adventurepaths}
  Embedding Model: {self.embedding_model}
  Chunk Size: {self.chunk_size} (overlap: {self.chunk_overlap})
  NPC Extraction: {'Enabled' if self.enable_npc_extraction else 'Disabled'}
"""


# Global config instance
config: Optional[Config] = None


def get_config(env_file: Optional[str] = None, force_reload: bool = False) -> Config:
    """
    Get or create global configuration instance
    
    Args:
        env_file: Path to .env file (optional)
        force_reload: If True, force reload config even if one exists
    
    Returns:
        Config instance
    """
    global config
    if config is None or force_reload:
        config = Config(env_file)
    return config
