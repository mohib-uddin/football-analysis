"""
AI Grading service - grades player performance using OpenAI
"""
import openai
from openai import AsyncOpenAI
import logging
from typing import List, Dict, Optional
import time
import json

from api.models.schemas import (
    PlayerGrade, GradingCriteria, PlayGradingResponse, 
    PlayerPosition, PlaySegment
)
from api.core.config import settings

logger = logging.getLogger(__name__)

class AIGrader:
    """Grades player performance using AI"""
    
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OpenAI API key not provided - grading will use mock data")
    
    async def grade_play(
        self,
        video_id: str,
        play_segment: PlaySegment,
        player_positions: Optional[Dict[int, str]] = None,
        play_context: str = ""
    ) -> PlayGradingResponse:
        """
        Grade all players in a play
        
        Args:
            video_id: Video identifier
            play_segment: The play to grade
            player_positions: Optional mapping of player_id to position. 
                            If None, attempts to infer positions or uses "UNKNOWN"
            play_context: Additional context about the play
        
        Returns:
            PlayGradingResponse with grades for each player
        """
        start_time = time.time()
        
        logger.info(f"Grading play {play_segment.play_id} in video {video_id}")
        
        # If player_positions not provided, get all players from play
        if player_positions is None:
            from api.services.video_storage import video_storage
            detected_player_ids = video_storage.get_players_in_play(video_id, play_segment.play_id)
            if detected_player_ids:
                # Infer positions based on formation/play type (basic heuristic)
                player_positions = self._infer_positions(
                    detected_player_ids, 
                    play_segment,
                    video_id
                )
                logger.info(f"Auto-detected {len(player_positions)} players in play {play_segment.play_id}")
            else:
                logger.warning(f"No players detected in play {play_segment.play_id}, using default")
                player_positions = {}
        
        # Batch grade all players in ONE API call instead of N calls
        if self.client and player_positions:
            try:
                # Extract relevant video analysis data
                video_data = self._extract_play_data(video_id, play_segment)
                
                # Grade all players in one API call
                player_grades = await self._batch_grade_players(
                    player_positions=player_positions,
                    play_segment=play_segment,
                    play_context=play_context,
                    video_data=video_data
                )
                
                # Generate play summary from batch response
                play_summary = self._generate_summary_from_grades(play_segment, player_grades)
            except Exception as e:
                logger.error(f"Error in batch grading: {e}, falling back to individual grading")
                # Fallback to individual grading if batch fails
                player_grades = []
                for player_id, position in player_positions.items():
                    try:
                        grade = await self._grade_player(
                            player_id=player_id,
                            position=position,
                            play_segment=play_segment,
                            play_context=play_context
                        )
                        player_grades.append(grade)
                    except Exception as e2:
                        logger.error(f"Error grading player {player_id}: {e2}")
                        player_grades.append(self._create_default_grade(player_id, position))
                play_summary = await self._generate_play_summary(play_segment, player_grades)
        else:
            # Mock grading or no OpenAI
            player_grades = []
            for player_id, position in player_positions.items():
                grade = self._mock_grade_player(player_id, position, settings.GRADING_CRITERIA.get(position, []))
                player_grades.append(grade)
            play_summary = f"Play {play_segment.play_id}: {play_segment.player_count} players, {play_segment.duration:.2f}s duration."
        
        processing_time = time.time() - start_time
        
        return PlayGradingResponse(
            video_id=video_id,
            play_id=play_segment.play_id,
            player_grades=player_grades,
            play_summary=play_summary,
            processing_time=processing_time
        )
    
    def _infer_positions(
        self, 
        player_ids: List[int], 
        play_segment: PlaySegment,
        video_id: str
    ) -> Dict[int, str]:
        """
        Infer player positions based on play type and formation
        This is a basic heuristic - in production, use roster data or manual assignment
        """
        # Basic position inference based on play type
        positions = {}
        
        # Common positions distribution
        # For a typical play, assume: 1 QB, 1-2 RB, 2-3 WR, 1 TE, 5 OL (offensive)
        # Or: 4 DL, 3 LB, 4 DB (defensive)
        
        if play_segment.play_type == "pass":
            # Offensive play
            position_order = ["QB", "RB", "WR", "WR", "TE", "OL", "OL", "OL", "OL", "OL", "WR"]
            # Fill remaining with generic offensive positions (OL or DB for extra players)
            for i, player_id in enumerate(player_ids[:len(position_order)]):
                positions[player_id] = position_order[i]
            # For extra players, use OL (most common offensive position)
            for player_id in player_ids[len(position_order):]:
                positions[player_id] = "OL"
        elif play_segment.play_type == "run":
            # Offensive play
            position_order = ["QB", "RB", "RB", "OL", "OL", "OL", "OL", "OL", "WR", "TE"]
            for i, player_id in enumerate(player_ids[:len(position_order)]):
                positions[player_id] = position_order[i]
            # For extra players, use OL
            for player_id in player_ids[len(position_order):]:
                positions[player_id] = "OL"
        else:
            # Unknown or defensive play - use generic defensive positions
            position_order = ["DL", "DL", "DL", "DL", "LB", "LB", "LB", "DB", "DB", "DB", "DB"]
            for i, player_id in enumerate(player_ids[:len(position_order)]):
                positions[player_id] = position_order[i]
            # For extra players, use DB (most common defensive position)
            for player_id in player_ids[len(position_order):]:
                positions[player_id] = "DB"
        
        return positions
    
    async def _grade_player(
        self,
        player_id: int,
        position: str,
        play_segment: PlaySegment,
        play_context: str
    ) -> PlayerGrade:
        """Grade a single player"""
        
        # Get position-specific criteria
        criteria = settings.GRADING_CRITERIA.get(position, [])
        
        if self.client:
            # Use OpenAI for grading
            return await self._ai_grade_player(player_id, position, play_segment, play_context, criteria)
        else:
            # Use mock grading
            return self._mock_grade_player(player_id, position, criteria)
    
    async def _ai_grade_player(
        self,
        player_id: int,
        position: str,
        play_segment: PlaySegment,
        play_context: str,
        criteria: List[str]
    ) -> PlayerGrade:
        """Grade player using OpenAI"""
        
        # Construct prompt
        prompt = self._build_grading_prompt(
            player_id=player_id,
            position=position,
            play_segment=play_segment,
            play_context=play_context,
            criteria=criteria
        )
        
        try:
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert football coach with decades of experience. 
                        You provide detailed, constructive player evaluations based on position-specific criteria.
                        Your feedback is specific, actionable, and balanced between strengths and areas for improvement."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Convert to PlayerGrade schema
            criteria_scores = [
                GradingCriteria(
                    criterion=c["criterion"],
                    score=c["score"],
                    feedback=c["feedback"],
                    examples=c.get("examples", [])
                )
                for c in result.get("criteria_scores", [])
            ]
            
            return PlayerGrade(
                player_id=player_id,
                position=PlayerPosition(position),
                overall_score=result.get("overall_score", 0),
                letter_grade=result.get("letter_grade", "F"),
                criteria_scores=criteria_scores,
                qualitative_feedback=result.get("qualitative_feedback", ""),
                strengths=result.get("strengths", []),
                areas_for_improvement=result.get("areas_for_improvement", []),
                training_citations=result.get("training_citations", [])
            )
            
        except Exception as e:
            logger.error(f"OpenAI grading error: {e}")
            return self._mock_grade_player(player_id, position, criteria)
    
    def _build_grading_prompt(
        self,
        player_id: int,
        position: str,
        play_segment: PlaySegment,
        play_context: str,
        criteria: List[str]
    ) -> str:
        """Build grading prompt for OpenAI"""
        
        prompt = f"""Grade Player #{player_id} (Position: {position}) for this play:

**Play Information:**
- Play ID: {play_segment.play_id}
- Duration: {play_segment.duration:.2f} seconds
- Start Time: {play_segment.start_time:.2f}s
- End Time: {play_segment.end_time:.2f}s
- Players Involved: {play_segment.player_count}
- Play Type: {play_segment.play_type or "Unknown"}

**Play Context:**
{play_context or "No additional context provided"}

**Grading Criteria for {position}:**
{', '.join(criteria)}

**Instructions:**
1. Grade the player on each criterion (0-100 scale)
2. Calculate an overall score (0-100)
3. Assign a letter grade (A+, A, A-, B+, B, B-, C+, C, C-, D, F)
4. Provide specific, constructive feedback
5. List 2-3 key strengths
6. List 2-3 areas for improvement
7. Reference relevant coaching principles

**Response Format (JSON):**
{{
    "overall_score": <number 0-100>,
    "letter_grade": "<A-F>",
    "criteria_scores": [
        {{
            "criterion": "<criterion name>",
            "score": <0-100>,
            "feedback": "<specific feedback>",
            "examples": ["<specific example from play>"]
        }}
    ],
    "qualitative_feedback": "<overall assessment>",
    "strengths": ["<strength 1>", "<strength 2>", ...],
    "areas_for_improvement": ["<area 1>", "<area 2>", ...],
    "training_citations": ["<coaching principle 1>", "<coaching principle 2>", ...]
}}
"""
        return prompt
    
    def _mock_grade_player(
        self,
        player_id: int,
        position: str,
        criteria: List[str]
    ) -> PlayerGrade:
        """Generate mock grade (for testing without OpenAI)"""
        
        import random
        
        overall_score = random.randint(65, 95)
        
        # Convert score to letter grade
        if overall_score >= 93:
            letter_grade = "A"
        elif overall_score >= 90:
            letter_grade = "A-"
        elif overall_score >= 87:
            letter_grade = "B+"
        elif overall_score >= 83:
            letter_grade = "B"
        elif overall_score >= 80:
            letter_grade = "B-"
        elif overall_score >= 77:
            letter_grade = "C+"
        elif overall_score >= 73:
            letter_grade = "C"
        elif overall_score >= 70:
            letter_grade = "C-"
        elif overall_score >= 60:
            letter_grade = "D"
        else:
            letter_grade = "F"
        
        criteria_scores = [
            GradingCriteria(
                criterion=c,
                score=random.randint(60, 100),
                feedback=f"Demonstrated {c} at a competent level with room for improvement.",
                examples=[f"Example of {c} from the play"]
            )
            for c in criteria[:5]  # Limit to 5 criteria
        ]
        
        return PlayerGrade(
            player_id=player_id,
            position=PlayerPosition(position),
            overall_score=overall_score,
            letter_grade=letter_grade,
            criteria_scores=criteria_scores,
            qualitative_feedback=f"Player #{player_id} showed solid performance in this play with good execution of fundamental techniques.",
            strengths=[
                "Strong technical execution",
                "Good awareness and positioning",
                "Consistent effort throughout the play"
            ],
            areas_for_improvement=[
                "Footwork could be more precise",
                "Decision-making speed can improve",
                "Communication with teammates"
            ],
            training_citations=[
                "Fundamental Techniques for " + position,
                "Position-Specific Drills",
                "Game Situation Analysis"
            ]
        )
    
    def _create_default_grade(self, player_id: int, position: str) -> PlayerGrade:
        """Create default grade on error"""
        return PlayerGrade(
            player_id=player_id,
            position=PlayerPosition(position),
            overall_score=0,
            letter_grade="N/A",
            criteria_scores=[],
            qualitative_feedback="Unable to grade this player due to processing error.",
            strengths=[],
            areas_for_improvement=[],
            training_citations=[]
        )
    
    async def _generate_play_summary(
        self,
        play_segment: PlaySegment,
        player_grades: List[PlayerGrade]
    ) -> str:
        """Generate overall summary for the play"""
        
        if not self.client:
            return f"Play {play_segment.play_id} involved {play_segment.player_count} players over {play_segment.duration:.2f} seconds."
        
        try:
            avg_score = sum(g.overall_score for g in player_grades) / len(player_grades) if player_grades else 0
            
            prompt = f"""Summarize this football play:

Play #{play_segment.play_id}
- Duration: {play_segment.duration:.2f}s
- Players: {play_segment.player_count}
- Average Grade: {avg_score:.1f}/100

Player Grades:
{self._format_grades_for_summary(player_grades)}

Provide a brief 2-3 sentence summary of the play's execution and key coaching points."""
            
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a football coach providing play summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating play summary: {e}")
            return f"Play {play_segment.play_id}: {play_segment.player_count} players, {play_segment.duration:.2f}s duration."
    
    def _format_grades_for_summary(self, player_grades: List[PlayerGrade]) -> str:
        """Format grades for summary prompt"""
        lines = []
        for grade in player_grades:
            lines.append(f"- Player #{grade.player_id} ({grade.position}): {grade.letter_grade} ({grade.overall_score})")
        return "\n".join(lines)
    
    def _extract_play_data(self, video_id: str, play_segment: PlaySegment) -> Dict:
        """Extract relevant video analysis data for the play"""
        from api.services.video_storage import video_storage
        
        analysis = video_storage.get_analysis(video_id)
        if not analysis or not analysis.frame_analyses:
            return {}
        
        # Get frames within play timeframe
        play_frames = [
            frame for frame in analysis.frame_analyses
            if play_segment.start_frame <= frame.frame_number <= play_segment.end_frame
        ]
        
        if not play_frames:
            return {}
        
        # Extract player trajectories (simplified - just presence per frame)
        player_trajectories = {}
        ball_positions = []
        
        for frame in play_frames:
            # Track ball positions
            ball_obj = next((obj for obj in frame.detected_objects if obj.label == 'ball'), None)
            if ball_obj:
                ball_positions.append({
                    'frame': frame.frame_number,
                    'timestamp': frame.timestamp,
                    'x': (ball_obj.bbox.x_min + ball_obj.bbox.x_max) / 2,
                    'y': (ball_obj.bbox.y_min + ball_obj.bbox.y_max) / 2
                })
            
            # Track player presence
            for obj in frame.detected_objects:
                if obj.label == 'player' and obj.object_id != -1:
                    if obj.object_id not in player_trajectories:
                        player_trajectories[obj.object_id] = []
                    player_trajectories[obj.object_id].append({
                        'frame': frame.frame_number,
                        'timestamp': frame.timestamp,
                        'team': obj.team_color or 'unknown'
                    })
        
        return {
            'total_frames': len(play_frames),
            'ball_positions': ball_positions[:10],  # Limit to first 10 for prompt size
            'player_frames': {pid: len(traj) for pid, traj in player_trajectories.items()},  # Just count
            'key_events': play_segment.key_events,
            'formation': getattr(play_segment, 'formation', None)
        }
    
    async def _batch_grade_players(
        self,
        player_positions: Dict[int, str],
        play_segment: PlaySegment,
        play_context: str,
        video_data: Dict
    ) -> List[PlayerGrade]:
        """Grade all players in ONE API call instead of N separate calls"""
        
        prompt = self._build_batch_grading_prompt(
            player_positions=player_positions,
            play_segment=play_segment,
            play_context=play_context,
            video_data=video_data
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert football coach. Grade all players in this play simultaneously.
                        Provide specific, constructive feedback based on position-specific criteria and the actual play data provided."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS * 2,  # More tokens for batch response
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Convert to PlayerGrade objects
            player_grades = []
            for player_data in result.get("player_grades", []):
                criteria_scores = [
                    GradingCriteria(
                        criterion=c.get("criterion", ""),
                        score=c.get("score", 0),
                        feedback=c.get("feedback", ""),
                        examples=c.get("examples", [])
                    )
                    for c in player_data.get("criteria_scores", [])
                ]
                
                player_grades.append(PlayerGrade(
                    player_id=player_data.get("player_id", 0),
                    position=PlayerPosition(player_data.get("position", "UNKNOWN")),
                    overall_score=player_data.get("overall_score", 0),
                    letter_grade=player_data.get("letter_grade", "F"),
                    criteria_scores=criteria_scores,
                    qualitative_feedback=player_data.get("qualitative_feedback", ""),
                    strengths=player_data.get("strengths", []),
                    areas_for_improvement=player_data.get("areas_for_improvement", []),
                    training_citations=player_data.get("training_citations", [])
                ))
            
            logger.info(f"Batch graded {len(player_grades)} players in 1 API call")
            return player_grades
            
        except Exception as e:
            logger.error(f"Batch grading error: {e}")
            raise
    
    def _build_batch_grading_prompt(
        self,
        player_positions: Dict[int, str],
        play_segment: PlaySegment,
        play_context: str,
        video_data: Dict
    ) -> str:
        """Build efficient batch grading prompt with only relevant data"""
        
        # Build player list
        players_info = []
        for player_id, position in player_positions.items():
            criteria = settings.GRADING_CRITERIA.get(position, [])
            players_info.append(f"- Player #{player_id} ({position}): Grade on {', '.join(criteria[:3])}")
        
        # Include only relevant video data
        video_summary = []
        if video_data.get('key_events'):
            video_summary.append(f"Key Events: {', '.join(video_data['key_events'])}")
        if video_data.get('ball_positions'):
            video_summary.append(f"Ball detected in {len(video_data['ball_positions'])} frames")
        if video_data.get('player_frames'):
            video_summary.append(f"Player activity: {len(video_data['player_frames'])} tracked players")
        
        prompt = f"""Grade ALL players in this play in one response:

**Play Summary:**
- Play #{play_segment.play_id}
- Duration: {play_segment.duration:.2f}s ({play_segment.start_time:.1f}s - {play_segment.end_time:.1f}s)
- Play Type: {play_segment.play_type or 'Unknown'}
- Players: {len(player_positions)}

**Play Context:**
{play_context or 'Standard play execution'}

**Video Analysis Data:**
{chr(10).join(video_summary) if video_summary else 'Standard play execution'}

**Players to Grade:**
{chr(10).join(players_info)}

**Instructions:**
Grade each player based on their position-specific criteria. For each player, provide:
1. Overall score (0-100) and letter grade (A-F)
2. Scores for their position criteria
3. Specific feedback referencing the play data
4. 2-3 key strengths
5. 2-3 areas for improvement
6. Relevant coaching principles

**Response Format (JSON):**
{{
    "player_grades": [
        {{
            "player_id": <number>,
            "position": "<position>",
            "overall_score": <0-100>,
            "letter_grade": "<A-F>",
            "criteria_scores": [
                {{
                    "criterion": "<name>",
                    "score": <0-100>,
                    "feedback": "<specific feedback>",
                    "examples": ["<example>"]
                }}
            ],
            "qualitative_feedback": "<overall assessment>",
            "strengths": ["<strength 1>", "<strength 2>"],
            "areas_for_improvement": ["<area 1>", "<area 2>"],
            "training_citations": ["<principle 1>", "<principle 2>"]
        }}
    ]
}}
"""
        return prompt
    
    def _generate_summary_from_grades(self, play_segment: PlaySegment, player_grades: List[PlayerGrade]) -> str:
        """Generate play summary from grades without extra API call"""
        if not player_grades:
            return f"Play {play_segment.play_id}: No players graded."
        
        avg_score = sum(g.overall_score for g in player_grades) / len(player_grades)
        top_player = max(player_grades, key=lambda g: g.overall_score)
        
        summary = f"Play #{play_segment.play_id} ({play_segment.duration:.1f}s): "
        summary += f"Average grade {avg_score:.1f}/100 across {len(player_grades)} players. "
        summary += f"Top performer: Player #{top_player.player_id} ({top_player.position}) with {top_player.letter_grade} ({top_player.overall_score:.1f})."
        
        if play_segment.key_events:
            summary += f" Key events: {', '.join(play_segment.key_events[:3])}."
        
        return summary

