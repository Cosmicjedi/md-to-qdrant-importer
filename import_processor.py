"""
Main Import Processor
Coordinates the entire import pipeline
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

from config import Config
from text_processor import TextChunker, MarkdownProcessor
from npc_extractor import NPCExtractor, NPCData
from qdrant_handler import QdrantHandler


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
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ImportProcessor:
    """Main processor for importing MD files to Qdrant"""
    
    def __init__(self, config: Config, progress_callback: Optional[Callable] = None):
        """
        Initialize import processor
        
        Args:
            config: Application configuration
            progress_callback: Optional callback for progress updates
        """
        self.config = config
        self.progress_callback = progress_callback
        
        # Initialize components
        self.chunker = TextChunker(
            chunk_size=config.chunk_size,
            overlap=config.chunk_overlap
        )
        self.processor = MarkdownProcessor(self.chunker)
        self.qdrant = QdrantHandler(config)
        
        if config.enable_npc_extraction:
            self.npc_extractor = NPCExtractor(config)
        else:
            self.npc_extractor = None
    
    def _update_progress(self, message: str, current: int = 0, total: int = 0):
        """Update progress via callback"""
        if self.progress_callback:
            self.progress_callback(message, current, total)
    
    def process_file(
        self,
        file_path: Path,
        skip_if_exists: bool = False,
        extract_npcs: bool = True
    ) -> ImportResult:
        """
        Process a single markdown file
        
        Args:
            file_path: Path to markdown file
            skip_if_exists: Skip if already in database
            extract_npcs: Whether to extract NPCs
            
        Returns:
            ImportResult
        """
        start_time = datetime.now()
        
        try:
            # Check if already exists
            if skip_if_exists and self.qdrant.check_file_exists(file_path):
                return ImportResult(
                    file_path=str(file_path),
                    success=True,
                    chunks_imported=0,
                    npcs_extracted=0,
                    processing_time=0.0
                )
            
            self._update_progress(f"Processing {file_path.name}...")
            
            # Process file into chunks
            chunks, metadata = self.processor.process_file(file_path)
            
            if not chunks:
                return ImportResult(
                    file_path=str(file_path),
                    success=False,
                    error="No content to process"
                )
            
            # Insert chunks into Qdrant
            self._update_progress(f"Inserting {len(chunks)} chunks...")
            chunks_inserted, collection_used = self.qdrant.insert_chunks(chunks, metadata, file_path)
            
            # Extract NPCs if enabled
            npcs_extracted = 0
            if extract_npcs and self.npc_extractor and self.config.enable_npc_extraction:
                self._update_progress(f"Extracting NPCs from {file_path.name}...")
                npcs = self.npc_extractor.extract_npcs_from_chunks(chunks, str(file_path))
                
                if npcs:
                    self._update_progress(f"Found {len(npcs)} NPCs, inserting...")
                    npcs_extracted = self.qdrant.insert_npcs(npcs)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ImportResult(
                file_path=str(file_path),
                success=True,
                chunks_imported=chunks_inserted,
                npcs_extracted=npcs_extracted,
                collection_used=collection_used,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return ImportResult(
                file_path=str(file_path),
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    def process_directory(
        self,
        directory: Path,
        recursive: bool = True,
        skip_existing: bool = False,
        extract_npcs: bool = True
    ) -> List[ImportResult]:
        """
        Process all markdown files in a directory
        
        Args:
            directory: Directory containing markdown files
            recursive: Search subdirectories
            skip_existing: Skip files already in database
            extract_npcs: Whether to extract NPCs
            
        Returns:
            List of ImportResults
        """
        # Find all markdown files
        if recursive:
            md_files = self.processor.find_markdown_files(directory)
        else:
            md_files = list(directory.glob("*.md")) + list(directory.glob("*.markdown"))
        
        if not md_files:
            self._update_progress("No markdown files found")
            return []
        
        self._update_progress(f"Found {len(md_files)} markdown files")
        
        # Process each file
        results = []
        for i, file_path in enumerate(md_files, 1):
            self._update_progress(
                f"Processing file {i}/{len(md_files)}: {file_path.name}",
                i,
                len(md_files)
            )
            
            result = self.process_file(
                file_path,
                skip_if_exists=skip_existing,
                extract_npcs=extract_npcs
            )
            results.append(result)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about processed data
        
        Returns:
            Dictionary of statistics
        """
        general_stats = self.qdrant.get_collection_stats(
            self.config.qdrant_collection_general
        )
        npc_stats = self.qdrant.get_collection_stats(
            self.config.qdrant_collection_npcs
        )
        rulebook_stats = self.qdrant.get_collection_stats(
            self.config.qdrant_collection_rulebooks
        )
        adventurepath_stats = self.qdrant.get_collection_stats(
            self.config.qdrant_collection_adventurepaths
        )
        
        return {
            'general_content': general_stats,
            'npcs': npc_stats,
            'rulebooks': rulebook_stats,
            'adventure_paths': adventurepath_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def save_results(self, results: List[ImportResult], output_path: Path):
        """
        Save import results to JSON file
        
        Args:
            results: List of ImportResults
            output_path: Path to save results
        """
        # Count by collection
        collection_counts = {}
        for r in results:
            if r.success and r.collection_used:
                collection_counts[r.collection_used] = collection_counts.get(r.collection_used, 0) + 1
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(results),
            'successful': sum(1 for r in results if r.success),
            'failed': sum(1 for r in results if not r.success),
            'total_chunks': sum(r.chunks_imported for r in results),
            'total_npcs': sum(r.npcs_extracted for r in results),
            'collection_distribution': collection_counts,
            'results': [r.to_dict() for r in results]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
