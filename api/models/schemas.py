"""Pydantic schemas for API requests and responses"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime

#Enum

class PlayerPosition(str, Enum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    OL = "OL"
    DL = "DL"
    LB = "LB"
    DB = "DB"
    K = "K"
    P = "P"
    LS = "LS"
    ATH = "ATH"
    UNKNOWN = "UNKNOWN"

# Video Analysis Request

class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float

class DetectedObject(BaseModel):
    """Detected object in the video"""
    object_id : int = Field(default = -1, description= "Tracking ID")
    label: str = Field(description = "Object label(player, ball, etc.)")

    bbox: BoundingBox
    confidence: float = Field(ge=0.0, le = 1.0)
    team_color: Optional[str] = None

class FrameAnalysis(BaseModel):
    """Analysis of a single frame"""
    frame_number: int 
    timestamp: float 
    detected_objects: List[DetectedObject]
    player_count: int
    ball_detected: bool

class PlaySegment(BaseModel):
    """A segmented play from video"""
    play_id: int
    start_time: float
    end_time: float
    duration: float
    start_frame: int
    end_frame: int
    player_count: int
    play_type: Optional[str] = "unknown"
    key_events: List[str] = Field(default_factory=list)

class VideoAnalysisRequest(BaseModel):
    """Request for video analysis"""
    video_path: str = Field(description="Path to video file")
    analyze_frames: bool = Field(default=True, description="Perform frame-by-frame analysis")
    detect_plays: bool = Field(default=True, description="Segment plays automatically")
    track_players: bool = Field(default=True, description="Track player movements")

class VideoAnalysisResponse(BaseModel):
    """Response from video analysis"""
    video_id: str
    duration: float
    total_frames: int
    fps: float
    plays: List[PlaySegment]
    frame_analyses: Optional[List[FrameAnalysis]] = None
    processing_time: float

class VideoVisualizationRequest(BaseModel):
    """Request for video visualization"""
    original_video_path: str
    output_path: Optional[str] = None

#Grading Models

class GradingCriteria(BaseModel):
    """Grading criteria for a specific skill"""
    criterion: str
    score: float = Field(ge=0, le=100)
    feedback: str
    examples: List[str] = Field(default_factory=list)

class PlayerGrade(BaseModel):
    """Grade for a single player"""
    player_id: int
    position: PlayerPosition
    overall_score: float = Field(ge=0, le=100)
    letter_grade: str = Field(default="F")
    criteria_scores: List[GradingCriteria] = Field(default_factory=list)
    qualitative_feedback: str = Field(default="")
    strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    training_citations: List[str] = Field(default_factory=list)

class PlayGradingRequest(BaseModel):
    """Request to grade a play"""
    video_id: str
    play_id: Optional[int] = None
    player_positions: Optional[Dict[int, str]] = None
    play_context: Optional[str] = ""

class PlayGradingResponse(BaseModel):
    """Response with play grades"""
    video_id: str
    play_id: int
    player_grades: List[PlayerGrade]
    play_summary: str
    processing_time: float

class BulkGradingRequest(BaseModel):
    """Request to grade all plays in a video"""
    video_id: str
    player_positions: Optional[Dict[int, str]] = None

class BulkGradingResponse(BaseModel):
    """Response with grades for all plays"""
    video_id: str
    total_plays: int
    play_grades: List[PlayGradingResponse]
    processing_time: float

#Q&A Models

class CoachingQuestion(BaseModel):
    """Coaching question from user"""
    question: str
    role: str = Field(default="coach", description="User role: coach or player")

class CoachingAnswer(BaseModel):
    """Answer to coaching question"""
    question: str
    answer: str
    citations: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)

#Health Check

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    models_loaded: bool
    version: str