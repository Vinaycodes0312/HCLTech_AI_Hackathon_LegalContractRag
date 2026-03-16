"""
Main Application Module
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
from pathlib import Path

from .config import settings
from .api import router, initialize_components

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready RAG system for legal contract analysis using Gemini AI",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, prefix="/api", tags=["API"])

# Mount static files for frontend
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    logger.info("Starting Bussiness Contract Search System...")
    logger.info(f"Version: {settings.app_version}")
    
    try:
        # Ensure directories exist
        settings.ensure_directories()
        
        # Initialize RAG components
        initialize_components()
        
        logger.info("Application startup complete")
        logger.info(f"API documentation available at: http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Bussiness Contract Search System...")


@app.get("/")
async def root():
    """Serve frontend or API info"""
    frontend_file = Path(__file__).parent.parent / "static" / "index.html"
    
    if frontend_file.exists():
        return FileResponse(frontend_file)
    else:
        return {
            "message": "Bussiness Contract Search System",
            "version": settings.app_version,
            "api_docs": "/docs",
            "health": "/api/health"
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
