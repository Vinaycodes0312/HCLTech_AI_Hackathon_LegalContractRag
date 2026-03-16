"""
Gemini Embedder Module
Generate embeddings using Google's Gemini Embedding API
"""
import google.generativeai as genai
from typing import List
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiEmbedder:
    """Generate embeddings using Gemini API"""
    
    def __init__(self, api_key: str, model: str = "models/embedding-001"):
        """
        Initialize Gemini embedder
        
        Args:
            api_key: Google Gemini API key
            model: Embedding model name
        """
        genai.configure(api_key=api_key)
        self.model = model
        logger.info(f"Initialized Gemini Embedder with model: {model}")
    
    def embed_text(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            task_type: Type of embedding task:
                - "retrieval_document" for documents to be stored
                - "retrieval_query" for search queries
                
        Returns:
            Embedding vector as list of floats
        """
        try:
            if not text.strip():
                raise ValueError("Cannot embed empty text")
            
            response = genai.embed_content(
                model=self.model,
                content=text,
                task_type=task_type
            )
            
            return response["embedding"]
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def embed_batch(
        self, 
        texts: List[str], 
        task_type: str = "retrieval_document",
        batch_size: int = 100,
        delay: float = 0.1
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to embed
            task_type: Type of embedding task
            batch_size: Number of texts to process at once
            delay: Delay between batches to avoid rate limiting
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        total = len(texts)
        
        logger.info(f"Generating embeddings for {total} texts in batches of {batch_size}")
        
        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            for text in batch:
                try:
                    embedding = self.embed_text(text, task_type)
                    batch_embeddings.append(embedding)
                except Exception as e:
                    logger.warning(f"Failed to embed text at index {i}: {str(e)}")
                    # Use zero vector as fallback
                    batch_embeddings.append([0.0] * 768)  # Standard embedding dimension
            
            embeddings.extend(batch_embeddings)
            
            # Progress update
            processed = min(i + batch_size, total)
            logger.info(f"Progress: {processed}/{total} embeddings generated")
            
            # Rate limiting
            if i + batch_size < total:
                time.sleep(delay)
        
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query
        
        Args:
            query: Search query text
            
        Returns:
            Query embedding vector
        """
        return self.embed_text(query, task_type="retrieval_query")
