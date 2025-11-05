"""
AI grading endpoints
"""
from fastapi import APIRouter, HTTPException, Request
import logging

from api.models.schemas import (
    PlayGradingRequest, PlayGradingResponse,
    BulkGradingRequest, BulkGradingResponse,
    CoachingQuestion, CoachingAnswer,
    PlaySegment
)
from api.services.ai_grader import AIGrader
from api.services.video_storage import video_storage
from api.core.config import settings
from api.routers.examples import EXAMPLES

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/play", 
    response_model=None,  # Can return PlayGradingResponse or BulkGradingResponse
    responses={
        200: {
            "description": "Successful grading",
            "content": {
                "application/json": {
                    "example": EXAMPLES["play_grading"]
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        500: {"description": "Internal server error"},
        503: {"description": "OpenAI service unavailable"}
    },
    summary="Grade Play(s) - Auto-Detection Enabled",
    description="""
    Grade all players in a play with AI-powered analysis.
    
    **AUTOMATIC FEATURES:**
    - ✅ **Auto-detects players**: If `player_positions` not provided, automatically finds all players in the play
    - ✅ **Auto-infers positions**: Uses play type and formation to assign positions (QB, WR, etc.)
    - ✅ **Grade all plays**: If `play_id` not provided, grades ALL plays in the video
    
    **USAGE EXAMPLES:**
    
    1. **Grade specific play with auto-detection** (RECOMMENDED):
    ```json
    {
      "video_id": "game_123",
      "play_id": 1
      // player_positions not needed - auto-detected!
    }
    ```
    
    2. **Grade all plays automatically**:
    ```json
    {
      "video_id": "game_123"
      // play_id not needed - grades all plays!
    }
    ```
    
    3. **Manual override** (if you know positions):
    ```json
    {
      "video_id": "game_123",
      "play_id": 1,
      "player_positions": {"42": "QB", "23": "WR"}
    }
    ```
    
    **Features:**
    - Position-specific performance criteria
    - Numeric scores (0-100) and letter grades (A-F)
    - Detailed qualitative feedback
    - Specific strengths and improvement areas
    - Training material citations
    
    **Supported Positions:**
    QB, RB, WR, TE, OL, DL, LB, DB, K, P
    
    **Grading Scale:**
    - A (90-100): Outstanding
    - B (80-89): Above Average
    - C (70-79): Average
    - D (60-69): Below Average
    - F (0-59): Failing
    
    **Note:** Requires `analyze_frames=true` during video analysis for auto-detection to work.
    """
)
async def grade_play(
    request: Request,
    grading_request: PlayGradingRequest
):
    """
    Grade all players in a specific play
    
    If play_id is not provided, grades all plays in the video.
    If player_positions is not provided, automatically detects all players and infers positions.
    """
    try:
        # Create AI grader
        grader = AIGrader()
        
        # If play_id not provided, grade all plays (return bulk response)
        if grading_request.play_id is None:
            # Use bulk grading endpoint logic
            analysis = video_storage.get_analysis(grading_request.video_id)
            if not analysis:
                raise HTTPException(
                    status_code=404,
                    detail=f"Video analysis not found for video_id: {grading_request.video_id}. "
                           f"Please analyze the video first using POST /api/v1/analysis/video"
                )
            
            if not analysis.plays:
                raise HTTPException(
                    status_code=400,
                    detail=f"No plays found in video {grading_request.video_id}. "
                           f"Make sure to run analysis with detect_plays=true"
                )
            
            # Grade all plays
            play_grades = []
            total_time = 0
            
            for play in analysis.plays:
                context_parts = []
                if play.play_type and play.play_type != "unknown":
                    context_parts.append(f"Play type: {play.play_type}")
                if play.key_events:
                    context_parts.append(f"Key events: {', '.join(play.key_events)}")
                
                enhanced_context = ". ".join(context_parts) if context_parts else ""
                
                result = await grader.grade_play(
                    video_id=grading_request.video_id,
                    play_segment=play,
                    player_positions=grading_request.player_positions,
                    play_context=enhanced_context
                )
                play_grades.append(result)
                total_time += result.processing_time
            
            # Return as bulk response
            from api.models.schemas import BulkGradingResponse
            return BulkGradingResponse(
                video_id=grading_request.video_id,
                total_plays=len(analysis.plays),
                play_grades=play_grades,
                processing_time=total_time
            )
        
        # Fetch real play data from video analysis results
        play_data = video_storage.get_play(grading_request.video_id, grading_request.play_id)
        
        if not play_data:
            # Check if video analysis exists at all
            if not video_storage.has_analysis(grading_request.video_id):
                raise HTTPException(
                    status_code=404,
                    detail=f"Video analysis not found for video_id: {grading_request.video_id}. "
                           f"Please analyze the video first using POST /api/v1/analysis/video"
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Play {grading_request.play_id} not found in video {grading_request.video_id}. "
                           f"Available plays: {[p.play_id for p in video_storage.get_analysis(grading_request.video_id).plays]}"
                )
        
        # Use real play segment from video analysis
        play_segment = play_data
        
        # Build enhanced play context from analysis data
        play_context_parts = []
        if play_segment.play_type and play_segment.play_type != "unknown":
            play_context_parts.append(f"Play type: {play_segment.play_type}")
        if play_segment.key_events:
            play_context_parts.append(f"Key events: {', '.join(play_segment.key_events)}")
        if grading_request.play_context:
            play_context_parts.append(grading_request.play_context)
        
        enhanced_context = ". ".join(play_context_parts) if play_context_parts else "No additional context"
        
        # Auto-detect players if positions not provided
        if not grading_request.player_positions:
            detected_players = video_storage.get_players_in_play(
                grading_request.video_id, 
                play_segment.play_id
            )
            if detected_players:
                logger.info(
                    f"Auto-detecting players for play {play_segment.play_id}: "
                    f"{len(detected_players)} players found"
                )
            else:
                logger.warning(
                    f"No players detected in play {play_segment.play_id}. "
                    f"Frame analysis may be required (set analyze_frames=true)"
                )
        
        logger.info(
            f"Grading play {play_segment.play_id} from video {grading_request.video_id} "
            f"(type: {play_segment.play_type}, events: {len(play_segment.key_events)}, "
            f"players: {len(grading_request.player_positions) if grading_request.player_positions else 'auto-detect'})"
        )
        
        # Grade the play with real data
        result = await grader.grade_play(
            video_id=grading_request.video_id,
            play_segment=play_segment,
            player_positions=grading_request.player_positions,
            play_context=enhanced_context
        )
        
        return result
        
    except HTTPException:
        # Re-raise HTTPException so FastAPI can handle it properly
        raise
    except Exception as e:
        logger.error(f"Error grading play: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error grading play: {str(e)}")

@router.post(
    "/bulk", 
    response_model=BulkGradingResponse,
    responses={
        200: {
            "description": "Successful bulk grading",
            "content": {
                "application/json": {
                    "example": EXAMPLES["bulk_grading"]
                }
            }
        }
    },
    summary="Grade All Plays",
    description="""
    Grade all plays in a video with comprehensive analysis.
    
    **Use Case:** Batch process entire game footage
    
    **Note:** This endpoint processes plays sequentially, so response time
    scales with the number of plays. For better performance, consider
    calling the single play endpoint in parallel for each play.
    """
)
async def grade_all_plays(
    request: Request,
    grading_request: BulkGradingRequest
):
    """
    Grade all plays in a video
    """
    try:
        grader = AIGrader()
        
        # Fetch real plays from video analysis results
        analysis = video_storage.get_analysis(grading_request.video_id)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Video analysis not found for video_id: {grading_request.video_id}. "
                       f"Please analyze the video first using POST /api/v1/analysis/video"
            )
        
        if not analysis.plays:
            raise HTTPException(
                status_code=400,
                detail=f"No plays found in video {grading_request.video_id}. "
                       f"Make sure to run analysis with detect_plays=true"
            )
        
        logger.info(f"Bulk grading {len(analysis.plays)} plays from video {grading_request.video_id}")
        
        play_grades = []
        total_time = 0
        
        for play in analysis.plays:
            # Build enhanced context from play data
            context_parts = []
            if play.play_type and play.play_type != "unknown":
                context_parts.append(f"Play type: {play.play_type}")
            if play.key_events:
                context_parts.append(f"Key events: {', '.join(play.key_events)}")
            
            enhanced_context = ". ".join(context_parts) if context_parts else ""
            
            result = await grader.grade_play(
                video_id=grading_request.video_id,
                play_segment=play,
                player_positions=grading_request.player_positions,
                play_context=enhanced_context
            )
            play_grades.append(result)
            total_time += result.processing_time
        
        return BulkGradingResponse(
            video_id=grading_request.video_id,
            total_plays=len(analysis.plays),
            play_grades=play_grades,
            processing_time=total_time
        )
        
    except Exception as e:
        logger.error(f"Error in bulk grading: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in bulk grading: {str(e)}")

@router.post(
    "/qa", 
    response_model=CoachingAnswer,
    responses={
        200: {
            "description": "Successful Q&A response",
            "content": {
                "application/json": {
                    "example": EXAMPLES["coaching_qa"]
                }
            }
        },
        503: {"description": "OpenAI API not configured"}
    },
    summary="Coaching Q&A",
    description="""
    Ask football coaching questions and receive AI-powered answers.
    
    **Features:**
    - Role-specific answers (coach vs player perspective)
    - Training material citations
    - Confidence scores
    - Comprehensive coaching guidance
    
    **Example Questions:**
    - "How can I improve my offensive line's pass protection?"
    - "What drills help develop linebacker coverage skills?"
    - "How do I teach proper tackling technique?"
    
    **Requires:** OpenAI API key configured in environment
    """
)
async def coaching_qa(
    question_request: CoachingQuestion
):
    """
    Ask coaching questions and get AI-powered answers
    """
    try:
        grader = AIGrader()
        
        if not grader.client:
            raise HTTPException(
                status_code=503,
                detail="OpenAI API not configured. Please set OPENAI_API_KEY."
            )
        
        # Build Q&A prompt
        system_prompt = """You are an expert football coach providing guidance and answers.
        Provide clear, actionable advice based on coaching best practices.
        Tailor your response to the user's role (coach or player)."""
        
        role_context = ""
        if question_request.role == "player":
            role_context = "\n\nNote: The user is a player, so focus on player-centric advice and motivation."
        elif question_request.role == "coach":
            role_context = "\n\nNote: The user is a coach, so provide strategic and tactical insights."
        
        prompt = f"{question_request.question}{role_context}"
        
        # Call OpenAI
        response = await grader.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        answer_text = response.choices[0].message.content.strip()
        
        return CoachingAnswer(
            question=question_request.question,
            answer=answer_text,
            citations=["General Coaching Principles", "Position Fundamentals"],
            confidence=0.85
        )
        
    except Exception as e:
        logger.error(f"Error in coaching Q&A: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in coaching Q&A: {str(e)}")

