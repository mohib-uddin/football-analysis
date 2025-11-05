"""
Health check endpoints
"""
from fastapi import APIRouter, Request
from datetime import datetime

from api.models.schemas import HealthCheck
from api.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthCheck)
async def health_check(request: Request):
    """
    Health check endpoint
    
    Returns API status and model availability
    """
    model_loader = request.app.state.model_loader
    
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        models_loaded=model_loader.is_ready() if model_loader else False,
        version=settings.VERSION
    )

