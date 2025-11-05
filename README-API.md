# FieldCoachAI - Core AI API

FastAPI backend providing AI-powered football video analysis, play segmentation, and player grading.

## Features

### 🎯 Core Business Logic
- **Video Analysis**: Player detection, tracking, and movement analysis using YOLOv5 + DeepSORT
- **Play Segmentation**: Automatic identification and timestamping of individual plays
- **AI Grading**: Position-specific player performance grading with OpenAI GPT-4
- **Coaching Q&A**: AI-powered coaching assistance and question answering

### 📊 What This API Provides
- Player detection and tracking in game footage
- Automatic play segmentation with timestamps
- Detailed player grades (0-100 scale + letter grades)
- Position-specific performance criteria
- Qualitative feedback with strengths/weaknesses
- Training material citations
- Coaching Q&A with AI

### ❌ What's NOT Included (Yet)
- Authentication/Authorization
- Database integration
- Video upload to cloud storage
- User management
- Training library management
- Persistent data storage

*These will be handled by your separate NestJS backend*

## Installation

### Prerequisites
- Python 3.8+
- CUDA-capable GPU (recommended for video processing)
- OpenAI API key

### Setup

1. **Install dependencies**:
```bash
pip install -r requirements-api.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

3. **Download model weights** (optional for full CV features):
- Download YOLOv5 weights from [here](https://docs.google.com/uc?export=download&id=1EaBmCzl4xnuebfoQnxU1xQgNmBy7mWi2)
- Place in `Bird's eye view/weights/`

## Running the API

### Start the server:
```bash
cd api
python main.py
```

Or using uvicorn directly:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
```http
GET /api/v1/health
```
Check API status and model availability.

### Video Analysis

#### Upload Video
```http
POST /api/v1/analysis/video/upload
Content-Type: multipart/form-data

file: <video file>
```

#### Analyze Video
```http
POST /api/v1/analysis/video
Content-Type: application/json

{
  "video_path": "temp/game_footage.mp4",
  "analyze_frames": true,
  "detect_plays": true,
  "track_players": true
}
```

Response includes:
- Video metadata (duration, fps, frames)
- Detected plays with timestamps
- Frame-by-frame analysis (optional)
- Player tracking data

### AI Grading

#### Grade Single Play
```http
POST /api/v1/grading/play
Content-Type: application/json

{
  "video_id": "game_123",
  "play_id": 1,
  "player_positions": {
    "1": "QB",
    "2": "WR",
    "3": "RB"
  },
  "play_context": "3rd and 5, red zone"
}
```

Response includes:
- Overall score (0-100)
- Letter grade (A-F)
- Position-specific criteria scores
- Detailed qualitative feedback
- Strengths and areas for improvement
- Training material citations

#### Bulk Grade All Plays
```http
POST /api/v1/grading/bulk
Content-Type: application/json

{
  "video_id": "game_123",
  "player_positions": {
    "1": "QB",
    "2": "WR",
    "3": "RB"
  }
}
```

### Coaching Q&A
```http
POST /api/v1/grading/qa
Content-Type: application/json

{
  "question": "How can I improve my quarterback's pocket presence?",
  "role": "coach"
}
```

## Example Usage

### Python Client Example

```python
import requests

API_BASE = "http://localhost:8000/api/v1"

# 1. Upload video
with open("game_footage.mp4", "rb") as f:
    response = requests.post(
        f"{API_BASE}/analysis/video/upload",
        files={"file": f}
    )
    video_path = response.json()["video_path"]

# 2. Analyze video
response = requests.post(
    f"{API_BASE}/analysis/video",
    json={
        "video_path": video_path,
        "analyze_frames": False,  # Skip frame-by-frame for speed
        "detect_plays": True,
        "track_players": True
    }
)
analysis = response.json()
print(f"Detected {len(analysis['plays'])} plays")

# 3. Grade a play
response = requests.post(
    f"{API_BASE}/grading/play",
    json={
        "video_id": analysis["video_id"],
        "play_id": 1,
        "player_positions": {
            "1": "QB",
            "2": "WR",
            "3": "RB",
            "4": "OL",
            "5": "DL"
        },
        "play_context": "2nd and 10, midfield"
    }
)
grades = response.json()

for player_grade in grades["player_grades"]:
    print(f"Player #{player_grade['player_id']}: {player_grade['letter_grade']} ({player_grade['overall_score']})")
    print(f"Feedback: {player_grade['qualitative_feedback']}")
```

### cURL Example

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Grade a play
curl -X POST http://localhost:8000/api/v1/grading/play \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "test_video",
    "play_id": 1,
    "player_positions": {"1": "QB", "2": "WR"},
    "play_context": "3rd and 5"
  }'
```

## Configuration

Key settings in `.env`:

```bash
# OpenAI (Required for grading)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Play Segmentation Tuning
MIN_PLAY_DURATION=2.0      # Minimum play length (seconds)
MAX_PLAY_DURATION=30.0     # Maximum play length (seconds)
BALL_MOVEMENT_THRESHOLD=50.0  # Pixels for ball movement detection
```

## Architecture

```
api/
├── main.py                 # FastAPI application
├── core/
│   └── config.py          # Configuration management
├── models/
│   └── schemas.py         # Pydantic models
├── services/
│   ├── model_loader.py    # CV model management
│   ├── video_analyzer.py  # Video analysis logic
│   └── ai_grader.py       # OpenAI grading logic
└── routers/
    ├── health.py          # Health check endpoints
    ├── analysis.py        # Video analysis endpoints
    └── grading.py         # AI grading endpoints
```

## Grading System

### Positions Supported
- QB (Quarterback)
- RB (Running Back)
- WR (Wide Receiver)
- TE (Tight End)
- OL (Offensive Line)
- DL (Defensive Line)
- LB (Linebacker)
- DB (Defensive Back)
- K (Kicker)
- P (Punter)

### Grading Scale
- **0-59**: F (Failing)
- **60-69**: D (Below Average)
- **70-76**: C- to C+ (Average)
- **77-86**: B- to B+ (Above Average)
- **87-92**: A- (Excellent)
- **93-100**: A/A+ (Outstanding)

### Position-Specific Criteria

Each position has 4-5 specific criteria (examples):
- **QB**: arm strength, accuracy, decision making, pocket presence, footwork
- **WR**: route running, hands, speed, separation, blocking
- **OL**: pass blocking, run blocking, footwork, hand placement, awareness

## Testing

### Run with mock data (no OpenAI key):
The API will function with mock grading data if no OpenAI key is provided.

### Run with OpenAI:
Set your API key in `.env` for full AI-powered grading.

## Performance Notes

- Video analysis is CPU/GPU intensive
- Frame-by-frame analysis is slow (set `analyze_frames: false` for faster processing)
- Play segmentation is relatively fast
- AI grading calls OpenAI API (rate limits apply)
- Consider processing videos asynchronously in production

## Integration with NestJS Backend

This API provides core AI functionality. Your NestJS backend should:

1. **Handle uploads**: Accept video uploads from users, save to storage, call this API
2. **Manage data**: Store analysis results, grades, and metadata in database
3. **Authentication**: Protect video uploads and grade viewing
4. **User management**: Handle coaches, players, admins
5. **Training library**: Manage training materials for citations

### Recommended Flow:
```
User → NestJS API → Store Video → Call This API → Store Results → Return to User
```

## Troubleshooting

### Models not loading
- Check if YOLO weights exist in the specified path
- API will run in "limited mode" without CV models (grading still works)

### OpenAI errors
- Verify API key is correct
- Check rate limits and quotas
- Ensure sufficient credits

### Video processing slow
- Use GPU for faster processing
- Set `analyze_frames: false` to skip frame-by-frame analysis
- Process smaller video segments

## Next Steps

1. **Test the API**: Use Swagger docs at `/docs`
2. **Integrate with NestJS**: Build your main backend
3. **Add database**: Store results persistently
4. **Deploy**: Consider containerization with Docker
5. **Scale**: Add async processing with Celery/RQ

## License

MIT

## Support

For issues or questions, contact the development team.

