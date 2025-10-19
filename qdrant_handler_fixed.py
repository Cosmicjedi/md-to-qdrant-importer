"""
Qdrant Database Handler - FIXED VERSION
Manages vector database operations with corrected adventure path routing

CHANGES:
- Added is_adventure_path() method that checks for "adventure" anywhere in filename
- Fixed determine_collection() to properly route adventure paths
- Now catches: "adventure", "adventure path", "adventurepath", etc.
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
import uuid
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)

from config import Config
from npc_extractor import NPCData

logger = logging.getLogger(__name__)


class QdrantHandler:
    """Handles all Qdrant database operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = QdrantClient(
            host=config.qdrant_host,
            port=config.qdrant_port,
            prefer_grpc=False
        )
        self._ensure_collections()
    
    def _ensure_collections(self):
        """Ensure all required collections exist"""
        collections_info = self.client.get_collections()
        existing = {c.name for c in collections_info.collections}
        
        required = [
            self.config.qdrant_collection_rulebooks,
            self.config.qdrant_collection_adventurepaths,
            self.config.qdrant_collection_npcs
        ]
        
        for collection_name in required:
            if collection_name not in existing:
                logger.info(f"Creating collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.config.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
            else:
                logger.info(f"Collection exists: {collection_name}")
    
    def is_adventure_path(self, file_path: Path) -> bool:
        """
        Check if a file is an adventure path.
        
        FIXED: Now checks for just "adventure" in the filename, not just
        "adventure path" or "adventurepath"
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is an adventure path
        """
        filename_lower = file_path.name.lower()
        # Check for any variation of "adventure" in the filename
        return "adventure" in filename_lower
    
    def determine_collection(self, file_path: Path) -> str:
        """
        Determine which collection a file should go into.
        
        FIXED: Now properly routes adventure paths using improved detection
        
        Args:
            file_path: Path to the file
            
        Returns:
            Name of the target collection
        """
        if self.is_adventure_path(file_path):
            logger.info(f"Routing '{file_path.name}' to adventure paths collection")
            return self.config.qdrant_collection_adventurepaths
        else:
            return self.config.qdrant_collection_rulebooks
    
    def insert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        file_path: Path
    ) -> int:
        """Insert text chunks with embeddings into appropriate collection"""
        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch: {len(chunks)} chunks, {len(embeddings)} embeddings")
        
        collection = self.determine_collection(file_path)
        
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            point_id = str(uuid.uuid4())
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "file_path": str(file_path),
                    "page_number": chunk.get("page_number"),
                    "chunk_index": chunk.get("chunk_index"),
                    "metadata": chunk.get("metadata", {})
                }
            ))
        
        self.client.upsert(collection_name=collection, points=points)
        logger.info(f"Inserted {len(points)} chunks into {collection}")
        return len(points)
    
    def insert_npcs(self, npcs: List[NPCData]) -> int:
        """Insert NPC data into NPCs collection"""
        if not npcs:
            return 0
        
        collection = self.config.qdrant_collection_npcs
        points = []
        
        for npc in npcs:
            point_id = str(uuid.uuid4())
            search_text = f"{npc.name}\n{npc.description}\n{npc.stats}"
            
            from embeddings import EmbeddingGenerator
            embedder = EmbeddingGenerator(self.config)
            embedding = embedder.generate_embeddings([search_text])[0]
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "name": npc.name,
                    "description": npc.description,
                    "stats": npc.stats,
                    "source_file": npc.source_file,
                    "page_number": npc.page_number
                }
            ))
        
        self.client.upsert(collection_name=collection, points=points)
        logger.info(f"Inserted {len(points)} NPCs")
        return len(points)
    
    def search(
        self,
        query_vector: List[float],
        collection_name: str,
        limit: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in a collection"""
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=Filter(**filter_dict) if filter_dict else None
        )
        
        return [{"score": hit.score, "payload": hit.payload} for hit in results]
    
    def delete_by_file(self, file_path: Path):
        """Delete all points associated with a file from all collections"""
        collections = [
            self.config.qdrant_collection_rulebooks,
            self.config.qdrant_collection_adventurepaths,
            self.config.qdrant_collection_npcs
        ]
        
        for collection in collections:
            try:
                result = self.client.scroll(
                    collection_name=collection,
                    scroll_filter=Filter(
                        must=[FieldCondition(key="file_path", match=MatchValue(value=str(file_path)))]
                    ),
                    limit=10000
                )
                
                point_ids = [point.id for point in result[0]]
                
                if point_ids:
                    self.client.delete(collection_name=collection, points_selector=point_ids)
                    logger.info(f"Deleted {len(point_ids)} points from {collection}")
            except Exception as e:
                logger.error(f"Error deleting from {collection}: {e}")
