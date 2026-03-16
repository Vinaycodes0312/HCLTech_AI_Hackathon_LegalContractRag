"""
Configuration Management for Bussiness Contract Search System
Loads environment variables and provides centralized config access
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    
    # Application
    app_name: str = Field(default="Bussiness Contract Search System", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Paths
    faiss_index_path: str = Field(default="./data/faiss_index", alias="FAISS_INDEX_PATH")
    upload_dir: str = Field(default="./data/uploads", alias="UPLOAD_DIR")
    
    # Chunking Parameters
    chunk_size: int = Field(default=1200, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    
    # Retrieval Parameters
    top_k_retrieval: int = Field(default=7, alias="TOP_K_RETRIEVAL")
    top_k_final: int = Field(default=5, alias="TOP_K_FINAL")
    
    # Gemini Model Settings
    embedding_model: str = Field(default="models/embedding-001", alias="EMBEDDING_MODEL")
    generation_model: str = Field(default="gemini-1.5-flash", alias="GENERATION_MODEL")
    temperature: float = Field(default=0.1, alias="TEMPERATURE")
    top_p: float = Field(default=0.8, alias="TOP_P")
    max_output_tokens: int = Field(default=1024, alias="MAX_OUTPUT_TOKENS")
    
    # Upload Settings
    max_file_size: int = Field(default=10485760, alias="MAX_FILE_SIZE")  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        Path(self.faiss_index_path).mkdir(parents=True, exist_ok=True)
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()
