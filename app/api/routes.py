"""
API Routes Module
FastAPI endpoints for the RAG system
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging
import os
from pathlib import Path
import shutil

from ..config import settings
from ..ingestion import IngestionPipeline, GeminiEmbedder
from ..retrieval import VectorStore, Retriever
from ..rag import GeminiLLM, QAChain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize components (will be set by main.py)
pipeline: Optional[IngestionPipeline] = None
qa_chain: Optional[QAChain] = None
vector_store: Optional[VectorStore] = None


def initialize_components():
    """Initialize RAG components"""
    global pipeline, qa_chain, vector_store
    
    try:
        # Initialize embedder
        embedder = GeminiEmbedder(
            api_key=settings.gemini_api_key,
            model=settings.embedding_model
        )
        
        # Initialize vector store
        vector_store = VectorStore(
            index_path=settings.faiss_index_path,
            dimension=3072  # gemini-embedding-001 produces 3072-dim embeddings
        )
        
        # Initialize LLM
        llm = GeminiLLM(
            api_key=settings.gemini_api_key,
            model=settings.generation_model,
            temperature=settings.temperature,
            top_p=settings.top_p,
            max_output_tokens=settings.max_output_tokens
        )
        
        # Initialize retriever
        retriever = Retriever(
            vector_store=vector_store,
            embedder=embedder,
            top_k_retrieval=settings.top_k_retrieval,
            top_k_final=settings.top_k_final
        )
        
        # Initialize ingestion pipeline
        pipeline = IngestionPipeline(
            embedder=embedder,
            vector_store=vector_store,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        # Initialize QA chain
        qa_chain = QAChain(llm=llm, retriever=retriever)
        
        logger.info("All components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        raise


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    question: str = Field(..., description="Question to ask about contracts")
    top_k: Optional[int] = Field(None, description="Number of chunks to retrieve")


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    answer: str
    sources: List[Dict]
    question: str
    success: bool


# API Endpoints

@router.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Bussiness Contract Search System API",
        "version": "1.0.0",
        "status": "running"
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        stats = vector_store.get_stats() if vector_store else {}
        return {
            "status": "healthy",
            "components": {
                "vector_store": vector_store is not None,
                "pipeline": pipeline is not None,
                "qa_chain": qa_chain is not None
            },
            "vector_store_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    """
    Upload and process a PDF contract
    
    - **file**: PDF file to upload
    """
    logger.info(f"📥 Received upload request for file: {file.filename}")
    
    if not pipeline:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        logger.warning(f"❌ Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    logger.info(f"📊 File size: {file_size / 1024:.2f} KB")
    
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum of {settings.max_file_size} bytes"
        )
    
    try:
        # Save uploaded file
        upload_path = Path(settings.upload_dir) / file.filename
        
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"💾 File saved: {upload_path}")
        
        # Process file through pipeline
        logger.info(f"⚙️  Processing file through pipeline...")
        result = pipeline.ingest_file(str(upload_path))
        
        logger.info(f"✅ File processed successfully: {file.filename}")
        logger.info(f"📊 Processing stats: {result}")
        
        return {
            "message": "File uploaded and processed successfully",
            "file_name": file.filename,
            "stats": result
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Upload failed for {file.filename}: {error_msg}")
        
        # Provide specific error messages
        if "API key" in error_msg or "authentication" in error_msg.lower():
            raise HTTPException(
                status_code=401,
                detail=f"API key error during processing: {error_msg}. Check your GEMINI_API_KEY in .env file."
            )
        elif "quota" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail=f"API quota exceeded while processing: {error_msg}. Wait or upgrade your plan."
            )
        elif "Permission denied" in error_msg or "access" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail=f"File access error: {error_msg}. Check file permissions and disk space."
            )
        elif "corrupt" in error_msg.lower() or "invalid" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or corrupted PDF file: {error_msg}. Try a different file."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Upload processing failed: {error_msg}"
            )


@router.post("/query", response_model=QueryResponse)
async def query_contracts(request: QueryRequest):
    """
    Query the uploaded contracts
    
    - **question**: Question to ask about the contracts
    - **top_k**: Optional number of context chunks to retrieve
    """
    logger.info(f"📥 Received query request: '{request.question}' (top_k={request.top_k})")
    
    if not qa_chain:
        raise HTTPException(
            status_code=500, 
            detail="QA system not initialized. Please restart the server."
        )
    
    if not request.question.strip():
        raise HTTPException(
            status_code=400, 
            detail="Question cannot be empty. Please provide a valid question."
        )
    
    # Check if we have any documents indexed
    if vector_store and vector_store.get_stats().get('total_documents', 0) == 0:
        raise HTTPException(
            status_code=404,
            detail="No documents indexed. Please upload PDF contracts before querying."
        )
    
    try:
        logger.info(f"⚙️  Processing query through QA chain...")
        result = qa_chain.answer(
            question=request.question,
            top_k=request.top_k,
            return_sources=True
        )
        logger.info(f"✅ Query completed. Success: {result.get('success', False)}")
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Query failed: {error_msg}")
        
        # Provide specific error messages based on error type
        if "API key" in error_msg or "authentication" in error_msg.lower():
            raise HTTPException(
                status_code=401,
                detail=f"API key error: {error_msg}. Please check your GEMINI_API_KEY in the .env file."
            )
        elif "quota" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail=f"API quota exceeded: {error_msg}. Please wait or upgrade your API plan."
            )
        elif "rate limit" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {error_msg}. Please wait a moment and try again."
            )
        elif "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail=f"Request timeout: {error_msg}. Try asking a simpler question or reducing top_k."
            )
        elif "No relevant information" in error_msg:
            raise HTTPException(
                status_code=404,
                detail="No relevant information found in the uploaded documents. Try rephrasing your question or uploading more contracts."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while processing your question: {error_msg}"
            )


@router.get("/contracts")
async def list_contracts():
    """List all uploaded contracts"""
    try:
        upload_dir = Path(settings.upload_dir)
        
        if not upload_dir.exists():
            return {"contracts": []}
        
        contracts = []
        for file_path in upload_dir.glob("*.pdf"):
            contracts.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "uploaded": file_path.stat().st_mtime
            })
        
        return {"contracts": contracts, "total": len(contracts)}
        
    except Exception as e:
        logger.error(f"Failed to list contracts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list contracts: {str(e)}")


@router.get("/stats")
async def get_stats():
    """Get system statistics"""
    if not vector_store:
        raise HTTPException(status_code=500, detail="Vector store not initialized")
    
    try:
        stats = vector_store.get_stats()
        
        # Add upload directory stats
        upload_dir = Path(settings.upload_dir)
        contract_count = len(list(upload_dir.glob("*.pdf"))) if upload_dir.exists() else 0
        
        return {
            "vector_store": stats,
            "contracts_uploaded": contract_count,
            "settings": {
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
                "top_k_retrieval": settings.top_k_retrieval,
                "embedding_model": settings.embedding_model,
                "generation_model": settings.generation_model
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/clear")
async def clear_index():
    """Clear the vector store index"""
    if not vector_store:
        raise HTTPException(status_code=500, detail="Vector store not initialized")
    
    try:
        vector_store.clear()
        vector_store.save()
        
        return {
            "message": "Vector store cleared successfully",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear index: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear index: {str(e)}")


@router.delete("/contracts/{filename}")
async def delete_contract(filename: str):
    """Delete a specific uploaded contract"""
    try:
        file_path = Path(settings.upload_dir) / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Contract not found")
        
        file_path.unlink()
        
        return {
            "message": f"Contract '{filename}' deleted successfully",
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete contract: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete contract: {str(e)}")
