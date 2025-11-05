# Frontend Integration Guide

Complete guide for integrating the FieldCoachAI API with your frontend.

## Table of Contents
1. [Quick Start](#quick-start)
2. [API Endpoints](#api-endpoints)
3. [Request/Response Examples](#requestresponse-examples)
4. [Error Handling](#error-handling)
5. [Best Practices](#best-practices)
6. [React Examples](#react-examples)
7. [TypeScript Types](#typescript-types)

---

## Quick Start

### API Base URL
```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

### Basic Fetch Example
```javascript
// Health check
const response = await fetch(`${API_BASE_URL}/health`);
const data = await response.json();
console.log(data.status); // "healthy"
```

---

## API Endpoints

### 1. Health Check
**GET** `/api/v1/health`

Check API status and model availability.

```javascript
const checkHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/health`);
  return await response.json();
};
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "models_loaded": false,
  "version": "1.0.0"
}
```

---

### 2. Grade Single Play
**POST** `/api/v1/grading/play`

Grade all players in a specific play.

```javascript
const gradeSinglePlay = async (videoId, playId, playerPositions, context) => {
  const response = await fetch(`${API_BASE_URL}/grading/play`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_id: videoId,
      play_id: playId,
      player_positions: playerPositions,
      play_context: context
    })
  });
  
  if (!response.ok) {
    throw new Error(`Grading failed: ${response.statusText}`);
  }
  
  return await response.json();
};

// Usage
const grades = await gradeSinglePlay(
  "game_123",
  1,
  { "1": "QB", "2": "WR", "3": "RB" },
  "3rd and 5, red zone, shotgun formation"
);
```

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
  "play_context": "3rd and 5, midfield"
}
```

**Response:** See [play_grading_example](#play-grading-response)

---

### 3. Grade All Plays (Bulk)
**POST** `/api/v1/grading/bulk`

Grade all plays in a video.

```javascript
const gradeAllPlays = async (videoId, playerPositions) => {
  const response = await fetch(`${API_BASE_URL}/grading/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_id: videoId,
      player_positions: playerPositions
    })
  });
  
  return await response.json();
};

// Usage
const bulkGrades = await gradeAllPlays(
  "game_123",
  { "1": "QB", "2": "WR", "3": "TE", "4": "RB" }
);
```

---

### 4. Coaching Q&A
**POST** `/api/v1/grading/qa`

Ask coaching questions and get AI answers.

```javascript
const askCoachingQuestion = async (question, role = 'coach') => {
  const response = await fetch(`${API_BASE_URL}/grading/qa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question: question,
      role: role,
      context: null
    })
  });
  
  if (response.status === 503) {
    throw new Error('OpenAI API not configured');
  }
  
  return await response.json();
};

// Usage
const answer = await askCoachingQuestion(
  "How can I improve my quarterback's decision-making under pressure?",
  "coach"
);
```

---

### 5. Upload Video
**POST** `/api/v1/analysis/video/upload`

Upload a video file for analysis.

```javascript
const uploadVideo = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/analysis/video/upload`, {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
};

// Usage with file input
const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  const result = await uploadVideo(file);
  console.log('Video path:', result.video_path);
};
```

---

### 6. Analyze Video
**POST** `/api/v1/analysis/video`

Analyze video with computer vision.

```javascript
const analyzeVideo = async (videoPath) => {
  const response = await fetch(`${API_BASE_URL}/analysis/video`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_path: videoPath,
      analyze_frames: false,  // Set to true for detailed analysis
      detect_plays: true,
      track_players: true
    })
  });
  
  if (response.status === 503) {
    throw new Error('CV models not loaded');
  }
  
  return await response.json();
};
```

---

## Request/Response Examples

### Play Grading Response
```json
{
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
          "feedback": "Excellent velocity on deep throws.",
          "examples": ["20-yard out route with tight spiral"]
        }
      ],
      "qualitative_feedback": "Strong performance overall...",
      "strengths": [
        "Quick release",
        "Good pocket presence"
      ],
      "areas_for_improvement": [
        "Footwork on rollouts",
        "Touch on short passes"
      ],
      "training_citations": [
        "QB Fundamentals: Pocket Presence"
      ]
    }
  ],
  "play_summary": "Well-executed offensive play...",
  "processing_time": 3.5
}
```

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes
- **200**: Success
- **400**: Bad Request (invalid parameters)
- **500**: Internal Server Error
- **503**: Service Unavailable (models not loaded or OpenAI not configured)

### Error Handling Example
```javascript
const gradePlay = async (data) => {
  try {
    const response = await fetch(`${API_BASE_URL}/grading/play`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Grading error:', error.message);
    throw error;
  }
};
```

---

## Best Practices

### 1. Use Environment Variables
```javascript
// .env
REACT_APP_API_URL=http://localhost:8000/api/v1

// In your code
const API_BASE_URL = process.env.REACT_APP_API_URL;
```

### 2. Create API Service Layer
```javascript
// services/api.js
const API_BASE_URL = process.env.REACT_APP_API_URL;

export const api = {
  async gradePlay(videoId, playId, playerPositions, context) {
    const response = await fetch(`${API_BASE_URL}/grading/play`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_id: videoId,
        play_id: playId,
        player_positions: playerPositions,
        play_context: context
      })
    });
    return await response.json();
  },
  
  async askQuestion(question, role) {
    const response = await fetch(`${API_BASE_URL}/grading/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, role })
    });
    return await response.json();
  }
};
```

### 3. Handle Loading States
```javascript
const [loading, setLoading] = useState(false);
const [data, setData] = useState(null);
const [error, setError] = useState(null);

const fetchGrades = async () => {
  setLoading(true);
  setError(null);
  try {
    const result = await api.gradePlay(...);
    setData(result);
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};
```

### 4. Implement Retry Logic
```javascript
const fetchWithRetry = async (url, options, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) return await response.json();
      if (i === retries - 1) throw new Error('Max retries reached');
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
};
```

---

## React Examples

### Complete Grade Display Component
```jsx
import React, { useState, useEffect } from 'react';

const PlayerGradeCard = ({ playerId, position, onGrade }) => {
  const [grade, setGrade] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchGrade = async () => {
    setLoading(true);
    try {
      const result = await fetch('http://localhost:8000/api/v1/grading/play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_id: 'game_123',
          play_id: 1,
          player_positions: { [playerId]: position }
        })
      });
      const data = await result.json();
      setGrade(data.player_grades[0]);
      onGrade && onGrade(data);
    } catch (error) {
      console.error('Error fetching grade:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading grade...</div>;
  if (!grade) return <button onClick={fetchGrade}>Grade Player</button>;

  return (
    <div className="grade-card">
      <h3>Player #{grade.player_id} - {grade.position}</h3>
      <div className="overall-grade">
        <span className="letter">{grade.letter_grade}</span>
        <span className="score">{grade.overall_score}/100</span>
      </div>
      <p>{grade.qualitative_feedback}</p>
      
      <div className="strengths">
        <h4>Strengths:</h4>
        <ul>
          {grade.strengths.map((s, i) => <li key={i}>{s}</li>)}
        </ul>
      </div>
      
      <div className="improvements">
        <h4>Areas for Improvement:</h4>
        <ul>
          {grade.areas_for_improvement.map((a, i) => <li key={i}>{a}</li>)}
        </ul>
      </div>
    </div>
  );
};

export default PlayerGradeCard;
```

### Coaching Q&A Component
```jsx
import React, { useState } from 'react';

const CoachingQA = () => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);

  const askQuestion = async () => {
    if (!question.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/grading/qa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question,
          role: 'coach'
        })
      });
      const data = await response.json();
      setAnswer(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="coaching-qa">
      <h2>Ask a Coaching Question</h2>
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="How can I improve..."
        rows={4}
      />
      <button onClick={askQuestion} disabled={loading}>
        {loading ? 'Thinking...' : 'Ask'}
      </button>
      
      {answer && (
        <div className="answer">
          <h3>Answer:</h3>
          <p>{answer.answer}</p>
          <div className="citations">
            <h4>References:</h4>
            <ul>
              {answer.citations.map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </div>
          <p className="confidence">
            Confidence: {(answer.confidence * 100).toFixed(0)}%
          </p>
        </div>
      )}
    </div>
  );
};

export default CoachingQA;
```

---

## TypeScript Types

```typescript
// types/api.ts

export interface HealthCheck {
  status: string;
  timestamp: string;
  models_loaded: boolean;
  version: string;
}

export interface PlayerGrade {
  player_id: number;
  position: 'QB' | 'RB' | 'WR' | 'TE' | 'OL' | 'DL' | 'LB' | 'DB' | 'K' | 'P';
  overall_score: number;
  letter_grade: string;
  criteria_scores: CriteriaScore[];
  qualitative_feedback: string;
  strengths: string[];
  areas_for_improvement: string[];
  training_citations: string[];
}

export interface CriteriaScore {
  criterion: string;
  score: number;
  feedback: string;
  examples: string[];
}

export interface PlayGradingResponse {
  video_id: string;
  play_id: number;
  player_grades: PlayerGrade[];
  play_summary: string;
  processing_time: number;
}

export interface CoachingAnswer {
  question: string;
  answer: string;
  citations: string[];
  confidence: number;
}

// API Service with TypeScript
class FieldCoachAPI {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000/api/v1') {
    this.baseURL = baseURL;
  }

  async gradePlay(
    videoId: string,
    playId: number,
    playerPositions: Record<number, string>,
    context?: string
  ): Promise<PlayGradingResponse> {
    const response = await fetch(`${this.baseURL}/grading/play`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_id: videoId,
        play_id: playId,
        player_positions: playerPositions,
        play_context: context
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return await response.json();
  }

  async askQuestion(question: string, role: 'coach' | 'player' = 'coach'): Promise<CoachingAnswer> {
    const response = await fetch(`${this.baseURL}/grading/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, role })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return await response.json();
  }

  async checkHealth(): Promise<HealthCheck> {
    const response = await fetch(`${this.baseURL}/health`);
    return await response.json();
  }
}

export const apiClient = new FieldCoachAPI();
```

---

## Complete Integration Example

```jsx
// App.jsx - Complete working example
import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = 'http://localhost:8000/api/v1';

function App() {
  const [health, setHealth] = useState(null);
  const [grades, setGrades] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check API health on mount
    fetch(`${API_BASE}/health`)
      .then(res => res.json())
      .then(data => setHealth(data));
  }, []);

  const handleGradePlay = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/grading/play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_id: 'demo_game',
          play_id: 1,
          player_positions: {
            1: 'QB',
            2: 'WR',
            3: 'RB'
          },
          play_context: '3rd and 5, midfield'
        })
      });
      const data = await response.json();
      setGrades(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header>
        <h1>FieldCoachAI Demo</h1>
        {health && (
          <div className="health-status">
            Status: {health.status} | Models: {health.models_loaded ? '✓' : '✗'}
          </div>
        )}
      </header>

      <main>
        <button onClick={handleGradePlay} disabled={loading}>
          {loading ? 'Grading...' : 'Grade Play'}
        </button>

        {grades && (
          <div className="grades">
            <h2>Play Summary</h2>
            <p>{grades.play_summary}</p>
            
            <h2>Player Grades</h2>
            {grades.player_grades.map(grade => (
              <div key={grade.player_id} className="grade-card">
                <h3>Player #{grade.player_id} - {grade.position}</h3>
                <div className="score">
                  {grade.letter_grade} ({grade.overall_score}/100)
                </div>
                <p>{grade.qualitative_feedback}</p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
```

---

## Testing the API

### Using cURL
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Grade a play
curl -X POST http://localhost:8000/api/v1/grading/play \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "test",
    "play_id": 1,
    "player_positions": {"1": "QB", "2": "WR"},
    "play_context": "3rd and 5"
  }'
```

### Using Postman
1. Import the OpenAPI spec from `/docs` (Swagger UI)
2. Set base URL: `http://localhost:8000/api/v1`
3. Test each endpoint with example payloads

---

## Need Help?

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Check logs**: Look at terminal where API is running

---

## Ready to Start!

1. Ensure API is running: `cd api && py main.py`
2. Copy the React examples above
3. Modify API_BASE_URL for your environment
4. Start building your frontend!

Good luck! 🚀

