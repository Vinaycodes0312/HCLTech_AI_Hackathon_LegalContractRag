"""
Gemini LLM Module
Google Gemini API integration for answer generation
"""
import google.generativeai as genai
from typing import Optional, Dict
import logging
import time
from google.api_core import exceptions as google_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiLLM:
    """
    Gemini LLM wrapper for answer generation
    Optimized for grounded, factual responses with enhanced reliability
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.1,
        top_p: float = 0.8,
        max_output_tokens: int = 1024
    ):
        """
        Initialize Gemini LLM
        
        Args:
            api_key: Google Gemini API key
            model: Model name (gemini-1.5-flash or gemini-1.5-pro)
            temperature: Sampling temperature (0-1, lower = more deterministic)
            top_p: Top-p sampling parameter
            max_output_tokens: Maximum tokens in response
        """
        genai.configure(api_key=api_key)
        
        self.model_name = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_output_tokens = max_output_tokens
        
        # Request throttling
        self._last_request_time = 0
        self._min_request_interval = 1.5  # Minimum seconds between requests
        
        # Initialize model with generation config
        self.generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
        )
        
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config=self.generation_config
        )
        
        logger.info(f"Initialized Gemini LLM: {model} (temp={temperature}, top_p={top_p})")
    
    def _throttle_request(self):
        """Ensure minimum time between API requests"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last
            logger.debug(f"⏱️ Throttling: waiting {wait_time:.1f}s")
            time.sleep(wait_time)
        
        self._last_request_time = time.time()
    
    def generate(self, prompt: str, max_retries: int = 5) -> str:
        """
        Generate response from prompt with enhanced retry logic
        
        Args:
            prompt: Input prompt
            max_retries: Maximum number of retries for rate limit errors
            
        Returns:
            Generated text response
        """
        # Throttle requests to avoid rate limits
        self._throttle_request()
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                
                # Extract text from response
                result_text = None
                if hasattr(response, 'text'):
                    result_text = response.text
                else:
                    logger.warning("No text in response, checking candidates")
                    if response.candidates:
                        result_text = response.candidates[0].content.parts[0].text
                    else:
                        raise ValueError("No valid response from Gemini")
                
                return result_text
                
            except google_exceptions.ResourceExhausted as e:
                # Rate limit or quota exceeded
                error_msg = str(e)
                last_error = e
                logger.warning(f"⚠️ Quota/Rate limit (attempt {attempt + 1}/{max_retries}): {error_msg[:200]}")
                
                if attempt < max_retries - 1:
                    # Progressive backoff: 3, 6, 12, 24 seconds
                    wait_time = 3 * (2 ** attempt)
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    # Last attempt failed
                    if "quota" in error_msg.lower():
                        raise Exception("API quota limit reached. The free tier has a daily limit. Please wait a few hours or upgrade your API plan.")
                    else:
                        raise Exception(f"Rate limit exceeded. Please wait a moment and try again. Error: {error_msg[:150]}")
            
            except google_exceptions.InvalidArgument as e:
                # Invalid request - don't retry
                error_msg = str(e)
                logger.error(f"Invalid request: {error_msg}")
                raise Exception(f"Invalid request: {error_msg[:200]}")
            
            except google_exceptions.DeadlineExceeded as e:
                # Timeout - retry with longer wait
                error_msg = str(e)
                last_error = e
                logger.warning(f"⏱️ Request timeout (attempt {attempt + 1}/{max_retries})")
                
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise Exception("Request timed out multiple times. Please try a simpler question or reduce context chunks.")
            
            except google_exceptions.ServiceUnavailable as e:
                # Service down - retry
                last_error = e
                logger.warning(f"🔧 Service unavailable (attempt {attempt + 1}/{max_retries})")
                
                if attempt < max_retries - 1:
                    wait_time = 5 * (2 ** attempt)
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise Exception("Gemini API is currently unavailable. Please try again later.")
                        
            except Exception as e:
                # Unknown error
                error_msg = str(e)
                logger.error(f"❌ Unexpected error: {error_msg}")
                
                # If it's a known transient error, retry
                if any(word in error_msg.lower() for word in ['timeout', 'connection', 'network']):
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = 5
                        logger.info(f"⏳ Network issue, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise Exception(f"Network error after {max_retries} attempts: {error_msg[:150]}")
                else:
                    # Unknown error, don't retry
                    raise
        
        # Should not reach here, but just in case
        if last_error:
            raise Exception(f"Failed after {max_retries} retries. Last error: {str(last_error)[:150]}")
        raise Exception("Failed to generate response after all retries")
    
    def generate_with_safety(self, prompt: str) -> Dict:
        """
        Generate response with safety ratings and metadata
        
        Args:
            prompt: Input prompt
            
        Returns:
            Dictionary with text, safety ratings, and metadata
        """
        try:
            response = self.model.generate_content(prompt)
            
            result = {
                "text": response.text if hasattr(response, 'text') else "",
                "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else "UNKNOWN",
                "safety_ratings": {},
                "success": True
            }
            
            # Extract safety ratings if available
            if response.candidates and response.candidates[0].safety_ratings:
                for rating in response.candidates[0].safety_ratings:
                    result["safety_ratings"][rating.category.name] = rating.probability.name
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "text": "",
                "error": str(e),
                "success": False
            }
    
    def chat(self, messages: list) -> str:
        """
        Multi-turn chat conversation
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Generated response
        """
        try:
            # Convert messages to Gemini format
            chat = self.model.start_chat(history=[])
            
            # Send messages
            for msg in messages[:-1]:  # All but last
                if msg['role'] == 'user':
                    chat.send_message(msg['content'])
            
            # Get response for last message
            response = chat.send_message(messages[-1]['content'])
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise
