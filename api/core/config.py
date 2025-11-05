"""
Configuration management
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    APP_NAME: str = "FieldCoachAI Core AI API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS - Configure these for production
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React default
        "http://localhost:3001",  # Alternative React port
        "http://localhost:4200",  # Angular default
        "http://localhost:5173",  # Vite default
        "http://localhost:8080",  # Vue default
        "*"  # Remove this in production, specify exact origins
    ]
    
    # OpenAI Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 2000
    
    # Model Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    YOLO_MODEL_PATH: str = str(BASE_DIR / "Bird's eye view" / "weights" / "yolov5m.pt")
    DEEPSORT_CONFIG_PATH: str = str(BASE_DIR / "Bird's eye view" / "deep_sort_pytorch" / "configs" / "deep_sort.yaml")
    
    # Video Processing
    MAX_VIDEO_SIZE_MB: int = 500
    TEMP_DIR: str = "temp"
    OUTPUT_DIR: str = "output"
    
    # Play Segmentation
    MIN_PLAY_DURATION: float = 2.0  # seconds
    MAX_PLAY_DURATION: float = 30.0  # seconds
    BALL_MOVEMENT_THRESHOLD: float = 50.0  # pixels
    PLAYER_CLUSTERING_THRESHOLD: float = 100.0  # pixels
    
    # AI Grading
    GRADING_SCALE_MIN: int = 0
    GRADING_SCALE_MAX: int = 100
    
    # Football Positions
    POSITIONS: List[str] = [
        "QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB", "K", "P"
    ]
    
    # Grading Criteria
    GRADING_CRITERIA: dict = {
        "QB": ["arm_strength", "accuracy", "decision_making", "pocket_presence", "footwork"],
        "RB": ["vision", "ball_security", "power", "speed", "blocking"],
        "WR": ["route_running", "hands", "speed", "separation", "blocking"],
        "TE": ["route_running", "hands", "blocking", "awareness"],
        "OL": ["pass_blocking", "run_blocking", "footwork", "hand_placement", "awareness"],
        "DL": ["pass_rush", "run_defense", "hand_usage", "leverage", "pursuit"],
        "LB": ["tackling", "coverage", "run_defense", "blitz", "awareness"],
        "DB": ["coverage", "ball_skills", "tackling", "awareness", "footwork"],
        "K": ["accuracy", "distance", "consistency"],
        "P": ["accuracy", "distance", "hang_time"],
        "UNKNOWN": ["overall_performance", "effort", "awareness", "fundamentals"]  # Generic criteria for unknown positions
    }
    
    class Config:
        # Load .env from project root (parent of api/)
        # Calculate path relative to this file's location
        _base_dir = Path(__file__).resolve().parent.parent.parent
        env_file = str(_base_dir / ".env")
        case_sensitive = True

settings = Settings()

# Create necessary directories
os.makedirs(settings.TEMP_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

