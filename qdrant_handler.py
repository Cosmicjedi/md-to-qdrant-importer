"""
Qdrant Database Handler
Manages connections and operations with Qdrant vector database
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
from sentence_transformers import SentenceTransformer

from config import Config
from npc_extractor import NPCData


class QdrantHandler:
    """Handles all Qdrant database operations"""
    
    def __init__(self, config: Config):
        """
        Initialize Qdrant handler
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Connect to local Qdrant instance
        self.client = QdrantClient(
            host=config.qdrant_host,
            port=config.qdrant_port,
            prefer_grpc=False  # Use REST API for local connections
        )
        
        # Initialize embedding model
        print(f"Loading embedding model: {config.embedding_model}")
        self.embedding_model = SentenceTransformer(config.embedding_model)
        
        # Verify vector dimension matches
        test_embedding = self.embedding_model.encode("test")
        actual_dim = len(test_embedding)
        if actual_dim != config.vector_dimension:
            print(f"Warning: Vector dimension mismatch. Config: {config.vector_dimension}, Actual: {actual_dim}")
            config.vector_dimension = actual_dim
        
        # Initialize collections
        self._ensure_collections()
    
    def _ensure_collections(self):
        """Ensure required collections exist"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        # Define all collections to create
        required_collections = [
            (self.config.qdrant_collection_general, "general content"),
            (self.config.qdrant_collection_npcs, "NPCs"),
            (self.config.qdrant_collection_rulebooks, "rulebooks"),
            (self.config.qdrant_collection_adventurepaths, "adventure paths"),
        ]
        
        # Create each collection if it doesn't exist
        for collection_name, description in required_collections:
            if collection_name not in collection_names:
                print(f"Creating collection: {collection_name} ({description})")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.config.vector_dimension,
                        distance=Distance.COSINE
                    )
                )
    
    def determine_collection(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """
        Determine which collection content should go to based on filename
        
        Args:
            file_path: Path to the file
            metadata: File metadata
            
        Returns:
            Collection name to use
        """
        filename_lower = file_path.name.lower()
        
        # Check for adventure path indicator in filename
        if 'adventure path' in filename_lower or 'adventurepath' in filename_lower:
            return self.config.qdrant_collection_adventurepaths
        
        # Check for rulebook indicators
        # Common rulebook patterns: "rulebook", "core rules", "rules", "handbook", "guide"
        rulebook_patterns = ['rulebook', 'core rules', 'rules', 'handbook', 'guide', 'manual', 'compendium']
        if any(pattern in filename_lower for pattern in rulebook_patterns):
            return self.config.qdrant_collection_rulebooks
        
        # Default to general collection
        return self.config.qdrant_collection_general
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for batch of texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return [emb.tolist() for emb in embeddings]
    
    def insert_chunks(
        self,
        chunks: List[str],
        metadata: Dict[str, Any],
        file_path: Path
    ) -> tuple[int, str]:
        """
        Insert text chunks into appropriate collection based on content type
        
        Args:
            chunks: List of text chunks
            metadata: File metadata
            file_path: Source file path
            
        Returns:
            Tuple of (number of chunks inserted, collection name used)
        """
        if not chunks:
            return 0, self.config.qdrant_collection_general
        
        # Determine which collection to use
        collection_name = self.determine_collection(file_path, metadata)
        
        # Generate embeddings
        embeddings = self.embed_batch(chunks)
        
        # Create points
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            
            payload = {
                'text': chunk,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'source_file': metadata['filename'],
                'file_path': str(file_path),
                'content_type': self._get_content_type_from_collection(collection_name),
                **metadata
            }
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            ))
        
        # Insert into Qdrant
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        return len(points), collection_name
    
    def _get_content_type_from_collection(self, collection_name: str) -> str:
        """Get content type label from collection name"""
        if collection_name == self.config.qdrant_collection_rulebooks:
            return "rulebook"
        elif collection_name == self.config.qdrant_collection_adventurepaths:
            return "adventure_path"
        elif collection_name == self.config.qdrant_collection_npcs:
            return "npc"
        else:
            return "general"
    
    def insert_npc(self, npc: NPCData) -> str:
        """
        Insert NPC into dedicated NPC collection
        
        Args:
            npc: NPCData to insert
            
        Returns:
            Point ID
        """
        # Create embedding from NPC description or name
        embed_text = npc.description if npc.description else npc.name
        if npc.raw_text:
            embed_text = npc.raw_text
        
        embedding = self.embed_text(embed_text)
        
        # Create point
        point_id = str(uuid.uuid4())
        payload = npc.to_dict()
        
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload
        )
        
        # Insert into Qdrant
        self.client.upsert(
            collection_name=self.config.qdrant_collection_npcs,
            points=[point]
        )
        
        return point_id
    
    def insert_npcs(self, npcs: List[NPCData]) -> int:
        """
        Insert multiple NPCs
        
        Args:
            npcs: List of NPCData
            
        Returns:
            Number of NPCs inserted
        """
        for npc in npcs:
            self.insert_npc(npc)
        return len(npcs)
    
    def check_file_exists(self, file_path: Path) -> bool:
        """
        Check if file has already been processed
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file exists in database
        """
        try:
            result = self.client.scroll(
                collection_name=self.config.qdrant_collection_general,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="file_path",
                            match=MatchValue(value=str(file_path))
                        )
                    ]
                ),
                limit=1
            )
            return len(result[0]) > 0
        except Exception:
            return False
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection
        
        Args:
            collection_name: Name of collection
            
        Returns:
            Dictionary of statistics
        """
        try:
            info = self.client.get_collection(collection_name=collection_name)
            return {
                'name': collection_name,
                'points_count': info.points_count,
                'vectors_count': info.vectors_count,
                'status': info.status.value if info.status else 'unknown'
            }
        except Exception as e:
            return {
                'name': collection_name,
                'error': str(e)
            }
    
    def delete_by_file(self, file_path: Path, collection_name: Optional[str] = None):
        """
        Delete all points associated with a file
        
        Args:
            file_path: Path to file
            collection_name: Collection to delete from (default: general)
        """
        if collection_name is None:
            collection_name = self.config.qdrant_collection_general
        
        # Qdrant doesn't support delete by filter directly, so we need to:
        # 1. Query for points with this file_path
        # 2. Delete by IDs
        result = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="file_path",
                        match=MatchValue(value=str(file_path))
                    )
                ]
            ),
            limit=10000  # Adjust based on expected file size
        )
        
        point_ids = [point.id for point in result[0]]
        
        if point_ids:
            self.client.delete(
                collection_name=collection_name,
                points_selector=point_ids
            )
