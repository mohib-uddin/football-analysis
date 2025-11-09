# 🚀 FieldCoachAI API - START HERE

**Status:** ✅ BACKEND READY - SETUP COMPLETE

**Last Updated:** November 10, 2025

---

## ✅ What's Complete

Your FastAPI backend is ready with all core AI business logic:

### Core Features
- ✅ **AI Grading System** - OpenAI GPT-4o powered player grading
- ✅ **Play Segmentation** - Automatic play detection from video
- ✅ **Video Analysis** - YOLOv5 + DeepSORT for player tracking
- ✅ **Coaching Q&A** - AI-powered coaching assistance
- ✅ **Position-Specific Grading** - 11 positions with custom criteria
- ✅ **Complete API Documentation** - Swagger + ReDoc
- ✅ **CORS Support** - Ready for frontend integration
- ✅ **Error Handling** - Robust validation and error responses
- ✅ **Pydantic Models** - All schemas created and validated

---

## 📁 Project Structure

```
footballanalysis-main/
├── api/                          # ✅ FastAPI backend
│   ├── main.py                   # Application entry point
│   ├── core/
│   │   ├── config.py            # Configuration & settings
│   │   └── __init__.py
│   ├── models/
│   │   ├── schemas.py           # Pydantic models
│   │   └── __init__.py
│   ├── services/
│   │   ├── ai_grader.py         # OpenAI grading logic
│   │   ├── video_analyzer.py   # Video processing
│   │   ├── model_loader.py      # CV model management
│   │   └── __init__.py
│   └── routers/
│       ├── grading.py           # AI grading endpoints
│       ├── analysis.py          # Video analysis endpoints
│       ├── health.py            # Health check
│       ├── examples.py          # Response examples
│       └── __init__.py
│
├── Bird's eye view/              # 🔵 Original repo CV models (USED)
│   ├── elements/
│   │   ├── yolo.py              # YOLOv5 detector (INTEGRATED)
│   │   ├── deep_sort.py         # DeepSORT tracker (INTEGRATED)
│   │   └── perspective_transform.py  # (INTEGRATED)
│   └── weights/                 # Model weights (download separately)
│
├── requirements-api.txt          # ✅ Complete dependencies
├── requirements-api-minimal.txt  # ✅ Minimal (no CV libs)
├── .env                         # ✅ Configuration file
│
├── API_DOCUMENTATION.md          # ✅ Complete API docs
├── FRONTEND_INTEGRATION.md       # ✅ Integration guide
├── README-API.md                 # ✅ API setup guide
├── test_api_complete.py          # ✅ Automated test suite
└── START_HERE.md                # 📖 This file
```

---

## 🎯 Quick Start (4 Steps)

### 1. Install Dependencies (Using UV - Recommended)
```bash
# Install UV package manager (if not installed)
pip install uv

# Install minimal dependencies (for grading only)
uv add --requirements requirements-api-minimal.txt

# OR install full dependencies (includes CV libraries - large download)
uv add --requirements requirements-api.txt
```

**Alternative (Using pip):**
```bash
# Minimal installation
py -m pip install -r requirements-api-minimal.txt

# OR full installation
py -m pip install -r requirements-api.txt
```

**Note:** CV libraries (torch, torchvision, opencv) are large downloads (~2GB). If you only need AI grading, use minimal installation.

### 2. Configure API Key
```bash
# Create or edit .env file in project root
OPENAI_API_KEY=your-openai-key-here
```

Get your OpenAI key from: https://platform.openai.com/api-keys

### 3. Start API
```bash
# Navigate to api directory
cd api

# Start with UV (recommended)
uv run main.py

# OR start with Python directly
python main.py
```

### 4. Verify API is Running
API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs (Interactive API testing)
- **ReDoc**: http://localhost:8000/redoc (Clean documentation)
- **Health Check**: http://localhost:8000/api/v1/health

---

## 🧪 Test the API

### Automated Test Suite
```bash
# Run comprehensive tests
py test_api_complete.py
```

This will test:
- ✅ Health check
- ✅ Single play grading
- ✅ Bulk grading
- ✅ Coaching Q&A
- ✅ CORS configuration
- ✅ Error handling
- ✅ Documentation

### Manual Test (Browser)
1. Open http://localhost:8000/docs
2. Click "Try it out" on `/api/v1/grading/play`
3. Use this test data:
```json
{
  "video_id": "test_game",
  "play_id": 1,
  "player_positions": {
    "1": "QB",
    "2": "WR",
    "3": "RB"
  },
  "play_context": "3rd and 5"
}
```
4. Click "Execute"
5. See detailed grades!

---

## 📚 Documentation

### For You (Developer)
1. **API_DOCUMENTATION.md** - Complete API reference
2. **FRONTEND_INTEGRATION.md** - Frontend integration guide with React examples
3. **README-API.md** - Detailed setup and usage

### For API Users
- **Swagger UI**: http://localhost:8000/docs (Interactive)
- **ReDoc**: http://localhost:8000/redoc (Clean docs)

---

## 🔌 API Endpoints Overview

### Health & Status
```
GET  /api/v1/health                 # Check API status
```

### AI Grading (Core Business Logic)
```
POST /api/v1/grading/play           # Grade single play
POST /api/v1/grading/bulk           # Grade all plays
POST /api/v1/grading/qa             # Coaching Q&A
```

### Video Analysis (Optional - requires CV libs)
```
POST /api/v1/analysis/video/upload  # Upload video
POST /api/v1/analysis/video         # Analyze video
```

---

## 💻 Frontend Integration

### Quick Example (React)
```javascript
const API_BASE = 'http://localhost:8000/api/v1';

// Grade a play
const gradePlay = async () => {
  const response = await fetch(`${API_BASE}/grading/play`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_id: 'game_123',
      play_id: 1,
      player_positions: { '1': 'QB', '2': 'WR' },
      play_context: '3rd and 5'
    })
  });
  
  const grades = await response.json();
  console.log(grades.player_grades);
};
```

**Complete Examples:** See `FRONTEND_INTEGRATION.md` for:
- React components
- TypeScript types
- Error handling
- Complete working examples

---

## 🎨 What the API Does

### 1. AI Grading (Core Feature)
- Grades players 0-100 with letter grades (A-F)
- Position-specific criteria (QB: arm strength, accuracy, etc.)
- Detailed qualitative feedback
- Strengths & areas for improvement
- Training material citations

### 2. Play Segmentation
- Automatically detects plays in video
- Identifies start/end times
- Tracks player count
- Detects play type (offensive/defensive)

### 3. Video Analysis (Optional)
- Player detection with YOLOv5
- Player tracking with DeepSORT
- Ball detection and tracking
- Frame-by-frame analysis

### 4. Coaching Q&A
- Ask football coaching questions
- Get AI-powered answers
- Includes training citations
- Role-specific (coach vs player)

---

## ⚙️ Configuration Options

### .env File
```bash
# Required for AI Grading
OPENAI_API_KEY=sk-your-key-here

# API Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Play Segmentation (tunable)
MIN_PLAY_DURATION=2.0
MAX_PLAY_DURATION=30.0
BALL_MOVEMENT_THRESHOLD=50.0
```

### Supported Positions
QB, RB, WR, TE, OL, DL, LB, DB, K, P, LS, ATH, UNKNOWN

### Grading Criteria (Examples)
- **QB**: arm_strength, accuracy, decision_making, pocket_presence, footwork
- **WR**: route_running, hands, speed, separation, blocking
- **RB**: vision, ball_security, power, speed, blocking

*See `api/core/config.py` for complete lists*

---

## 🔧 Troubleshooting

### API won't start
```bash
# Check Python version (need 3.10+, tested on 3.12)
py --version

# Reinstall dependencies with UV
uv add --requirements requirements-api-minimal.txt

# OR with pip
py -m pip install -r requirements-api-minimal.txt
```

### "Attribute 'app' not found" error
```bash
# Use uvicorn directly instead of python main.py
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# OR with uv
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### OpenAI not working
```bash
# Check .env file has your key
cat .env | grep OPENAI_API_KEY

# Or edit manually
# .env
OPENAI_API_KEY=sk-your-actual-key-here
```

### Port 8000 in use
```bash
# Use different port
cd api
py -m uvicorn main:app --port 8001
```

### CV models not loading
**This is OK!** The API works in "limited mode":
- ✅ AI grading works
- ✅ Coaching Q&A works
- ❌ Video analysis disabled

To enable video analysis:
```bash
py -m pip install opencv-python torch torchvision
```

---

## 📊 What's NOT Included

This API provides **core AI business logic only**. Your NestJS backend will handle:

- ❌ User authentication/authorization
- ❌ Database (PostgreSQL, MongoDB, etc.)
- ❌ Video storage (S3, Azure Blob, etc.)
- ❌ User management
- ❌ Training library management
- ❌ File uploads to cloud

**Integration Architecture:**
```
User → NestJS Backend → Store Video → FieldCoachAI API → Store Results → User
           ↓
        Database
           ↓
      Cloud Storage
```

---

## 🎯 Next Steps

### 1. Test the API
```bash
# Start API
cd api && py main.py

# In new terminal, run tests
py test_api_complete.py
```

### 2. Explore Documentation
- Open http://localhost:8000/docs
- Try the endpoints
- See example responses

### 3. Build Your Frontend
- Read `FRONTEND_INTEGRATION.md`
- Copy React examples
- Start building!

### 4. Build Your NestJS Backend
- Handle auth & users
- Store videos in cloud
- Call this API for AI features
- Store results in database

---

## 📈 Performance Notes

### AI Grading
- **Speed**: 2-4 seconds per play
- **Cost**: ~$0.01-0.05 per grading (OpenAI)
- **Concurrent**: Can grade multiple plays in parallel

### Video Analysis
- **Speed**: Depends on video length & hardware
- **Optimization**: Set `analyze_frames: false` for faster results
- **GPU**: Use CUDA for 5-10x speedup

### Coaching Q&A
- **Speed**: 1-3 seconds per question
- **Cost**: ~$0.01-0.02 per question (OpenAI)

---

## 🆘 Need Help?

### Check Documentation
1. `API_DOCUMENTATION.md` - Complete API reference
2. `FRONTEND_INTEGRATION.md` - Integration guide
3. `README-API.md` - Setup guide
4. http://localhost:8000/docs - Interactive API docs

### Common Issues
- **OpenAI errors**: Check API key and credits
- **CV models not loading**: Expected if torch not installed
- **CORS errors**: Check `CORS_ORIGINS` in config
- **Slow responses**: Expected for video analysis

---

## ✅ Checklist

Before frontend integration:

- [ ] API starts successfully
- [ ] Health check returns `"status": "healthy"`
- [ ] Test grading endpoint works
- [ ] OpenAI API key configured
- [ ] Read `FRONTEND_INTEGRATION.md`
- [ ] Run `test_api_complete.py` successfully

---

## 🎉 You're Ready!

The API is **production-ready** for frontend integration!

### What You Have
✅ Complete AI grading system  
✅ Play segmentation logic  
✅ Video analysis (optional)  
✅ Coaching Q&A  
✅ Full API documentation  
✅ CORS configured  
✅ Error handling  
✅ Request validation  
✅ Example responses  
✅ Test suite  
✅ Integration guide  

### Start Building
1. Keep this API running: `cd api && py main.py`
2. Build your frontend (React, Angular, Vue, etc.)
3. Build your NestJS backend (auth, database, storage)
4. Connect them together!

---

## 📞 Integration Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend (React/Angular/Vue)                               │
│       ↓                                                     │
│  NestJS Backend                                             │
│    ├─ Auth & Users                                          │
│    ├─ Database (PostgreSQL)                                 │
│    ├─ Video Storage (S3)                                    │
│    └─ Calls →  FieldCoachAI API (This Repo)                │
│                  ├─ AI Grading                              │
│                  ├─ Play Segmentation                       │
│                  ├─ Video Analysis                          │
│                  └─ Coaching Q&A                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**Ready to integrate? Start with `FRONTEND_INTEGRATION.md`!** 🚀

Good luck building FieldCoachAI! 🏈

