"""
Embedding Generator Module
Handles generation of embeddings using various providers
"""

from typing import List, Optional
from config import Config


class EmbeddingGenerator:
    """
    Generates embeddings for text using configured embedding provider
    
    Supports:
    - Sentence Transformers (local)
    - OpenAI embeddings
    - Azure OpenAI embeddings
    """
    
    def __init__(self, config: Config):
        """
        Initialize the embedding generator
        
        Args:
            config: Configuration object containing embedding settings
        """
        self.config = config
        self.model = None
        self.provider = config.embedding_provider.lower() if hasattr(config, 'embedding_provider') else 'sentence-transformers'
        
        if self.provider == 'sentence-transformers' or self.provider == 'local':
            self._init_sentence_transformers()
        elif self.provider == 'openai':
            self._init_openai()
        elif self.provider == 'azure':
            self._init_azure()
        else:
            # Default to sentence transformers
            self._init_sentence_transformers()
    
    def _init_sentence_transformers(self):
        """Initialize Sentence Transformers model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            model_name = getattr(self.config, 'embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
            print(f"Loading Sentence Transformers model: {model_name}")
            self.model = SentenceTransformer(model_name)
            print(f"Model loaded successfully. Embedding dimension: {self.get_embedding_dimension()}")
            
        except ImportError:
            raise ImportError(
                "sentence-transformers is required. Install it with: "
                "pip install sentence-transformers"
            )
    
    def _init_openai(self):
        """Initialize OpenAI embeddings"""
        try:
            import openai
            self.openai_client = openai.OpenAI(api_key=self.config.openai_api_key)
            self.model_name = getattr(self.config, 'embedding_model', 'text-embedding-ada-002')
        except ImportError:
            raise ImportError("openai package is required for OpenAI embeddings")
    
    def _init_azure(self):
        """Initialize Azure OpenAI embeddings"""
        try:
            import openai
            from azure.identity import DefaultAzureCredential
            
            self.openai_client = openai.AzureOpenAI(
                api_key=self.config.azure_openai_key,
                api_version=self.config.azure_api_version,
                azure_endpoint=self.config.azure_endpoint
            )
            self.model_name = getattr(self.config, 'embedding_model', 'text-embedding-ada-002')
        except ImportError:
            raise ImportError("openai and azure-identity packages are required for Azure embeddings")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text
            
        Returns:
            List of floats representing the embedding vector
        """
        return self.generate_embeddings([text])[0]
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        if self.provider in ['sentence-transformers', 'local']:
            return self._generate_sentence_transformers(texts)
        elif self.provider == 'openai':
            return self._generate_openai(texts)
        elif self.provider == 'azure':
            return self._generate_azure(texts)
        else:
            return self._generate_sentence_transformers(texts)
    
    def _generate_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Sentence Transformers"""
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]
    
    def _generate_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        response = self.openai_client.embeddings.create(
            input=texts,
            model=self.model_name
        )
        return [item.embedding for item in response.data]
    
    def _generate_azure(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Azure OpenAI"""
        response = self.openai_client.embeddings.create(
            input=texts,
            model=self.model_name
        )
        return [item.embedding for item in response.data]
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors
        
        Returns:
            Embedding dimension size
        """
        if self.provider in ['sentence-transformers', 'local']:
            return self.model.get_sentence_embedding_dimension()
        elif self.provider in ['openai', 'azure']:
            # Common OpenAI embedding dimensions
            if 'ada-002' in self.model_name:
                return 1536
            elif 'text-embedding-3-small' in self.model_name:
                return 1536
            elif 'text-embedding-3-large' in self.model_name:
                return 3072
            else:
                # Default, but should be configured
                return 1536
        else:
            return 384  # Default for all-MiniLM-L6-v2
