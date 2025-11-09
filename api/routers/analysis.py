"""
Video analysis endpoints
"""
from fastapi import APIRouter, HTTPException, Request, File, UploadFile
from fastapi.responses import JSONResponse
import logging
import shutil
from pathlib import Path

from api.models.schemas import VideoAnalysisRequest, VideoAnalysisResponse, VideoVisualizationRequest
from api.services.video_analyzer import VideoAnalyzer
from api.services.video_storage import video_storage
from api.services.video_visualizer import VideoVisualizer
from api.core.config import settings
from api.routers.examples import EXAMPLES

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/video", 
    response_model=VideoAnalysisResponse,
    responses={
        200: {
            "description": "Successful video analysis",
            "content": {
                "application/json": {
                    "example": EXAMPLES["video_analysis"]
                }
            }
        },
        400: {"description": "Invalid video file or path"},
        503: {"description": "CV models not loaded"}
    },
    summary="Analyze Video",
    description="""
    Comprehensive video analysis with computer vision.
    
    **Features:**
    - Player detection and tracking (YOLOv5 + DeepSORT)
    - Ball detection and tracking
    - Automatic play segmentation
    - Frame-by-frame analysis (optional)
    - Player count and positioning
    
    **Performance Notes:**
    - Frame-by-frame analysis is CPU/GPU intensive
    - Set `analyze_frames: false` for faster processing
    - Processing time scales with video length
    - Recommended: Process videos < 5 minutes
    
    **Requires:** CV models installed (opencv, torch, torchvision)
    """
)
async def analyze_video(
    request: Request,
    analysis_request: VideoAnalysisRequest
):
    """
    Analyze a video file
    """
    try:
        model_loader = request.app.state.model_loader
        
        if not model_loader.is_ready():
            raise HTTPException(
                status_code=503,
                detail="CV models not loaded. API running in limited mode."
            )
        
        # Create analyzer
        analyzer = VideoAnalyzer(model_loader)
        
        # Analyze video
        result = await analyzer.analyze_video(
            video_path=analysis_request.video_path,
            analyze_frames=analysis_request.analyze_frames,
            detect_plays=analysis_request.detect_plays,
            track_players=analysis_request.track_players
        )
        
        # Store analysis results for later use (e.g., grading)
        video_storage.store_analysis(result)
        logger.info(f"Stored analysis results for video_id: {result.video_id} ({len(result.plays)} plays)")
        
        return result
        
    except HTTPException:
        # Re-raise HTTPException so FastAPI can handle it properly
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing video: {str(e)}")

@router.post("/video/upload", response_model=dict)
async def upload_video(
    file: UploadFile = File(...)
):
    """
    Upload a video file for analysis
    
    Saves the video to temporary storage and returns the path
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Supported: MP4, AVI, MOV, MKV"
            )
        
        # Save file
        file_path = Path(settings.TEMP_DIR) / file.filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Video uploaded: {file_path}")
        
        return {
            "message": "Video uploaded successfully",
            "video_path": str(file_path),
            "filename": file.filename,
            "size_bytes": file_path.stat().st_size
        }
        
    except HTTPException:
        # Re-raise HTTPException so FastAPI can handle it properly
        raise
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")

@router.get("/video/{video_id}/plays", response_model=list)
async def get_video_plays(video_id: str):
    """
    Get segmented plays for a video
    
    Returns the plays detected during video analysis.
    Video must be analyzed first using POST /api/v1/analysis/video
    """
    analysis = video_storage.get_analysis(video_id)
    
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Video analysis not found for video_id: {video_id}. "
                   f"Please analyze the video first using POST /api/v1/analysis/video"
        )
    
    logger.info(f"Retrieved {len(analysis.plays)} plays for video_id: {video_id}")
    return analysis.plays

@router.get("/video/{video_id}", response_model=VideoAnalysisResponse)
async def get_video_analysis(video_id: str):
    """
    Get complete video analysis results
    
    Returns the full analysis including plays, metadata, and frame analyses.
    Video must be analyzed first using POST /api/v1/analysis/video
    """
    analysis = video_storage.get_analysis(video_id)
    
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Video analysis not found for video_id: {video_id}. "
                   f"Please analyze the video first using POST /api/v1/analysis/video"
        )
    
    logger.info(f"Retrieved analysis for video_id: {video_id}")
    return analysis

@router.get("/videos", response_model=list)
async def list_videos():
    """
    List all video IDs that have been analyzed
    
    Returns a list of video_id strings that have analysis results stored.
    """
    video_ids = video_storage.list_videos()
    logger.info(f"Listed {len(video_ids)} videos with analysis")
    return video_ids

@router.post("/video/{video_id}/visualize", response_model=dict)
async def visualize_video(
    video_id: str,
    request: VideoVisualizationRequest
):
    """
    Generate visualized video with bounding boxes and analysis
    
    Creates a new video file with:
    - Bounding boxes around detected players and ball
    - Player tracking IDs (P1, P2, etc.)
    - Team colors (if detected)
    - Confidence scores
    - Frame numbers and timestamps
    
    **Requirements:**
    - Video must be analyzed first with `analyze_frames=true`
    - Original video file must still exist at the provided path
    
    **Example:**
    ```json
    {
      "original_video_path": "temp/video.mp4",
      "output_path": "output/video_visualized.mp4"  // Optional
    }
    ```
    
    **Returns:**
    - Path to the generated visualized video
    - Processing statistics
    """
    try:
        # Check if analysis exists
        analysis = video_storage.get_analysis(video_id)
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Video analysis not found for video_id: {video_id}. "
                       f"Please analyze the video first using POST /api/v1/analysis/video"
            )
        
        if not analysis.frame_analyses:
            raise HTTPException(
                status_code=400,
                detail=f"Frame analyses not available for video_id: {video_id}. "
                       f"Re-run analysis with analyze_frames=true"
            )
        
        # Check if original video exists
        original_path = Path(request.original_video_path)
        if not original_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Original video not found: {request.original_video_path}"
            )
        
        # Create visualizer
        visualizer = VideoVisualizer()
        
        # Generate visualized video
        output_file = visualizer.visualize_video(
            video_id=video_id,
            original_video_path=str(original_path),
            output_path=request.output_path
        )
        
        output_path_obj = Path(output_file)
        
        return {
            "message": "Video visualization complete",
            "video_id": video_id,
            "original_video": str(original_path),
            "visualized_video": output_file,
            "output_path": output_file,
            "file_size_mb": output_path_obj.stat().st_size / (1024 * 1024) if output_path_obj.exists() else 0,
            "frames_processed": len(analysis.frame_analyses),
            "plays_detected": len(analysis.plays)
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error visualizing video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error visualizing video: {str(e)}")

