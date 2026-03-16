"""
PDF Loader Module
Extracts text from PDF files with page-level metadata
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFLoader:
    """Load and extract text from PDF documents"""
    
    def __init__(self):
        """Initialize PDF loader"""
        pass
    
    def load(self, file_path: str) -> List[Dict]:
        """
        Load a PDF file and extract text with metadata
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing page content and metadata
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            if not file_path.suffix.lower() == '.pdf':
                raise ValueError(f"File is not a PDF: {file_path}")
            
            logger.info(f"Loading PDF: {file_path.name}")
            
            # Open PDF with PyMuPDF
            doc = fitz.open(file_path)
            pages_data = []
            
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Only add pages with actual content
                if text.strip():
                    pages_data.append({
                        "page_content": text,
                        "metadata": {
                            "contract_name": file_path.name,
                            "page_number": page_num + 1,  # 1-indexed for user display
                            "total_pages": len(doc),
                            "source": str(file_path)
                        }
                    })
            
            doc.close()
            logger.info(f"Extracted {len(pages_data)} pages from {file_path.name}")
            
            return pages_data
            
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {str(e)}")
            raise
    
    def load_multiple(self, file_paths: List[str]) -> List[Dict]:
        """
        Load multiple PDF files
        
        Args:
            file_paths: List of paths to PDF files
            
        Returns:
            Combined list of all pages from all documents
        """
        all_pages = []
        
        for file_path in file_paths:
            try:
                pages = self.load(file_path)
                all_pages.extend(pages)
            except Exception as e:
                logger.warning(f"Skipping file {file_path}: {str(e)}")
                continue
        
        logger.info(f"Loaded {len(all_pages)} total pages from {len(file_paths)} documents")
        return all_pages
