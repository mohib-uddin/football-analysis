"""
FieldCoachAI - Core AI API
FastAPI backend for video analysis, play segmentation, and AI grading
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import api modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import logging

from api.routers import analysis, grading, health
from api.core.config import settings
from api.services.model_loader import ModelLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model loader
model_loader = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global model_loader
    logger.info("Starting FieldCoachAI API...")
    
    # Load models on startup
    model_loader = ModelLoader()
    await model_loader.load_models()
    app.state.model_loader = model_loader
    
    logger.info("All models loaded successfully!")
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down FieldCoachAI API...")

# Initialize FastAPI app
app = FastAPI(
    title="FieldCoachAI - Core AI API",
    description="""
    Advanced AI-powered football/soccer video analysis platform.
    
    ## Features
    * **Video Analysis**: Player detection, tracking, and movement analysis
    * **Play Segmentation**: Automatic identification of individual plays
    * **AI Grading**: Position-specific player performance grading with detailed feedback
    * **Coaching Q&A**: AI-powered coaching assistance
    
    ## Endpoints
    * `/api/v1/analysis/*` - Video analysis and player tracking
    * `/api/v1/grading/*` - AI grading and feedback
    * `/api/v1/health` - Health check
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Video Analysis"])
app.include_router(grading.router, prefix="/api/v1/grading", tags=["AI Grading"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FieldCoachAI Core AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    # Use import string for reload to work properly
    if settings.DEBUG:
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=True,
            log_level="info"
        )
    else:
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            reload=False,
            log_level="info"
        )

