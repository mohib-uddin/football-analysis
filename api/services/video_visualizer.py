"""
Video visualization service - draws bounding boxes and analysis on video
"""
import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Optional
import time

from api.models.schemas import VideoAnalysisResponse, FrameAnalysis, DetectedObject
from api.services.video_storage import video_storage

logger = logging.getLogger(__name__)

class VideoVisualizer:
    """Visualizes video analysis with bounding boxes and labels"""
    
    def __init__(self):
        pass
    
    def visualize_video(
        self,
        video_id: str,
        original_video_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Create visualized video with bounding boxes and analysis
        
        Args:
            video_id: Video identifier
            original_video_path: Path to original video file
            output_path: Optional output path (defaults to original path + '_visualized.mp4')
        
        Returns:
            Path to output video file
        """
        # Get analysis results
        analysis = video_storage.get_analysis(video_id)
        if not analysis:
            raise ValueError(f"No analysis found for video_id: {video_id}")
        
        if not analysis.frame_analyses:
            raise ValueError(f"No frame analyses available for video_id: {video_id}. "
                           f"Re-run analysis with analyze_frames=true")
        
        # Set output path
        if output_path is None:
            original_path = Path(original_video_path)
            output_path = str(original_path.parent / f"{original_path.stem}_visualized.mp4")
        
        logger.info(f"Visualizing video: {original_video_path} -> {output_path}")
        
        # Open video
        cap = cv2.VideoCapture(original_video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {original_video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Create frame lookup for quick access
        frame_lookup = {frame.frame_number: frame for frame in analysis.frame_analyses}
        
        frame_num = 0
        processed = 0
        start_time = time.time()
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Get frame analysis if available
            frame_analysis = frame_lookup.get(frame_num)
            
            if frame_analysis:
                # Draw bounding boxes and labels
                frame = self._draw_analysis(frame, frame_analysis)
            
            # Add frame number and timestamp
            self._draw_frame_info(frame, frame_num, analysis.fps)
            
            out.write(frame)
            frame_num += 1
            processed += 1
            
            if processed % 100 == 0:
                logger.info(f"Processed {processed} frames...")
        
        cap.release()
        out.release()
        
        processing_time = time.time() - start_time
        logger.info(f"Visualization complete: {output_path} ({processing_time:.1f}s)")
        
        return output_path
    
    def _draw_analysis(self, frame: np.ndarray, frame_analysis: FrameAnalysis) -> np.ndarray:
        """Draw bounding boxes and labels on frame"""
        frame = frame.copy()
        
        for obj in frame_analysis.detected_objects:
            # Get bounding box coordinates
            x1, y1 = int(obj.bbox.x_min), int(obj.bbox.y_min)
            x2, y2 = int(obj.bbox.x_max), int(obj.bbox.y_max)
            
            # Choose color based on label and object_id
            if obj.label == 'ball':
                color = (102, 0, 102)  # Purple for ball
                label_text = "Ball"
            elif obj.label == 'player':
                # Use object_id for consistent color per player
                color = self._get_player_color(obj.object_id)
                if obj.object_id != -1:
                    label_text = f"P{obj.object_id}"
                else:
                    label_text = "Player"
                
                # Add team color if available
                if obj.team_color:
                    label_text += f" ({obj.team_color})"
            else:
                color = (128, 128, 128)  # Gray for other objects
                label_text = obj.label
            
            # Add confidence score
            if obj.confidence > 0:
                label_text += f" {obj.confidence:.1f}"
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label background
            label_size, _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            label_y = max(y1 - 10, label_size[1] + 10)
            cv2.rectangle(
                frame,
                (x1, label_y - label_size[1] - 5),
                (x1 + label_size[0] + 5, label_y + 5),
                color,
                -1
            )
            
            # Draw label text
            cv2.putText(
                frame,
                label_text,
                (x1 + 2, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
        
        return frame
    
    def _draw_frame_info(self, frame: np.ndarray, frame_num: int, fps: float):
        """Draw frame number and timestamp"""
        timestamp = frame_num / fps if fps > 0 else 0
        
        # Frame number
        cv2.putText(
            frame,
            f"Frame: {frame_num}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        # Timestamp
        cv2.putText(
            frame,
            f"Time: {timestamp:.2f}s",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
    
    def _get_player_color(self, player_id: int) -> tuple:
        """Get consistent color for player based on ID"""
        # Use a color palette that gives different colors for different IDs
        colors = [
            (0, 255, 0),      # Green
            (255, 0, 0),      # Blue
            (0, 0, 255),      # Red
            (255, 255, 0),    # Cyan
            (255, 0, 255),    # Magenta
            (0, 255, 255),    # Yellow
            (128, 0, 128),    # Purple
            (255, 165, 0),    # Orange
            (0, 128, 255),    # Light Blue
            (255, 192, 203),  # Pink
            (128, 128, 0),    # Olive
            (0, 128, 128),    # Teal
            (128, 0, 0),      # Maroon
            (0, 0, 128),      # Navy
        ]
        
        if player_id == -1:
            return (128, 128, 128)  # Gray for untracked
        
        return colors[player_id % len(colors)]

