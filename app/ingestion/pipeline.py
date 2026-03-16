"""
Ingestion Pipeline Module
End-to-end pipeline for processing and indexing documents
"""
from typing import List
import logging
from pathlib import Path

from .pdf_loader import PDFLoader
from .chunker import Chunker
from .gemini_embedder import GeminiEmbedder
from ..retrieval.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Complete pipeline for document ingestion:
    PDF → Extract → Chunk → Embed → Store in FAISS
    """
    
    def __init__(
        self,
        embedder: GeminiEmbedder,
        vector_store: VectorStore,
        chunk_size: int = 1200,
        chunk_overlap: int = 200
    ):
        """
        Initialize ingestion pipeline
        
        Args:
            embedder: Gemini embedder instance
            vector_store: Vector store instance
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.pdf_loader = PDFLoader()
        self.chunker = Chunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedder = embedder
        self.vector_store = vector_store
        
        logger.info("Ingestion pipeline initialized")
    
    def ingest_file(self, file_path: str) -> dict:
        """
        Ingest a single PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with ingestion statistics
        """
        try:
            logger.info(f"Starting ingestion for: {file_path}")
            
            # Step 1: Load PDF
            logger.info("Step 1/4: Loading PDF...")
            pages = self.pdf_loader.load(file_path)
            
            # Step 2: Chunk documents
            logger.info("Step 2/4: Chunking text...")
            chunks = self.chunker.chunk_documents(pages)
            
            # Step 3: Generate embeddings
            logger.info("Step 3/4: Generating embeddings...")
            texts = [chunk['page_content'] for chunk in chunks]
            embeddings = self.embedder.embed_batch(texts, task_type="retrieval_document")
            
            # Step 4: Add to vector store
            logger.info("Step 4/4: Storing in vector database...")
            metadatas = [chunk['metadata'] for chunk in chunks]
            self.vector_store.add_texts(texts, embeddings, metadatas)
            
            # Save index to disk
            self.vector_store.save()
            
            stats = {
                "file_name": Path(file_path).name,
                "pages_processed": len(pages),
                "chunks_created": len(chunks),
                "embeddings_generated": len(embeddings),
                "status": "success"
            }
            
            logger.info(f"Ingestion complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Ingestion failed for {file_path}: {str(e)}")
            return {
                "file_name": Path(file_path).name,
                "status": "failed",
                "error": str(e)
            }
    
    def ingest_files(self, file_paths: List[str]) -> List[dict]:
        """
        Ingest multiple PDF files
        
        Args:
            file_paths: List of paths to PDF files
            
        Returns:
            List of ingestion statistics for each file
        """
        results = []
        
        logger.info(f"Starting batch ingestion for {len(file_paths)} files")
        
        for file_path in file_paths:
            result = self.ingest_file(file_path)
            results.append(result)
        
        # Summary
        successful = sum(1 for r in results if r['status'] == 'success')
        logger.info(f"Batch ingestion complete: {successful}/{len(file_paths)} files processed successfully")
        
        return results
