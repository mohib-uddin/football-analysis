"""
Video analysis service - processes videos and extracts information
"""
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import time
import sys

# Optional imports for CV functionality
try:
    import cv2
    import numpy as np
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False
    cv2 = None
    np = None

from api.models.schemas import (
    DetectedObject, BoundingBox, FrameAnalysis, 
    PlaySegment, VideoAnalysisResponse
)
from api.core.config import settings

logger = logging.getLogger(__name__)

# Import color detection function from Bird's eye view
# Temporarily add path, import, then remove to avoid main.py discovery
birds_eye_view_path = str(Path(__file__).resolve().parent.parent.parent / "Bird's eye view")
path_added = False
if birds_eye_view_path not in sys.path:
    sys.path.insert(0, birds_eye_view_path)
    path_added = True

try:
    from elements.assets import detect_color
    COLOR_DETECTION_AVAILABLE = True
except ImportError:
    COLOR_DETECTION_AVAILABLE = False
    logger.warning("Color detection not available - install scikit-learn")
finally:
    # Remove path immediately to prevent main.py discovery
    if path_added and birds_eye_view_path in sys.path:
        sys.path.remove(birds_eye_view_path)

class VideoAnalyzer:
    """Analyzes football videos"""
    
    def __init__(self, model_loader):
        self.model_loader = model_loader
        self.detector = model_loader.get_detector()
        self.tracker = model_loader.get_tracker()
        self.perspective_transform = model_loader.get_perspective_transform()
    
    async def analyze_video(
        self, 
        video_path: str,
        analyze_frames: bool = True,
        detect_plays: bool = True,
        track_players: bool = True
    ) -> VideoAnalysisResponse:
        """
        Analyze a video file
        
        Args:
            video_path: Path to video file
            analyze_frames: Whether to analyze individual frames
            detect_plays: Whether to segment plays
            track_players: Whether to track player movements
        
        Returns:
            VideoAnalysisResponse with analysis results
        """
        if not CV_AVAILABLE:
            raise ValueError("OpenCV is not installed. Install with: py -m pip install opencv-python")
        
        start_time = time.time()
        
        logger.info(f"Starting video analysis: {video_path}")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Video properties: {total_frames} frames, {fps} fps, {duration:.2f}s")
        
        # GPU optimization: Skip frames if analyzing every frame is too slow
        # Process every Nth frame for play segmentation (faster), all frames if analyze_frames=True
        frame_skip = 5 if not analyze_frames else 1  # Skip frames for segmentation-only mode
        
        # Check if GPU is available for logging
        try:
            import torch
            if torch.cuda.is_available():
                logger.info("🚀 Using GPU acceleration for faster processing")
            else:
                logger.warning("⚠️  Using CPU - processing will be slower. Consider installing GPU-enabled PyTorch.")
                # Increase frame skip on CPU for faster processing
                if not analyze_frames:
                    frame_skip = 10
        except:
            pass
        
        # Analyze frames
        frame_analyses = []
        frame_data_for_segmentation = []
        
        # Track player colors across frames for team identification
        player_colors = {}  # {track_id: color}
        
        frame_num = 0
        processed_frames = 0
        last_log_time = time.time()
        
        logger.info(f"Processing video (frame skip: {frame_skip} for segmentation)...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Skip frames for faster processing (only if not doing full frame analysis)
            if frame_num % frame_skip != 0 and not analyze_frames:
                frame_num += 1
                continue
            
            # Progress logging every 5 seconds
            current_time = time.time()
            if current_time - last_log_time >= 5.0:
                progress = (frame_num / total_frames) * 100 if total_frames > 0 else 0
                logger.info(f"Processing: {frame_num}/{total_frames} frames ({progress:.1f}%)")
                last_log_time = current_time
            
            timestamp = frame_num / fps
            
            # Detect objects in frame
            tracking_outputs = None
            if self.detector:
            detections = self.detector.detect(frame)
            
                # Track players - this returns track_id for each player
                if track_players and self.tracker:
                    tracking_outputs = self.tracker.detection_to_deepsort(detections, frame)
                    
                # Create a mapping from detection index to tracking ID
                track_id_map = {}
                if tracking_outputs is not None and len(tracking_outputs) > 0:
                    # tracking_outputs format: [x1, y1, x2, y2, track_id]
                    for track in tracking_outputs:
                        if len(track) >= 5:
                            track_bbox = track[:4]
                            track_id = int(track[4])
                            # Match to detection by bbox overlap
                            track_id_map[tuple(track_bbox)] = track_id
                
                # Convert to schema objects with tracking IDs and team colors
                detected_objects = []
                player_positions = []  # For formation detection
                
                for det in detections:
                    bbox_coords = [det['bbox'][0][0], det['bbox'][0][1], det['bbox'][1][0], det['bbox'][1][1]]
                    bbox = BoundingBox(
                        x_min=bbox_coords[0],
                        y_min=bbox_coords[1],
                        x_max=bbox_coords[2],
                        y_max=bbox_coords[3]
                            )
                            
                    # Find matching track_id
                    object_id = -1
                    if track_players and tracking_outputs is not None and len(tracking_outputs) > 0:
                        # Find best matching track by bbox overlap
                        for track in tracking_outputs:
                            if len(track) >= 5:
                                track_bbox = track[:4]
                                # Check if this is the same detection (similar bbox)
                                if self._bbox_overlap(bbox_coords, track_bbox) > 0.5:
                                    object_id = int(track[4])
                                    break
                    
                    # Detect team color for players
                    team_color = None
                    if det['label'] == 'player' and COLOR_DETECTION_AVAILABLE:
                        try:
                            # Extract player region from frame
                            y1, y2 = max(0, bbox_coords[1]), min(frame.shape[0], bbox_coords[3])
                            x1, x2 = max(0, bbox_coords[0]), min(frame.shape[1], bbox_coords[2])
                            
                            if x2 > x1 and y2 > y1:
                                player_region = frame[y1:y2, x1:x2]
                                if player_region.size > 0:
                                    color_bgr = detect_color(player_region)
                                    # Convert BGR to color name
                                    team_color = self._color_to_name(color_bgr)
                                    
                                    # Store color for this player (track consistency)
                                    if object_id != -1:
                                        if object_id not in player_colors:
                                            player_colors[object_id] = team_color
                                        else:
                                            # Use most common color for this player
                                            team_color = player_colors[object_id]
                except Exception as e:
                            logger.debug(f"Color detection failed for player: {e}")
                
                obj = DetectedObject(
                        object_id=object_id,
                    label=det['label'],
                    bbox=bbox,
                    confidence=float(det['score']),
                        team_color=team_color
                )
                detected_objects.append(obj)
                    
                    # Collect player positions for formation detection
                    if det['label'] == 'player':
                        center_x = (bbox_coords[0] + bbox_coords[2]) / 2
                        center_y = (bbox_coords[1] + bbox_coords[3]) / 2
                        player_positions.append({
                            'x': center_x,
                            'y': center_y,
                            'team_color': team_color,
                            'track_id': object_id
                        })
            
            # Count players and check for ball
            player_count = sum(1 for obj in detected_objects if obj.label == 'player')
            ball_detected = any(obj.label == 'ball' for obj in detected_objects)
                ball_position = self._get_ball_position(detected_objects)
                
                # Detect formation
                formation = self._detect_formation(player_positions) if player_count >= 6 else None
            
            # Store frame analysis
            if analyze_frames:
                frame_analysis = FrameAnalysis(
                    frame_number=frame_num,
                    timestamp=timestamp,
                    detected_objects=detected_objects,
                    player_count=player_count,
                    ball_detected=ball_detected
                )
                frame_analyses.append(frame_analysis)
            
            # Store data for play segmentation
            frame_data_for_segmentation.append({
                'frame_num': frame_num,
                'timestamp': timestamp,
                'player_count': player_count,
                'ball_detected': ball_detected,
                    'ball_position': ball_position,
                    'formation': formation,
                    'detected_objects': detected_objects  # For key events detection
            })
            
            frame_num += 1
            processed_frames += 1
            
            # Log progress
            if frame_num % 100 == 0:
                logger.info(f"Processed {frame_num}/{total_frames} frames")
        
        cap.release()
        
        # Segment plays if requested
        plays = []
        if detect_plays:
            plays = self._segment_plays(frame_data_for_segmentation, fps)
            logger.info(f"Detected {len(plays)} plays")
        
        processing_time = time.time() - start_time
        
        # Generate unique video ID
        video_id = Path(video_path).stem + "_" + str(int(time.time()))
        
        return VideoAnalysisResponse(
            video_id=video_id,
            duration=duration,
            total_frames=total_frames,
            fps=fps,
            plays=plays,
            frame_analyses=frame_analyses if analyze_frames else None,
            processing_time=processing_time
        )
    
    def _bbox_overlap(self, bbox1, bbox2) -> float:
        """Calculate Intersection over Union (IoU) between two bounding boxes"""
        if not CV_AVAILABLE:
            return 0.0
        
        # bbox format: [x1, y1, x2, y2]
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        # Calculate intersection area
        x_min = max(x1_min, x2_min)
        y_min = max(y1_min, y2_min)
        x_max = min(x1_max, x2_max)
        y_max = min(y1_max, y2_max)
        
        if x_max < x_min or y_max < y_min:
            return 0.0
        
        intersection = (x_max - x_min) * (y_max - y_min)
        
        # Calculate union area
        bbox1_area = (x1_max - x1_min) * (y1_max - y1_min)
        bbox2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union = bbox1_area + bbox2_area - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _color_to_name(self, color_bgr) -> str:
        """Convert BGR color to readable name"""
        # Color palette from assets.py
        color_map = {
            (0, 0, 128): 'blue',
            (0, 128, 0): 'green',
            (255, 0, 0): 'red',
            (0, 192, 192): 'cyan',
            (192, 0, 192): 'magenta',
            (192, 192, 0): 'yellow',
            (0, 0, 0): 'black',
            (255, 255, 255): 'white',
            (128, 128, 128): 'gray'
        }
        
        # Find closest color
        min_dist = float('inf')
        closest_name = 'unknown'
        
        for bgr, name in color_map.items():
            dist = sum((a - b) ** 2 for a, b in zip(color_bgr, bgr)) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest_name = name
        
        return closest_name
    
    def _detect_formation(self, player_positions: List[Dict]) -> Optional[str]:
        """Detect offensive/defensive formation based on player positioning"""
        if not CV_AVAILABLE or len(player_positions) < 6:
            return None
        
        # Separate by team (if colors detected)
        teams = {}
        for player in player_positions:
            color = player.get('team_color', 'unknown')
            if color not in teams:
                teams[color] = []
            teams[color].append(player)
        
        # Get the two main teams (ignore "unknown" if possible)
        team_colors = [k for k in teams.keys() if k != 'unknown']
        if len(team_colors) < 2 and 'unknown' in teams:
            team_colors.append('unknown')
        
        if len(team_colors) < 2:
            return "unknown formation"
        
        # Analyze formation for each team
        formations = []
        for color in team_colors[:2]:
            team_players = teams[color]
            if len(team_players) < 3:
                continue
            
            # Sort players by y-coordinate (front to back)
            sorted_players = sorted(team_players, key=lambda p: p['y'])
            
            # Count players in each "line" (divide into thirds)
            y_positions = [p['y'] for p in sorted_players]
            min_y, max_y = min(y_positions), max(y_positions)
            third = (max_y - min_y) / 3 if max_y > min_y else 1
            
            front_line = sum(1 for y in y_positions if y < min_y + third)
            mid_line = sum(1 for y in y_positions if min_y + third <= y < min_y + 2 * third)
            back_line = sum(1 for y in y_positions if y >= min_y + 2 * third)
            
            # Determine formation type
            if len(team_players) >= 7:  # Likely offensive/defensive line
                if front_line >= 5:
                    formations.append(f"{color}: offensive line")
                elif front_line >= 3 and mid_line >= 3:
                    formations.append(f"{color}: 4-3 defense")
                elif back_line >= 4:
                    formations.append(f"{color}: prevent defense")
                else:
                    formations.append(f"{color}: balanced")
            else:
                formations.append(f"{color}: {len(team_players)} players")
        
        return ", ".join(formations) if formations else "unknown formation"
    
    def _get_ball_position(self, detected_objects: List[DetectedObject]) -> Optional[Tuple[float, float]]:
        """Get ball position from detected objects"""
        if not CV_AVAILABLE:
            return None
        for obj in detected_objects:
            if obj.label == 'ball':
                # Return center of bounding box
                center_x = (obj.bbox.x_min + obj.bbox.x_max) / 2
                center_y = (obj.bbox.y_min + obj.bbox.y_max) / 2
                return (center_x, center_y)
        return None
    
    def _segment_plays(self, frame_data: List[Dict], fps: float) -> List[PlaySegment]:
        """
        Segment video into individual plays
        
        Uses heuristics:
        - Play starts when players cluster (formation)
        - Play ends when ball stops moving or players disperse
        - Minimum and maximum play durations
        - Detects play type (run, pass) and key events
        """
        plays = []
        play_id = 1
        
        if not frame_data:
            return plays
        
        in_play = False
        play_start_frame = 0
        play_start_time = 0
        play_start_ball_pos = None
        last_ball_pos = None
        frames_without_movement = 0
        play_frames = []  # Store frames during the play for analysis
        
        for i, frame_info in enumerate(frame_data):
            frame_num = frame_info['frame_num']
            timestamp = frame_info['timestamp']
            player_count = frame_info['player_count']
            ball_detected = frame_info['ball_detected']
            ball_pos = frame_info['ball_position']
            formation = frame_info.get('formation')
            
            # Check for play start
            if not in_play and player_count >= 6:  # Minimum players to start a play
                in_play = True
                play_start_frame = frame_num
                play_start_time = timestamp
                play_start_ball_pos = ball_pos
                last_ball_pos = ball_pos
                frames_without_movement = 0
                play_frames = [frame_info]
                logger.debug(f"Play {play_id} started at frame {frame_num}")
            
            # Check for play end
            elif in_play:
                play_frames.append(frame_info)
                
                # Check ball movement
                ball_moved_significantly = False
                if ball_pos and last_ball_pos and CV_AVAILABLE:
                    distance = np.sqrt(
                        (ball_pos[0] - last_ball_pos[0])**2 + 
                        (ball_pos[1] - last_ball_pos[1])**2
                    )
                    if distance < settings.BALL_MOVEMENT_THRESHOLD:
                        frames_without_movement += 1
                    else:
                        frames_without_movement = 0
                        ball_moved_significantly = True
                    last_ball_pos = ball_pos
                
                # End play if:
                # 1. Ball hasn't moved for a while
                # 2. Players dispersed
                # 3. Maximum play duration reached
                duration = timestamp - play_start_time
                
                should_end_play = (
                    frames_without_movement > fps * 2 or  # Ball stationary for 2 seconds
                    player_count < 4 or  # Players dispersed
                    duration > settings.MAX_PLAY_DURATION
                )
                
                if should_end_play and duration >= settings.MIN_PLAY_DURATION:
                    # Analyze the play to determine type and key events
                    play_type, key_events = self._analyze_play_type_and_events(
                        play_frames, fps, play_start_ball_pos
                    )
                    
                    play = PlaySegment(
                        play_id=play_id,
                        start_time=play_start_time,
                        end_time=timestamp,
                        duration=duration,
                        start_frame=play_start_frame,
                        end_frame=frame_num,
                        player_count=player_count,
                        play_type=play_type,
                        key_events=key_events
                    )
                    plays.append(play)
                    logger.debug(f"Play {play_id} ended at frame {frame_num}, type: {play_type}, duration: {duration:.2f}s")
                    
                    in_play = False
                    play_id += 1
                    frames_without_movement = 0
                    play_frames = []
        
        return plays
    
    def _analyze_play_type_and_events(
        self, 
        play_frames: List[Dict], 
        fps: float,
        start_ball_pos: Optional[Tuple[float, float]]
    ) -> Tuple[str, List[str]]:
        """
        Analyze play frames to determine play type and detect key events
        
        Returns:
            (play_type, key_events) where play_type is "run", "pass", "unknown"
            and key_events is a list of detected events
        """
        if not CV_AVAILABLE or not play_frames:
            return ("unknown", [])
        
        key_events = []
        play_type = "unknown"
        
        # Analyze ball movement patterns
        ball_positions = []
        ball_heights = []  # Y-coordinate (vertical movement suggests pass)
        
        for frame in play_frames:
            if frame.get('ball_position'):
                ball_positions.append(frame['ball_position'])
                ball_heights.append(frame['ball_position'][1])
        
        if len(ball_positions) >= 3:
            # Calculate total ball displacement
            start_pos = ball_positions[0]
            end_pos = ball_positions[-1]
            total_distance = np.sqrt(
                (end_pos[0] - start_pos[0])**2 + 
                (end_pos[1] - start_pos[1])**2
            )
            
            # Calculate vertical movement
            max_height = min(ball_heights) if ball_heights else 0  # Lower y = higher on screen
            min_height = max(ball_heights) if ball_heights else 0
            vertical_movement = abs(max_height - min_height)
            
            # Detect play type based on ball movement
            if vertical_movement > 100:  # Significant vertical movement suggests pass
                play_type = "pass"
                key_events.append("pass")
            elif total_distance > 200:  # Significant horizontal movement
                play_type = "run"
                key_events.append("handoff")
            else:
                play_type = "short play"
        
        # Detect key events
        # 1. Play start (snap)
        if play_frames and play_frames[0].get('player_count', 0) >= 6:
            key_events.insert(0, "snap")
        
        # 2. Detect if players are clustering (tackle/pile)
        for i, frame in enumerate(play_frames):
            if i < len(play_frames) - 1:
                objects = frame.get('detected_objects', [])
                players = [obj for obj in objects if obj.label == 'player']
                
                # Check for player clustering (potential tackle)
                if len(players) >= 4:
                    # Calculate average distance between players
                    positions = []
                    for player in players:
                        x = (player.bbox.x_min + player.bbox.x_max) / 2
                        y = (player.bbox.y_min + player.bbox.y_max) / 2
                        positions.append((x, y))
                    
                    if len(positions) >= 4:
                        # Check if multiple players are close together
                        close_pairs = 0
                        for j in range(len(positions)):
                            for k in range(j + 1, len(positions)):
                                dist = np.sqrt(
                                    (positions[j][0] - positions[k][0])**2 + 
                                    (positions[j][1] - positions[k][1])**2
                                )
                                if dist < 100:  # Pixels threshold for "close"
                                    close_pairs += 1
                        
                        if close_pairs >= 3 and "tackle" not in key_events:
                            key_events.append("tackle")
        
        # 3. Add formation info if available
        if play_frames and play_frames[0].get('formation'):
            formation = play_frames[0]['formation']
            if formation and formation != "unknown formation":
                key_events.append(f"formation: {formation}")
        
        return (play_type, key_events)

