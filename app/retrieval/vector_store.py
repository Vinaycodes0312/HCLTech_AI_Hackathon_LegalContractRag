"""
Vector Store Module
FAISS-based vector storage with persistence
"""
import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """
    FAISS vector store for semantic search
    Handles embedding storage, retrieval, and persistence
    """
    
    def __init__(self, index_path: str, dimension: int = 768):
        """
        Initialize vector store
        
        Args:
            index_path: Directory to save/load FAISS index
            dimension: Embedding dimension (768 for Gemini embedding-001)
        """
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.dimension = dimension
        self.index: Optional[faiss.Index] = None
        self.texts: List[str] = []
        self.metadatas: List[Dict] = []
        
        # Try to load existing index
        self.load()
        
        # Create new index if none exists
        if self.index is None:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        # Using IndexFlatL2 for exact L2 distance search
        # For larger datasets, consider IndexIVFFlat or IndexHNSWFlat
        self.index = faiss.IndexFlatL2(self.dimension)
        self.texts = []
        self.metadatas = []
        logger.info(f"Created new FAISS index with dimension {self.dimension}")
    
    def add_texts(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict]
    ) -> List[int]:
        """
        Add texts and their embeddings to the vector store
        
        Args:
            texts: List of text chunks
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            
        Returns:
            List of IDs for added texts
        """
        if len(texts) != len(embeddings) or len(texts) != len(metadatas):
            raise ValueError("texts, embeddings, and metadatas must have same length")
        
        if not texts:
            return []
        
        # Convert embeddings to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Normalize embeddings for cosine similarity (optional but recommended)
        # faiss.normalize_L2(embeddings_array)
        
        # Add to FAISS index
        start_id = len(self.texts)
        self.index.add(embeddings_array)
        
        # Store texts and metadata
        self.texts.extend(texts)
        self.metadatas.extend(metadatas)
        
        ids = list(range(start_id, start_id + len(texts)))
        
        logger.info(f"Added {len(texts)} texts to vector store. Total: {len(self.texts)}")
        return ids
    
    def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[str, Dict, float]]:
        """
        Search for similar texts using embedding
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (text, metadata, distance)
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Vector store is empty")
            return []
        
        # Ensure k doesn't exceed available documents
        k = min(k, self.index.ntotal)
        
        # Convert query to numpy array
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_array, k)
        
        # Prepare results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.texts):  # Valid index
                results.append((
                    self.texts[idx],
                    self.metadatas[idx],
                    float(dist)
                ))
        
        logger.info(f"Retrieved {len(results)} results for query")
        return results
    
    def save(self):
        """Save FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            index_file = self.index_path / "faiss.index"
            faiss.write_index(self.index, str(index_file))
            
            # Save texts and metadata
            data_file = self.index_path / "data.pkl"
            with open(data_file, 'wb') as f:
                pickle.dump({
                    'texts': self.texts,
                    'metadatas': self.metadatas
                }, f)
            
            logger.info(f"Saved vector store to {self.index_path}")
            
        except Exception as e:
            logger.error(f"Failed to save vector store: {str(e)}")
            raise
    
    def load(self) -> bool:
        """
        Load FAISS index and metadata from disk
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            index_file = self.index_path / "faiss.index"
            data_file = self.index_path / "data.pkl"
            
            if not index_file.exists() or not data_file.exists():
                logger.info("No existing index found")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(str(index_file))
            
            # Load texts and metadata
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
                self.texts = data['texts']
                self.metadatas = data['metadatas']
            
            logger.info(f"Loaded vector store with {len(self.texts)} documents from {self.index_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load vector store: {str(e)}")
            return False
    
    def clear(self):
        """Clear all data and create new index"""
        self._create_new_index()
        logger.info("Vector store cleared")
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector store
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_documents": len(self.texts),
            "dimension": self.dimension,
            "index_size": self.index.ntotal if self.index else 0
        }
