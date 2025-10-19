"""
Main Import Processor - FIXED VERSION
Coordinates the entire import pipeline

CHANGES:
- Added skipped_npc_extraction field to ImportResult
- Modified process_file() to skip NPC extraction for adventure paths
- Added tracking for when NPC extraction is skipped
- Updated save_results() to report skipped NPC extractions
- FIXED: Pass chunker to MarkdownProcessor constructor
- FIXED: Added recursive and skip_existing parameters to process_directory()
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import time

from config import Config
from text_processor import TextChunker, MarkdownProcessor
from npc_extractor import NPCExtractor, NPCData
from qdrant_handler import QdrantHandler
from embeddings import EmbeddingGenerator


@dataclass
class ImportResult:
    """Result of importing a single file"""
    file_path: str
    success: bool
    chunks_imported: int = 0
    npcs_extracted: int = 0
    collection_used: str = ""
    error: Optional[str] = None
    processing_time: float = 0.0
    skipped_npc_extraction: bool = False
    skipped_existing: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ImportProcessor:
    """Main import pipeline coordinator"""
    
    def __init__(
        self,
        config: Config,
        progress_callback: Optional[Callable[[str], None]] = None
    ):
        self.config = config
        self.progress_callback = progress_callback
        
        self.qdrant = QdrantHandler(config)
        self.chunker = TextChunker(
            chunk_size=config.chunk_size,
            overlap=config.chunk_overlap
        )
        # FIXED: Pass chunker to MarkdownProcessor
        self.markdown_processor = MarkdownProcessor(self.chunker)
        self.embedder = EmbeddingGenerator(config)
        
        self.npc_extractor = None
        if config.enable_npc_extraction:
            self.npc_extractor = NPCExtractor(config)
    
    def _update_progress(self, message: str):
        """Send progress update if callback is provided"""
        if self.progress_callback:
            self.progress_callback(message)
    
    def _file_already_imported(self, file_path: Path) -> bool:
        """
        Check if a file has already been imported to the database
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists in database
        """
        try:
            collection = self.qdrant.determine_collection(file_path)
            # Query for points with this file path
            result = self.qdrant.client.scroll(
                collection_name=collection,
                scroll_filter={
                    "must": [
                        {
                            "key": "metadata.file_path",
                            "match": {"value": str(file_path)}
                        }
                    ]
                },
                limit=1
            )
            return len(result[0]) > 0
        except Exception:
            # If collection doesn't exist or any error, assume not imported
            return False
    
    def process_file(
        self,
        file_path: Path,
        extract_npcs: bool = True,
        skip_if_exists: bool = False
    ) -> ImportResult:
        """
        Process a single markdown file
        
        Args:
            file_path: Path to the markdown file
            extract_npcs: Whether to extract NPCs (ignored for adventure paths)
            skip_if_exists: Skip if file already in database
            
        Returns:
            ImportResult with processing details
        """
        start_time = time.time()
        
        try:
            # Check if file already imported
            if skip_if_exists and self._file_already_imported(file_path):
                self._update_progress(f"Skipping {file_path.name} (already imported)")
                return ImportResult(
                    file_path=str(file_path),
                    success=True,
                    skipped_existing=True,
                    processing_time=time.time() - start_time
                )
            
            self._update_progress(f"Processing {file_path.name}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sections = self.markdown_processor.parse_markdown(content)
            
            chunks = self.chunker.create_chunks(
                text=content,
                metadata={"file_path": str(file_path)}
            )
            
            if not chunks:
                return ImportResult(
                    file_path=str(file_path),
                    success=False,
                    error="No chunks created from file"
                )
            
            self._update_progress(f"Generating embeddings for {len(chunks)} chunks...")
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedder.generate_embeddings(texts)
            
            self._update_progress(f"Inserting chunks into Qdrant...")
            chunks_inserted = self.qdrant.insert_chunks(chunks, embeddings, file_path)
            
            collection = self.qdrant.determine_collection(file_path)
            
            is_adventure_path = self.qdrant.is_adventure_path(file_path)
            
            npcs_extracted = 0
            skipped_npc_extraction = False
            
            if is_adventure_path:
                self._update_progress(f"Skipping NPC extraction for adventure path: {file_path.name}")
                skipped_npc_extraction = True
            elif extract_npcs and self.npc_extractor and self.config.enable_npc_extraction:
                self._update_progress(f"Extracting NPCs from {file_path.name}...")
                npcs = self.npc_extractor.extract_npcs_from_chunks(chunks, str(file_path))
                
                if npcs:
                    self._update_progress(f"Found {len(npcs)} NPCs, inserting...")
                    npcs_extracted = self.qdrant.insert_npcs(npcs)
            
            processing_time = time.time() - start_time
            
            return ImportResult(
                file_path=str(file_path),
                success=True,
                chunks_imported=chunks_inserted,
                npcs_extracted=npcs_extracted,
                collection_used=collection,
                processing_time=processing_time,
                skipped_npc_extraction=skipped_npc_extraction
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return ImportResult(
                file_path=str(file_path),
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    def process_directory(
        self,
        directory: Path,
        pattern: str = "*.md",
        recursive: bool = False,
        skip_existing: bool = False,
        extract_npcs: bool = True
    ) -> List[ImportResult]:
        """
        Process all matching files in a directory
        
        Args:
            directory: Directory to process
            pattern: File pattern to match (default: "*.md")
            recursive: Whether to search subdirectories recursively
            skip_existing: Skip files already in database
            extract_npcs: Whether to extract NPCs
            
        Returns:
            List of import results
        """
        # Collect files based on recursive flag
        if recursive:
            # Use rglob for recursive search
            files = list(directory.rglob(pattern))
        else:
            # Use glob for non-recursive search
            files = list(directory.glob(pattern))
        
        if not files:
            self._update_progress(
                f"No files matching '{pattern}' found in {directory}" +
                (" (including subdirectories)" if recursive else "")
            )
            return []
        
        self._update_progress(
            f"Found {len(files)} files to process" +
            (" (including subdirectories)" if recursive else "")
        )
        
        results = []
        for i, file_path in enumerate(files, 1):
            self._update_progress(f"[{i}/{len(files)}] Processing {file_path.name}")
            result = self.process_file(
                file_path,
                extract_npcs=extract_npcs,
                skip_if_exists=skip_existing
            )
            results.append(result)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics from Qdrant collections
        
        Returns:
            Dictionary with collection statistics
        """
        stats = {}
        
        for collection_name in [
            f"{self.config.qdrant_collection_prefix}_npcs",
            f"{self.config.qdrant_collection_prefix}_rulebooks",
            f"{self.config.qdrant_collection_prefix}_adventurepaths"
        ]:
            try:
                collection_info = self.qdrant.client.get_collection(collection_name)
                stats[collection_name] = {
                    "points_count": collection_info.points_count,
                    "vectors_count": collection_info.vectors_count
                }
            except Exception as e:
                stats[collection_name] = {"error": str(e)}
        
        return stats
    
    def save_results(
        self,
        results: List[ImportResult],
        output_path: Path
    ):
        """
        Save import results to JSON file
        
        Args:
            results: List of import results
            output_path: Path to save results JSON
        """
        summary = {
            'total_files': len(results),
            'successful': sum(1 for r in results if r.success),
            'failed': sum(1 for r in results if not r.success),
            'skipped_existing': sum(1 for r in results if r.skipped_existing),
            'total_chunks': sum(r.chunks_imported for r in results),
            'total_npcs': sum(r.npcs_extracted for r in results),
            'adventure_paths_skipped_npc': sum(1 for r in results if r.skipped_npc_extraction),
            'total_time': sum(r.processing_time for r in results),
            'timestamp': datetime.now().isoformat()
        }
        
        output_data = {
            'summary': summary,
            'results': [r.to_dict() for r in results]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        self._update_progress(f"Results saved to {output_path}")
