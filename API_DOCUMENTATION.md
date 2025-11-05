# FieldCoachAI - Core AI API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**Interactive Docs:** http://localhost:8000/docs

---

## Overview

FieldCoachAI provides AI-powered football video analysis and player grading through a REST API. The system uses computer vision (YOLOv5, DeepSORT) for video analysis and OpenAI GPT-4 for intelligent grading.

### Key Features
- **Video Analysis**: Player detection, tracking, and play segmentation
- **AI Grading**: Position-specific player performance grading
- **Coaching Q&A**: AI-powered coaching assistance
- **Production-Ready**: Full CORS support, error handling, and validation

---

## Architecture

### Technology Stack
- **Framework**: FastAPI 0.104.1
- **AI/ML**: OpenAI GPT-4o, YOLOv5, DeepSORT
- **Computer Vision**: OpenCV, PyTorch
- **Validation**: Pydantic v2

### Components
1. **Video Analysis Service** (`api/services/video_analyzer.py`)
   - Frame extraction and processing
   - Player/ball detection
   - Play segmentation

2. **AI Grading Service** (`api/services/ai_grader.py`)
   - OpenAI integration
   - Position-specific grading
   - Feedback generation

3. **Model Loader** (`api/services/model_loader.py`)
   - CV model management
   - Graceful degradation if models unavailable

---

## Quick Start

### 1. Installation
```bash
# Install dependencies
py -m pip install -r requirements-api.txt

# Or minimal (for testing without CV)
py -m pip install -r requirements-api-minimal.txt
```

### 2. Configuration
```bash
# Copy and edit .env file
cp .env.example .env

# Add your OpenAI API key
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run API
```bash
cd api
py main.py

# Or with uvicorn
py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test
```bash
# Open browser
http://localhost:8000/docs

# Or run automated tests
py test_api_complete.py
```

---

## API Endpoints

### Health & Status

#### GET `/api/v1/health`
Check API health and model status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "models_loaded": false,
  "version": "1.0.0"
}
```

**Status Codes:**
- `200`: API is healthy

---

### AI Grading

#### POST `/api/v1/grading/play`
Grade all players in a specific play.

**Request:**
```json
{
  "video_id": "game_123",
  "play_id": 1,
  "player_positions": {
    "1": "QB",
    "2": "WR",
    "3": "RB",
    "4": "OL",
    "5": "DL"
  },
  "play_context": "3rd and 5, midfield, shotgun"
}
```

**Response:** [See full example in FRONTEND_INTEGRATION.md]

**Features:**
- Position-specific criteria (QB: arm strength, accuracy, etc.)
- Numeric scores (0-100) + letter grades (A-F)
- Qualitative feedback
- Strengths & areas for improvement
- Training citations

**Status Codes:**
- `200`: Success
- `400`: Invalid request
- `500`: Server error
- `503`: OpenAI not configured

---

#### POST `/api/v1/grading/bulk`
Grade all plays in a video.

**Request:**
```json
{
  "video_id": "game_123",
  "player_positions": {
    "1": "QB",
    "2": "WR",
    "3": "TE",
    "4": "RB"
  }
}
```

**Response:**
```json
{
  "video_id": "game_123",
  "total_plays": 3,
  "play_grades": [/* array of PlayGradingResponse */],
  "processing_time": 9.5
}
```

**Note:** Processes sequentially. For better performance, call `/play` in parallel.

---

#### POST `/api/v1/grading/qa`
Ask coaching questions.

**Request:**
```json
{
  "question": "How can I improve QB decision-making under pressure?",
  "role": "coach",
  "context": null
}
```

**Response:**
```json
{
  "question": "How can I improve...",
  "answer": "To improve quarterback decision-making...",
  "citations": [
    "QB Decision Making Under Duress",
    "Pocket Presence Training Manual"
  ],
  "confidence": 0.92
}
```

**Roles:**
- `coach`: Strategic and tactical insights
- `player`: Player-focused advice and motivation

**Status Codes:**
- `200`: Success
- `503`: OpenAI API not configured

---

### Video Analysis

#### POST `/api/v1/analysis/video/upload`
Upload video file.

**Request:** `multipart/form-data`
- `file`: Video file (MP4, AVI, MOV, MKV)

**Response:**
```json
{
  "message": "Video uploaded successfully",
  "video_path": "temp/game_footage.mp4",
  "filename": "game_footage.mp4",
  "size_bytes": 15728640
}
```

**Supported Formats:** `.mp4`, `.avi`, `.mov`, `.mkv`

**Status Codes:**
- `200`: Success
- `400`: Invalid file type

---

#### POST `/api/v1/analysis/video`
Analyze video with computer vision.

**Request:**
```json
{
  "video_path": "temp/game_footage.mp4",
  "analyze_frames": false,
  "detect_plays": true,
  "track_players": true
}
```

**Response:**
```json
{
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
    }
  ],
  "frame_analyses": null,
  "processing_time": 12.3
}
```

**Performance:**
- Frame-by-frame analysis is CPU/GPU intensive
- Set `analyze_frames: false` for faster processing
- Recommended: Videos < 5 minutes

**Status Codes:**
- `200`: Success
- `400`: Invalid video path
- `503`: CV models not loaded

**Requires:** OpenCV, torch, torchvision installed

---

## Data Models

### Supported Positions
- **QB**: Quarterback
- **RB**: Running Back
- **WR**: Wide Receiver
- **TE**: Tight End
- **OL**: Offensive Line
- **DL**: Defensive Line
- **LB**: Linebacker
- **DB**: Defensive Back
- **K**: Kicker
- **P**: Punter

### Grading Scale
| Score | Grade | Description |
|-------|-------|-------------|
| 93-100 | A | Outstanding |
| 90-92 | A- | Excellent |
| 87-89 | B+ | Very Good |
| 83-86 | B | Above Average |
| 80-82 | B- | Good |
| 77-79 | C+ | Above Average |
| 73-76 | C | Average |
| 70-72 | C- | Below Average |
| 60-69 | D | Poor |
| 0-59 | F | Failing |

### Position-Specific Criteria

**QB (Quarterback)**
- arm_strength
- accuracy
- decision_making
- pocket_presence
- footwork

**WR (Wide Receiver)**
- route_running
- hands
- speed
- separation
- blocking

**RB (Running Back)**
- vision
- ball_security
- power
- speed
- blocking

*[See `api/core/config.py` for complete criteria list]*

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes
- **200**: Success
- **400**: Bad Request (validation failed)
- **422**: Unprocessable Entity (schema validation failed)
- **500**: Internal Server Error
- **503**: Service Unavailable (models/OpenAI not configured)

### Example Error Handling
```javascript
try {
  const response = await fetch('/api/v1/grading/play', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  
  if (!response.ok) {
    const error = await response.json();
    console.error('API Error:', error.detail);
    // Handle error
  }
  
  const data = await response.json();
  // Process data
} catch (error) {
  console.error('Network error:', error);
}
```

---

## Configuration

### Environment Variables

```bash
# OpenAI Configuration (Required for grading)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=2000

# API Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Model Paths
YOLO_MODEL_PATH=Bird's eye view/weights/yolov5m.pt
DEEPSORT_CONFIG_PATH=Bird's eye view/deep_sort_pytorch/configs/deep_sort.yaml

# Play Segmentation Parameters
MIN_PLAY_DURATION=2.0
MAX_PLAY_DURATION=30.0
BALL_MOVEMENT_THRESHOLD=50.0
PLAYER_CLUSTERING_THRESHOLD=100.0
```

### CORS Configuration

Default allowed origins:
- `http://localhost:3000` (React)
- `http://localhost:3001`
- `http://localhost:4200` (Angular)
- `http://localhost:5173` (Vite)
- `http://localhost:8080` (Vue)

**Production:** Update `CORS_ORIGINS` in `.env` to specific domains.

---

## Performance Optimization

### Video Analysis
1. **Skip frame-by-frame analysis**: Set `analyze_frames: false`
2. **Process shorter clips**: Break long videos into segments
3. **Use GPU**: Install CUDA-enabled PyTorch for faster processing
4. **Async processing**: Process videos in background (not included in this API)

### Grading
1. **Parallel requests**: Call `/grading/play` in parallel for multiple plays
2. **Cache results**: Store grades in your database
3. **Limit players**: Grade fewer players per request if needed

### OpenAI
- **Rate limits**: OpenAI has rate limits (~3500 RPM for GPT-4)
- **Costs**: Each grading call costs ~$0.01-0.05
- **Optimization**: Batch questions, use shorter contexts

---

## Testing

### Manual Testing
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Grade a play
curl -X POST http://localhost:8000/api/v1/grading/play \
  -H "Content-Type: application/json" \
  -d '{"video_id":"test","play_id":1,"player_positions":{"1":"QB"}}'
```

### Automated Testing
```bash
# Run comprehensive test suite
py test_api_complete.py
```

### Interactive Testing
1. Open http://localhost:8000/docs
2. Click "Try it out" on any endpoint
3. Fill in parameters
4. Click "Execute"

---

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in environment
- [ ] Configure specific CORS origins (remove `*`)
- [ ] Add rate limiting
- [ ] Set up monitoring/logging
- [ ] Use production WSGI server (gunicorn)
- [ ] Add authentication/authorization
- [ ] Set up SSL/TLS
- [ ] Configure database for persistent storage

### Recommended Stack
- **Server**: Gunicorn + Uvicorn workers
- **Reverse Proxy**: Nginx
- **Database**: PostgreSQL (for your NestJS backend)
- **Cache**: Redis
- **Queue**: Celery (for async video processing)

---

## Integration with NestJS Backend

This API provides core AI functionality. Your NestJS backend should:

1. **Video Management**
   - Accept uploads from users
   - Store videos in cloud (S3, Azure Blob)
   - Call this API for analysis
   - Store results in database

2. **User Management**
   - Authentication (JWT)
   - Role-based access (Admin/Coach/Player)
   - User profiles

3. **Data Persistence**
   - Store videos, grades, plays
   - Training library management
   - User preferences

4. **Business Logic**
   - Assign players to positions
   - Manage teams and rosters
   - Generate reports

### Recommended Flow
```
User → NestJS API → Store Video → Call FieldCoachAI API → Store Results → Return to User
```

---

## Troubleshooting

### API won't start
- Check if port 8000 is available
- Verify Python version (3.8+)
- Check dependencies installed

### CV models not loading
- Models run in "limited mode" (grading only)
- Install: `py -m pip install opencv-python torch torchvision`
- Download YOLO weights (see README)

### OpenAI errors
- Check API key is valid
- Verify sufficient credits
- Check rate limits

### Slow video processing
- Expected for long videos
- Use GPU acceleration
- Set `analyze_frames: false`

---

## Support & Resources

- **API Documentation**: http://localhost:8000/docs
- **Frontend Integration Guide**: `FRONTEND_INTEGRATION.md`
- **Requirements**: `requirements-api.txt`
- **Test Suite**: `test_api_complete.py`

---

## Changelog

### Version 1.0.0 (Current)
- Initial release
- Video analysis with YOLOv5 + DeepSORT
- AI grading with OpenAI GPT-4o
- Play segmentation
- Coaching Q&A
- Full API documentation
- CORS support
- Error handling
- Request validation

---

## License

MIT

---

**Ready for Frontend Integration!** 🚀

See `FRONTEND_INTEGRATION.md` for React/TypeScript examples and complete integration guide.

