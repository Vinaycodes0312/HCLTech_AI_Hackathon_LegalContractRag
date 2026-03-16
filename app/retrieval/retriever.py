"""
Retriever Module
Semantic retrieval with deduplication and ranking
"""
from typing import List, Dict, Tuple, Optional
import logging
from collections import defaultdict

from .vector_store import VectorStore
from ..ingestion.gemini_embedder import GeminiEmbedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Retriever:
    """
    Semantic retriever with smart deduplication and ranking
    Optimized for legal contract Q&A
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedder: GeminiEmbedder,
        top_k_retrieval: int = 7,
        top_k_final: int = 5
    ):
        """
        Initialize retriever
        
        Args:
            vector_store: Vector store instance
            embedder: Gemini embedder for query embedding
            top_k_retrieval: Initial number of chunks to retrieve
            top_k_final: Final number of chunks to return after deduplication
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.top_k_retrieval = top_k_retrieval
        self.top_k_final = top_k_final
        
        logger.info(f"Retriever initialized (retrieve={top_k_retrieval}, final={top_k_final})")
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: User question
            top_k: Override for number of final results (optional)
            
        Returns:
            List of retrieved chunks with metadata and scores
        """
        if top_k is None:
            top_k = self.top_k_final
        
        try:
            # Step 1: Generate query embedding
            logger.info(f"Retrieving documents for query: {query[:100]}...")
            query_embedding = self.embedder.embed_query(query)
            
            # Step 2: Retrieve from vector store
            initial_results = self.vector_store.similarity_search(
                query_embedding,
                k=self.top_k_retrieval
            )
            
            if not initial_results:
                logger.warning("No results found in vector store")
                return []
            
            # Step 3: Deduplicate overlapping chunks
            deduplicated = self._deduplicate_chunks(initial_results)
            
            # Step 4: Select top-k final results
            final_results = deduplicated[:top_k]
            
            # Step 5: Format results
            formatted_results = []
            for text, metadata, distance in final_results:
                formatted_results.append({
                    "content": text,
                    "metadata": metadata,
                    "score": float(distance),
                    "contract_name": metadata.get("contract_name", "Unknown"),
                    "page_number": metadata.get("page_number", 0)
                })
            
            logger.info(f"Retrieved {len(formatted_results)} final chunks")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            raise
    
    def _deduplicate_chunks(
        self,
        results: List[Tuple[str, Dict, float]]
    ) -> List[Tuple[str, Dict, float]]:
        """
        Remove overlapping chunks, keeping the best one per page
        
        Args:
            results: List of (text, metadata, distance) tuples
            
        Returns:
            Deduplicated list
        """
        # Group by (contract_name, page_number)
        page_chunks = defaultdict(list)
        
        for text, metadata, distance in results:
            key = (
                metadata.get("contract_name", "Unknown"),
                metadata.get("page_number", 0)
            )
            page_chunks[key].append((text, metadata, distance))
        
        # For each page, keep only the chunk with lowest distance (best match)
        deduplicated = []
        for chunks in page_chunks.values():
            # Sort by distance (lower is better)
            chunks.sort(key=lambda x: x[2])
            deduplicated.append(chunks[0])
        
        # Sort all deduplicated chunks by distance
        deduplicated.sort(key=lambda x: x[2])
        
        logger.info(f"Deduplicated {len(results)} → {len(deduplicated)} chunks")
        return deduplicated
    
    def get_context_for_llm(self, query: str, top_k: Optional[int] = None) -> Tuple[str, List[Dict]]:
        """
        Retrieve and format context for LLM
        
        Args:
            query: User question
            top_k: Number of chunks to retrieve
            
        Returns:
            Tuple of (formatted_context, source_metadata)
        """
        chunks = self.retrieve(query, top_k)
        
        if not chunks:
            return "", []
        
        # Format context for LLM
        context_parts = []
        sources = []
        
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Document {i}]")
            context_parts.append(f"Source: {chunk['contract_name']} (Page {chunk['page_number']})")
            context_parts.append(chunk['content'])
            context_parts.append("")  # Blank line between documents
            
            sources.append({
                "contract_name": chunk['contract_name'],
                "page_number": chunk['page_number'],
                "chunk_id": i
            })
        
        formatted_context = "\n".join(context_parts)
        
        return formatted_context, sources
