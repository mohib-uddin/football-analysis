"""
Example responses for API documentation
"""
from api.models.schemas import (
    VideoAnalysisResponse, PlayGradingResponse, 
    PlayerGrade, GradingCriteria, PlaySegment,
    CoachingAnswer, HealthCheck
)
from datetime import datetime

# Example responses for Swagger docs

health_example = {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00",
    "models_loaded": False,
    "version": "1.0.0"
}

video_analysis_example = {
    "video_id": "game_footage_123_1705315800",
    "duration": 45.5,
    "total_frames": 1365,
    "fps": 30.0,
    "plays": [
        {
            "play_id": 1,
            "start_time": 5.0,
            "end_time": 15.5,
            "duration": 10.5,
            "start_frame": 150,
            "end_frame": 465,
            "player_count": 22,
            "play_type": "offensive",
            "key_events": ["snap", "pass"]
        },
        {
            "play_id": 2,
            "start_time": 20.0,
            "end_time": 28.0,
            "duration": 8.0,
            "start_frame": 600,
            "end_frame": 840,
            "player_count": 22,
            "play_type": "defensive",
            "key_events": ["tackle"]
        }
    ],
    "frame_analyses": None,
    "processing_time": 12.3
}

play_grading_example = {
    "video_id": "game_123",
    "play_id": 1,
    "player_grades": [
        {
            "player_id": 1,
            "position": "QB",
            "overall_score": 87.5,
            "letter_grade": "B+",
            "criteria_scores": [
                {
                    "criterion": "arm_strength",
                    "score": 90,
                    "feedback": "Excellent velocity on deep throws with good zip on intermediate routes.",
                    "examples": ["20-yard out route with tight spiral"]
                },
                {
                    "criterion": "accuracy",
                    "score": 85,
                    "feedback": "Generally accurate with slight high throws under pressure.",
                    "examples": ["2 of 3 completions in red zone"]
                },
                {
                    "criterion": "decision_making",
                    "score": 88,
                    "feedback": "Quick reads and proper progressions, one questionable throw into coverage.",
                    "examples": ["Checked down appropriately twice"]
                }
            ],
            "qualitative_feedback": "Strong performance with excellent arm strength and quick decision-making. Accuracy slightly suffered under pressure but overall showed good command of the offense. Demonstrated proper footwork and pocket presence throughout the play.",
            "strengths": [
                "Quick release and strong arm",
                "Good pre-snap reads",
                "Maintained composure under pressure"
            ],
            "areas_for_improvement": [
                "Footwork consistency when rolling out",
                "Touch on short passes",
                "Reading zone coverage post-snap"
            ],
            "training_citations": [
                "QB Fundamentals: Pocket Presence",
                "Decision Making Under Pressure",
                "Throwing Mechanics"
            ]
        },
        {
            "player_id": 2,
            "position": "WR",
            "overall_score": 82.0,
            "letter_grade": "B",
            "criteria_scores": [
                {
                    "criterion": "route_running",
                    "score": 85,
                    "feedback": "Sharp cuts with good separation technique.",
                    "examples": ["Clean break on slant route"]
                },
                {
                    "criterion": "hands",
                    "score": 80,
                    "feedback": "Reliable but one drop on contested catch.",
                    "examples": ["Caught ball in traffic"]
                }
            ],
            "qualitative_feedback": "Solid route running with good separation. Needs to improve concentration on contested catches.",
            "strengths": [
                "Explosive out of breaks",
                "Good body control"
            ],
            "areas_for_improvement": [
                "Concentration on tough catches",
                "Blocking on run plays"
            ],
            "training_citations": [
                "WR Route Techniques",
                "Catching Fundamentals"
            ]
        }
    ],
    "play_summary": "Well-executed offensive play with strong QB performance. Good ball distribution and receiver separation. Minor execution issues on blocking assignments. Overall grade indicates above-average team execution with specific areas for improvement in pass protection.",
    "processing_time": 3.5
}

bulk_grading_example = {
    "video_id": "game_123",
    "total_plays": 3,
    "play_grades": [
        play_grading_example,
        {
            "video_id": "game_123",
            "play_id": 2,
            "player_grades": [],
            "play_summary": "Defensive play with strong pressure.",
            "processing_time": 3.2
        },
        {
            "video_id": "game_123",
            "play_id": 3,
            "player_grades": [],
            "play_summary": "Special teams execution.",
            "processing_time": 2.8
        }
    ],
    "processing_time": 9.5
}

coaching_qa_example = {
    "question": "How can I improve my quarterback's decision-making under pressure?",
    "answer": "To improve quarterback decision-making under pressure, focus on these key areas:\n\n1. **Film Study**: Have your QB study defensive schemes daily to recognize pre-snap indicators of pressure. Understanding blitz packages helps anticipate where pressure comes from.\n\n2. **Hot Routes**: Install and drill hot routes extensively. Your QB needs automatic responses when pressure is coming - typically quick slants, hitches, or RB swing routes.\n\n3. **Pocket Presence Drills**: Use 'pocket awareness' drills where defenders rush at varied speeds. Teach your QB to feel pressure without looking, using subtle weight shifts and peripheral vision.\n\n4. **Clock Management**: Implement a '3-second rule' in practice. If the ball isn't out in 3 seconds, throw it away or scramble. This creates an internal clock.\n\n5. **Progression Simplification**: Under pressure, limit reads to 2-3 options max. Primary read, safety valve, scramble/throwaway.\n\n6. **Mental Reps**: Use virtual reality or film sessions where your QB calls out his decision on every pressured play before seeing the outcome.",
    "citations": [
        "QB Decision Making Under Duress - Chapter 5",
        "Pocket Presence Training Manual",
        "Film Study Techniques for Quarterbacks"
    ],
    "confidence": 0.92
}

# Export examples for use in router documentation
EXAMPLES = {
    "health": health_example,
    "video_analysis": video_analysis_example,
    "play_grading": play_grading_example,
    "bulk_grading": bulk_grading_example,
    "coaching_qa": coaching_qa_example
}

