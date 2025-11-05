# FieldCoachAI - Complete API Workflow Guide

## 🎯 Core Functionality Status

### ✅ **COMPLETE - Ready for Frontend Integration**

| Feature | Status | Endpoint | Notes |
|---------|--------|----------|-------|
| **AI Grading** | ✅ Complete | `/api/v1/grading/play` | OpenAI GPT-4o powered |
| **Bulk Grading** | ✅ Complete | `/api/v1/grading/bulk` | Grade all plays at once |
| **Coaching Q&A** | ✅ Complete | `/api/v1/grading/qa` | AI-powered answers |
| **Play Segmentation** | ✅ Complete | Built into video analysis | Automatic play detection |
| **Video Analysis** | ⚠️ Partial | `/api/v1/analysis/video` | Works if CV models loaded |
| **Video Upload** | ✅ Complete | `/api/v1/analysis/video/upload` | File upload endpoint |
| **Health Check** | ✅ Complete | `/api/v1/health` | API status |

### ⚠️ **What's Missing (For Your NestJS Backend to Handle)**

1. **Authentication/Authorization** - Not in this API (handled by NestJS)
2. **Database Storage** - Not in this API (handled by NestJS)
3. **User Management** - Not in this API (handled by NestJS)
4. **Training Library Management** - Not in this API (handled by NestJS)
5. **Cloud Storage Integration** - Not in this API (handled by NestJS)

**This API provides CORE AI BUSINESS LOGIC only.**

---

## 📋 Complete API Call Workflow

Based on your original requirements, here's the exact order of API calls:

### **Workflow 1: Upload Video → Analyze → Grade Plays**

#### Step 1: Upload Video
```http
POST /api/v1/analysis/video/upload
Content-Type: multipart/form-data

file: [video file]
```

**Response:**
```json
{
  "message": "Video uploaded successfully",
  "video_path": "temp/game_footage.mp4",
  "filename": "game_footage.mp4",
  "size_bytes": 15728640
}
```

**Save:** `video_path` for next step

---

#### Step 2: Analyze Video (Get Plays)
```http
POST /api/v1/analysis/video
Content-Type: application/json

{
  "video_path": "temp/game_footage.mp4",
  "analyze_frames": false,        // Skip for speed
  "detect_plays": true,           // IMPORTANT: Get play segments
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
    },
    {
      "play_id": 2,
      "start_time": 20.0,
      "end_time": 28.0,
      "duration": 8.0,
      ...
    }
  ],
  "processing_time": 12.3
}
```

**Save:**
- `video_id` - Use for all grading calls
- `plays` array - Each play has `play_id` you'll need

---

#### Step 3: Grade Each Play

For **EACH** play from Step 2, call:

```http
POST /api/v1/grading/play
Content-Type: application/json

{
  "video_id": "game_footage_123_1705315800",
  "play_id": 1,                    // From plays array
  "player_positions": {
    "1": "QB",                      // Map player_id to position
    "2": "WR",
    "3": "RB",
    "4": "OL",
    "5": "DL",
    "6": "LB",
    "7": "DB"
    // ... add all players
  },
  "play_context": "3rd and 5, midfield, shotgun formation"
}
```

**Response:**
```json
{
  "video_id": "game_footage_123_1705315800",
  "play_id": 1,
  "player_grades": [
    {
      "player_id": 1,
      "position": "QB",
      "overall_score": 87.5,
      "letter_grade": "B+",
      "criteria_scores": [...],
      "qualitative_feedback": "Strong performance...",
      "strengths": ["Quick release", "Good pocket presence"],
      "areas_for_improvement": ["Footwork consistency", "Touch on short passes"],
      "training_citations": ["QB Fundamentals: Pocket Presence", ...]
    },
    // ... more players
  ],
  "play_summary": "Well-executed offensive play...",
  "processing_time": 3.5
}
```

**Save:** All grades in your database (NestJS backend)

---

### **Workflow 2: Bulk Grade All Plays (Alternative)**

If you want to grade ALL plays at once:

```http
POST /api/v1/grading/bulk
Content-Type: application/json

{
  "video_id": "game_footage_123_1705315800",
  "player_positions": {
    "1": "QB",
    "2": "WR",
    "3": "RB",
    // ... all players
  }
}
```

**Response:** Grades for all plays in one response

---

### **Workflow 3: Coaching Q&A (Anytime)**

This can be called independently:

```http
POST /api/v1/grading/qa
Content-Type: application/json

{
  "question": "How can I improve my quarterback's decision-making under pressure?",
  "role": "coach"  // or "player"
}
```

**Response:**
```json
{
  "question": "...",
  "answer": "To improve quarterback decision-making...",
  "citations": ["QB Decision Making Under Duress", ...],
  "confidence": 0.92
}
```

---

## 🔄 Complete Integration Flow

### **For Your NestJS Backend:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User uploads video via NestJS                            │
│    ↓                                                         │
│ 2. NestJS saves video to cloud storage (S3/Azure)          │
│    ↓                                                         │
│ 3. NestJS calls: POST /api/v1/analysis/video/upload        │
│    (or skips if already uploaded)                           │
│    ↓                                                         │
│ 4. NestJS calls: POST /api/v1/analysis/video               │
│    Gets: video_id, plays[]                                  │
│    ↓                                                         │
│ 5. NestJS saves plays to database                           │
│    ↓                                                         │
│ 6. For each play, NestJS calls:                             │
│    POST /api/v1/grading/play                               │
│    Gets: player_grades[]                                    │
│    ↓                                                         │
│ 7. NestJS saves grades to database                          │
│    ↓                                                         │
│ 8. NestJS returns results to frontend                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Step-by-Step Implementation Guide

### **Phase 1: Video Upload & Analysis**

```javascript
// 1. User uploads video (handled by NestJS)
// 2. Call this API to analyze
const analyzeVideo = async (videoPath) => {
  const response = await fetch('http://localhost:8000/api/v1/analysis/video', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_path: videoPath,
      analyze_frames: false,  // Faster
      detect_plays: true,     // Required!
      track_players: true
    })
  });
  
  const analysis = await response.json();
  
  // Save to your database:
  // - video_id
  // - plays array (with play_id, start_time, end_time, etc.)
  
  return analysis;
};
```

### **Phase 2: Grade Each Play**

```javascript
// For each play from Phase 1
const gradePlay = async (videoId, playId, playerPositions, context) => {
  const response = await fetch('http://localhost:8000/api/v1/grading/play', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_id: videoId,
      play_id: playId,
      player_positions: playerPositions,  // Map of player_id -> position
      play_context: context
    })
  });
  
  const grades = await response.json();
  
  // Save to your database:
  // - Each player_grade with all details
  // - Link to video_id and play_id
  
  return grades;
};

// Process all plays
const gradeAllPlays = async (videoId, plays, playerPositions) => {
  const allGrades = [];
  
  for (const play of plays) {
    const grades = await gradePlay(
      videoId,
      play.play_id,
      playerPositions,
      `Play ${play.play_id}: ${play.play_type}`
    );
    allGrades.push(grades);
    
    // Optional: Add delay to avoid rate limits
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  return allGrades;
};
```

### **Phase 3: Display Results**

```javascript
// Frontend fetches from your NestJS backend
// NestJS returns grades from database
// Display in UI with:
// - Play-by-play list
// - Player grades
// - Strengths/improvements
// - Training citations
```

---

## 🎯 Key Requirements Checklist

Based on your original doc, here's what each API provides:

### ✅ **Video Upload & Storage**
- ✅ Upload endpoint: `/api/v1/analysis/video/upload`
- ⚠️ Cloud storage: Your NestJS handles this

### ✅ **Computer Vision Analysis**
- ✅ Player detection: Built into video analysis
- ✅ Player tracking: Built into video analysis
- ✅ Ball detection: Built into video analysis
- ⚠️ Requires CV models to be loaded (optional)

### ✅ **Play Segmentation**
- ✅ Automatic play detection: Returns `plays[]` array
- ✅ Play timestamps: `start_time`, `end_time` in each play
- ✅ Play metadata: `play_type`, `player_count`, `key_events`

### ✅ **AI Grading System**
- ✅ Grade every player: `player_grades[]` array
- ✅ Qualitative feedback: `qualitative_feedback` field
- ✅ Numeric scores: `overall_score` (0-100)
- ✅ Letter grades: `letter_grade` (A-F)
- ✅ Position-specific criteria: `criteria_scores[]` array
- ✅ Training citations: `training_citations[]` array

### ✅ **Coaching Q&A**
- ✅ Ask questions: `/api/v1/grading/qa`
- ✅ AI answers: `answer` field
- ✅ Citations: `citations[]` array
- ⚠️ Training library search: Basic (OpenAI-powered)

---

## ⚠️ What's Missing (For Your NestJS Backend)

### **1. Training System (Admin)**
- Upload coaching videos: Your NestJS handles
- Upload transcripts: Your NestJS handles
- Link transcripts to videos: Your NestJS handles
- Tag training materials: Your NestJS handles
- Index transcripts: Your NestJS handles

**This API uses OpenAI for citations, but you'll want to build a training library search in NestJS.**

### **2. User Management**
- User login/logout: NestJS
- Password reset: NestJS
- Role-based access: NestJS
- User accounts: NestJS

### **3. Data Persistence**
- Store videos: NestJS + Database
- Store grades: NestJS + Database
- Store plays: NestJS + Database
- Store training materials: NestJS + Database

---

## 🚀 Recommended Implementation Order

### **Week 1: Core Grading**
1. ✅ Test grading endpoint
2. ✅ Integrate with NestJS
3. ✅ Store grades in database
4. ✅ Display grades in frontend

### **Week 2: Video Analysis**
1. ✅ Integrate video upload
2. ✅ Call analysis endpoint
3. ✅ Store plays in database
4. ✅ Grade plays automatically

### **Week 3: Full Workflow**
1. ✅ Complete video → analysis → grading flow
2. ✅ Add coaching Q&A
3. ✅ Build training library (NestJS)
4. ✅ Enhance citations

---

## 📊 API Call Summary

### **Minimum Required Calls:**

1. **Upload Video** (if using API upload)
   ```
   POST /api/v1/analysis/video/upload
   ```

2. **Analyze Video** (get plays)
   ```
   POST /api/v1/analysis/video
   ```

3. **Grade Each Play**
   ```
   POST /api/v1/grading/play (called multiple times)
   ```

### **Optional Calls:**

- **Bulk Grading** (alternative to individual calls)
  ```
  POST /api/v1/grading/bulk
  ```

- **Coaching Q&A** (anytime)
  ```
  POST /api/v1/grading/qa
  ```

---

## ✅ Everything is Ready!

Your API has **ALL core functionality** needed. The missing pieces (auth, database, storage) are intentionally left for your NestJS backend.

**Start integrating now!** Follow the workflow above. 🚀

