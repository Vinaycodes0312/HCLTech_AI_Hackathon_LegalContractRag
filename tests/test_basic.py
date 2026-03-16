"""
Test Suite for Bussiness Contract Search System
Run with: pytest tests/
"""
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.chunker import Chunker
from app.ingestion.pdf_loader import PDFLoader


class TestChunker:
    """Test the chunking functionality"""
    
    def test_chunker_initialization(self):
        """Test chunker can be initialized"""
        chunker = Chunker(chunk_size=100, chunk_overlap=20)
        assert chunker.chunk_size == 100
        assert chunker.chunk_overlap == 20
    
    def test_chunk_text(self):
        """Test basic text chunking"""
        chunker = Chunker(chunk_size=50, chunk_overlap=10)
        
        text = "This is a test document. " * 100
        metadata = {"contract_name": "test.pdf", "page_number": 1}
        
        chunks = chunker.chunk_text(text, metadata)
        
        assert len(chunks) > 0
        assert all('page_content' in chunk for chunk in chunks)
        assert all('metadata' in chunk for chunk in chunks)
    
    def test_empty_text(self):
        """Test chunking empty text"""
        chunker = Chunker()
        chunks = chunker.chunk_text("", {"test": "metadata"})
        assert len(chunks) == 0


class TestPDFLoader:
    """Test PDF loading functionality"""
    
    def test_loader_initialization(self):
        """Test loader can be initialized"""
        loader = PDFLoader()
        assert loader is not None
    
    # Note: Actual PDF loading tests would require sample PDF files
    # For a complete test suite, add sample PDFs to tests/fixtures/


# Add more tests as needed
# Example test structure for other components:

"""
class TestVectorStore:
    def test_create_index(self):
        pass
    
    def test_add_texts(self):
        pass
    
    def test_similarity_search(self):
        pass


class TestRetriever:
    def test_retrieve(self):
        pass
    
    def test_deduplication(self):
        pass


class TestGeminiLLM:
    @pytest.mark.skipif(not os.getenv('GEMINI_API_KEY'), reason="No API key")
    def test_generate(self):
        pass
"""

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
