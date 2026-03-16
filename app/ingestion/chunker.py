"""
Chunker Module
Smart text chunking optimized for legal documents
"""
from typing import List, Dict
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Chunker:
    """
    Smart text chunker with overlap for legal documents
    Optimized for Gemini's context window (1200 tokens, 200 overlap)
    """
    
    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 200):
        """
        Initialize chunker
        
        Args:
            chunk_size: Target size for each chunk in tokens (approximate)
            chunk_overlap: Number of tokens to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Rough approximation: 1 token ≈ 4 characters for English
        self.char_per_token = 4
    
    def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Chunk a single text with metadata preservation
        
        Args:
            text: Text content to chunk
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text.strip():
            return []
        
        # Convert token sizes to character sizes
        chunk_size_chars = self.chunk_size * self.char_per_token
        overlap_chars = self.chunk_overlap * self.char_per_token
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Split into chunks
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + chunk_size_chars
            
            # Find a good breaking point (sentence or paragraph boundary)
            if end < len(text):
                # Look for paragraph break first
                break_point = text.rfind('\n\n', start, end)
                if break_point == -1 or break_point < start + overlap_chars:
                    # Look for sentence break
                    break_point = self._find_sentence_boundary(text, start, end)
                
                if break_point > start:
                    end = break_point
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_id'] = chunk_id
                chunk_metadata['chunk_start_char'] = start
                chunk_metadata['chunk_end_char'] = end
                
                chunks.append({
                    "page_content": chunk_text,
                    "metadata": chunk_metadata
                })
                
                chunk_id += 1
            
            # Move start position with overlap
            start = end - overlap_chars if end < len(text) else end
        
        return chunks
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Chunk multiple documents
        
        Args:
            documents: List of document dictionaries with page_content and metadata
            
        Returns:
            List of chunk dictionaries
        """
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_text(doc['page_content'], doc['metadata'])
            all_chunks.extend(chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
        return all_chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers and headers (common patterns)
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def _find_sentence_boundary(self, text: str, start: int, preferred_end: int) -> int:
        """
        Find a sentence boundary near the preferred end position
        
        Args:
            text: Full text
            start: Start position
            preferred_end: Preferred end position
            
        Returns:
            Position of sentence boundary
        """
        # Look for sentence endings: . ! ?
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        
        # Search backwards from preferred_end
        search_start = max(start + self.chunk_overlap * self.char_per_token, start)
        search_text = text[search_start:preferred_end]
        
        best_pos = -1
        for ending in sentence_endings:
            pos = search_text.rfind(ending)
            if pos > best_pos:
                best_pos = pos
        
        if best_pos > 0:
            return search_start + best_pos + 1
        
        return preferred_end
