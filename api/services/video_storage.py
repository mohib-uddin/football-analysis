"""
Video analysis storage service - stores video analysis results in memory
In production, this would be replaced with a database
"""
import logging
from typing import Dict, Optional
from api.models.schemas import VideoAnalysisResponse

logger = logging.getLogger(__name__)

class VideoStorage:
    """In-memory storage for video analysis results"""
    
    def __init__(self):
        # Store video analysis results by video_id
        self._analysis_results: Dict[str, VideoAnalysisResponse] = {}
    
    def store_analysis(self, analysis_result: VideoAnalysisResponse):
        """Store video analysis results"""
        self._analysis_results[analysis_result.video_id] = analysis_result
        logger.info(f"Stored analysis results for video_id: {analysis_result.video_id}")
        logger.debug(f"Stored {len(analysis_result.plays)} plays for video {analysis_result.video_id}")
    
    def get_analysis(self, video_id: str) -> Optional[VideoAnalysisResponse]:
        """Retrieve video analysis results by video_id"""
        return self._analysis_results.get(video_id)
    
    def get_play(self, video_id: str, play_id: int) -> Optional[dict]:
        """Get a specific play from analysis results"""
        analysis = self.get_analysis(video_id)
        if not analysis:
            return None
        
        # Find play by play_id
        for play in analysis.plays:
            if play.play_id == play_id:
                return play
        
        return None
    
    def get_players_in_play(self, video_id: str, play_id: int) -> list:
        """Get all unique player IDs that appear in a play"""
        analysis = self.get_analysis(video_id)
        if not analysis:
            return []
        
        play = self.get_play(video_id, play_id)
        if not play or not analysis.frame_analyses:
            return []
        
        # Extract player IDs from frames within the play
        player_ids = set()
        for frame in analysis.frame_analyses:
            # Check if frame is within play timeframe
            if play.start_frame <= frame.frame_number <= play.end_frame:
                for obj in frame.detected_objects:
                    if obj.label == 'player' and obj.object_id != -1:
                        player_ids.add(obj.object_id)
        
        return sorted(list(player_ids))
    
    def has_analysis(self, video_id: str) -> bool:
        """Check if analysis exists for video_id"""
        return video_id in self._analysis_results
    
    def list_videos(self) -> list:
        """List all video_ids that have analysis results"""
        return list(self._analysis_results.keys())
    
    def delete_analysis(self, video_id: str) -> bool:
        """Delete analysis results for a video"""
        if video_id in self._analysis_results:
            del self._analysis_results[video_id]
            logger.info(f"Deleted analysis results for video_id: {video_id}")
            return True
        return False

# Global storage instance
video_storage = VideoStorage()

