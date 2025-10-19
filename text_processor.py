"""
Text Processing Module
Handles markdown parsing, chunking, and preprocessing for vector embeddings
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import hashlib


class TextChunker:
    """Handles text chunking with configurable size and overlap"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize text chunker
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        text_length = len(text)
        
        # Calculate chunk positions
        start = 0
        while start < text_length:
            # Determine end position
            end = min(start + self.chunk_size, text_length)
            
            # Try to break at sentence boundary if not at end
            if end < text_length:
                # Look for sentence end markers
                sentence_ends = ['. ', '! ', '? ', '\n\n']
                best_break = end
                
                for marker in sentence_ends:
                    # Search backwards from end for marker
                    pos = text.rfind(marker, start + self.overlap, end)
                    if pos != -1:
                        best_break = pos + len(marker) - 1
                        break
                
                # If no sentence boundary found, try word boundary
                if best_break == end:
                    space_pos = text.rfind(' ', start + self.overlap, end)
                    if space_pos != -1:
                        best_break = space_pos
                
                end = best_break
            
            # Extract chunk
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move to next chunk with overlap
            start = end - self.overlap if end < text_length else text_length
        
        return chunks
    
    def create_chunks(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Create chunks with metadata (compatible with import_processor)
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with 'text' and metadata
        """
        if metadata is None:
            metadata = {}
        
        text_chunks = self.chunk_text(text)
        
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_dict = {
                'text': chunk_text,
                'chunk_index': i,
                'total_chunks': len(text_chunks),
                **metadata
            }
            chunks.append(chunk_dict)
        
        return chunks
    
    def chunk_by_sections(self, text: str, headers: List[str]) -> Dict[str, List[str]]:
        """
        Chunk text by markdown sections
        
        Args:
            text: Markdown text
            headers: List of header texts found in document
            
        Returns:
            Dictionary mapping section names to chunks
        """
        sections = {}
        
        # Split by headers
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = text.split('\n')
        
        current_section = "Introduction"
        current_content = []
        
        for line in lines:
            header_match = re.match(header_pattern, line)
            
            if header_match:
                # Save previous section
                if current_content:
                    section_text = '\n'.join(current_content).strip()
                    if section_text:
                        sections[current_section] = self.chunk_text(section_text)
                
                # Start new section
                current_section = header_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            section_text = '\n'.join(current_content).strip()
            if section_text:
                sections[current_section] = self.chunk_text(section_text)
        
        return sections


class MarkdownProcessor:
    """Processes markdown files for import"""
    
    def __init__(self, chunker: TextChunker):
        """
        Initialize markdown processor
        
        Args:
            chunker: TextChunker instance
        """
        self.chunker = chunker
    
    def parse_markdown(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse markdown content into sections
        
        Args:
            content: Markdown content
            
        Returns:
            List of section dictionaries with headers and content
        """
        sections = []
        
        # Split by headers
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')
        
        current_section = {
            'level': 0,
            'title': 'Introduction',
            'content': []
        }
        
        for line in lines:
            header_match = re.match(header_pattern, line)
            
            if header_match:
                # Save previous section
                if current_section['content']:
                    current_section['content'] = '\n'.join(current_section['content']).strip()
                    if current_section['content']:
                        sections.append(current_section)
                
                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = {
                    'level': level,
                    'title': title,
                    'content': []
                }
            else:
                current_section['content'].append(line)
        
        # Save last section
        if current_section['content']:
            current_section['content'] = '\n'.join(current_section['content']).strip()
            if current_section['content']:
                sections.append(current_section)
        
        return sections
    
    def extract_metadata(self, content: str, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from markdown content
        
        Args:
            content: Markdown content
            file_path: Path to file
            
        Returns:
            Dictionary of metadata
        """
        metadata = {
            'filename': file_path.name,
            'filepath': str(file_path),
            'file_hash': hashlib.md5(content.encode()).hexdigest(),
            'char_count': len(content),
            'line_count': content.count('\n') + 1
        }
        
        # Extract title (first H1 or H2)
        title_match = re.search(r'^#{1,2}\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # Extract all headers for structure
        headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        metadata['headers'] = headers
        metadata['header_count'] = len(headers)
        
        # Check for YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            # Simple YAML parsing (basic key: value)
            frontmatter = {}
            for line in frontmatter_match.group(1).split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()
            metadata['frontmatter'] = frontmatter
        
        # Detect content type hints
        content_lower = content.lower()
        metadata['content_hints'] = []
        
        # Check for NPC indicators
        npc_patterns = [
            r'\bstats?\b', r'\bhit points?\b', r'\barmor class\b',
            r'\bstr\s*\d+\b', r'\bdex\s*\d+\b', r'\bcon\s*\d+\b',
            r'\bchallenge rating\b', r'\bcr\s*\d+', r'\bnpc\b',
            r'\bcreature\b', r'\bmonster\b'
        ]
        
        for pattern in npc_patterns:
            if re.search(pattern, content_lower):
                metadata['content_hints'].append('npc_content')
                break
        
        # Check for rulebook indicators
        rulebook_patterns = [
            r'\brules?\b', r'\bmechanics?\b', r'\bgame(?:play)?\b',
            r'\bchapter\s+\d+', r'\bsection\s+\d+', r'\bappendix\b'
        ]
        
        for pattern in rulebook_patterns:
            if re.search(pattern, content_lower):
                metadata['content_hints'].append('rulebook_content')
                break
        
        # Check for adventure/campaign indicators
        adventure_patterns = [
            r'\badventure\b', r'\bcampaign\b', r'\bquest\b',
            r'\bencounter\s+\d+', r'\bscene\s+\d+', r'\bact\s+\d+'
        ]
        
        for pattern in adventure_patterns:
            if re.search(pattern, content_lower):
                metadata['content_hints'].append('adventure_content')
                break
        
        return metadata
    
    def process_file(self, file_path: Path) -> Tuple[List[str], Dict[str, Any]]:
        """
        Process a markdown file into chunks with metadata
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            Tuple of (chunks, metadata)
        """
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata
        metadata = self.extract_metadata(content, file_path)
        
        # Clean content for chunking
        cleaned_content = self.clean_markdown(content)
        
        # Chunk the content
        chunks = self.chunker.chunk_text(cleaned_content)
        
        return chunks, metadata
    
    def clean_markdown(self, content: str) -> str:
        """
        Clean markdown content for better chunking
        
        Args:
            content: Raw markdown content
            
        Returns:
            Cleaned content
        """
        # Remove YAML frontmatter
        content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
        
        # Remove HTML comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # Convert multiple newlines to double newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove leading/trailing whitespace
        content = content.strip()
        
        return content
    
    def find_markdown_files(self, directory: Path) -> List[Path]:
        """
        Recursively find all markdown files in directory
        
        Args:
            directory: Root directory to search
            
        Returns:
            List of markdown file paths
        """
        markdown_extensions = ['.md', '.markdown', '.mdown', '.mkd']
        markdown_files = []
        
        for ext in markdown_extensions:
            markdown_files.extend(directory.rglob(f'*{ext}'))
        
        # Sort for consistent processing order
        return sorted(markdown_files)
    
    def extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from markdown
        
        Args:
            content: Markdown content
            
        Returns:
            List of code blocks with language info
        """
        code_blocks = []
        
        # Match fenced code blocks
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for language, code in matches:
            code_blocks.append({
                'language': language or 'plain',
                'code': code.strip()
            })
        
        return code_blocks
    
    def extract_tables(self, content: str) -> List[str]:
        """
        Extract markdown tables
        
        Args:
            content: Markdown content
            
        Returns:
            List of table strings
        """
        tables = []
        
        # Simple table detection (lines with |)
        lines = content.split('\n')
        in_table = False
        current_table = []
        
        for line in lines:
            if '|' in line:
                if not in_table:
                    in_table = True
                current_table.append(line)
            else:
                if in_table and current_table:
                    tables.append('\n'.join(current_table))
                    current_table = []
                in_table = False
        
        # Don't forget last table
        if current_table:
            tables.append('\n'.join(current_table))
        
        return tables
