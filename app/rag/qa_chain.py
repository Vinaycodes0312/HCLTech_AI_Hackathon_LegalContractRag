"""
QA Chain Module
Question-answering chain with retrieval and generation
"""
from typing import Dict, Optional, List
import logging

from .gemini_llm import GeminiLLM
from .prompt_templates import PromptTemplates
from ..retrieval.retriever import Retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QAChain:
    """
    Question-answering chain combining retrieval and generation
    Implements RAG pattern: Retrieve → Augment → Generate
    """
    
    def __init__(
        self,
        llm: GeminiLLM,
        retriever: Retriever,
        prompt_templates: Optional[PromptTemplates] = None
    ):
        """
        Initialize QA chain
        
        Args:
            llm: Gemini LLM instance
            retriever: Retriever instance
            prompt_templates: Prompt templates (uses default if None)
        """
        self.llm = llm
        self.retriever = retriever
        self.templates = prompt_templates or PromptTemplates()
        
        logger.info("QA Chain initialized")
    
    def answer(
        self,
        question: str,
        top_k: Optional[int] = None,
        return_sources: bool = True
    ) -> Dict:
        """
        Answer a question using RAG
        
        Args:
            question: User's question
            top_k: Number of context chunks to retrieve
            return_sources: Whether to return source citations
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            logger.info(f"📥 Processing question: {question[:100]}...")
            
            # Step 1: Retrieve relevant context
            logger.info("🔍 Retrieving relevant context...")
            context, sources = self.retriever.get_context_for_llm(question, top_k)
            
            if not context:
                logger.warning("⚠️ No context retrieved for question")
                return {
                    "answer": "No relevant information found in the uploaded contracts. Please upload contracts first or try rephrasing your question.",
                    "sources": [],
                    "question": question,
                    "success": False,
                    "error": "No context retrieved"
                }
            
            logger.info(f"✅ Retrieved {len(sources)} context chunks")
            
            # Step 2: Generate prompt
            prompt = self.templates.qa_prompt(context, question)
            
            # Step 3: Generate answer with retry logic
            logger.info("🤖 Generating answer with Gemini...")
            answer = self.llm.generate(prompt)
            
            # Step 4: Format response
            result = {
                "answer": answer,
                "question": question,
                "success": True
            }
            
            if return_sources:
                result["sources"] = self._format_sources(sources)
            
            logger.info("✅ Successfully generated answer")
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error in QA chain: {error_msg}")
            
            # Provide user-friendly error message
            user_message = error_msg
            if "quota" in error_msg.lower():
                user_message = "API quota limit reached. Please wait a few hours or try again later. The free API has daily limits."
            elif "rate limit" in error_msg.lower():
                user_message = "Too many requests. Please wait 30 seconds and try again."
            elif "timeout" in error_msg.lower():
                user_message = "Request timed out. Try asking a simpler question or reducing context chunks in settings."
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                user_message = "Network error. Please check your internet connection and try again."
            elif "unavailable" in error_msg.lower():
                user_message = "Gemini API is temporarily unavailable. Please try again in a few minutes."
            
            return {
                "answer": user_message,
                "sources": [],
                "question": question,
                "success": False,
                "error": error_msg
            }
    
    def _format_sources(self, sources: List[Dict]) -> List[Dict]:
        """
        Format sources for output
        
        Args:
            sources: List of source metadata dictionaries
            
        Returns:
            Formatted source list
        """
        formatted = []
        seen = set()
        
        for source in sources:
            # Create unique key to avoid duplicates
            key = (source['contract_name'], source['page_number'])
            
            if key not in seen:
                formatted.append({
                    "contract": source['contract_name'],
                    "page": source['page_number']
                })
                seen.add(key)
        
        return formatted
    
    def validate_answer(self, answer: str, context: str) -> bool:
        """
        Validate if answer is grounded in context
        
        Args:
            answer: Generated answer
            context: Source context
            
        Returns:
            True if valid, False otherwise
        """
        try:
            prompt = self.templates.validation_prompt(answer, context)
            response = self.llm.generate(prompt)
            
            is_valid = response.strip().upper().startswith("VALID")
            
            if not is_valid:
                logger.warning(f"Answer validation failed: {response}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error in validation: {str(e)}")
            return False
