# How to Visualize Video with Bounding Boxes and Analysis

## 📹 **Overview**

After analyzing a video, you can generate a visualized version with:
- ✅ **Bounding boxes** around detected players and ball
- ✅ **Player tracking IDs** (P1, P2, P3, etc.)
- ✅ **Team colors** (if detected)
- ✅ **Confidence scores** for each detection
- ✅ **Frame numbers** and **timestamps**

---

## 🚀 **Step-by-Step Guide**

### **Step 1: Analyze Video**

First, analyze your video with `analyze_frames=true`:

```bash
POST /api/v1/analysis/video
Content-Type: application/json

{
  "video_path": "temp/video.mp4",
  "analyze_frames": true,    // ← REQUIRED for visualization
  "detect_plays": true,
  "track_players": true
}
```

**Response:**
```json
{
  "video_id": "video_1234567890",
  "duration": 15.8,
  "total_frames": 395,
  "fps": 25.0,
  "plays": [...],
  "frame_analyses": [...]
}
```

**Save the `video_id`!**

---

### **Step 2: Generate Visualized Video**

Call the visualization endpoint:

```bash
POST /api/v1/analysis/video/{video_id}/visualize
Content-Type: application/json

{
  "original_video_path": "temp/video.mp4",
  "output_path": "output/video_visualized.mp4"  // Optional
}
```

**Example with cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/video/video_1234567890/visualize" \
  -H "Content-Type: application/json" \
  -d '{
    "original_video_path": "temp/video.mp4",
    "output_path": "output/video_visualized.mp4"
  }'
```

**Response:**
```json
{
  "message": "Video visualization complete",
  "video_id": "video_1234567890",
  "original_video": "temp/video.mp4",
  "visualized_video": "output/video_visualized.mp4",
  "output_path": "output/video_visualized.mp4",
  "file_size_mb": 12.5,
  "frames_processed": 395,
  "plays_detected": 4
}
```

---

## 📊 **What You'll See**

### **Visualizations Include:**

1. **Player Bounding Boxes**
   - Color-coded by player ID
   - Label: `P{id} (team_color) confidence`
   - Example: `P1 (red) 0.95`

2. **Ball Bounding Box**
   - Purple bounding box
   - Label: `Ball confidence`
   - Example: `Ball 0.87`

3. **Frame Information**
   - Frame number (top-left)
   - Timestamp (top-left, below frame number)

4. **Color Coding**
   - Each tracked player gets a unique color
   - Untracked players are gray
   - Ball is purple

---

## 🎨 **Visualization Features**

### **Player Tracking:**
- ✅ Consistent colors per player ID
- ✅ Player ID labels (P1, P2, P3, etc.)
- ✅ Team color detection (if available)
- ✅ Confidence scores

### **Ball Detection:**
- ✅ Purple bounding box
- ✅ Confidence score
- ✅ "Ball" label

### **Frame Info:**
- ✅ Frame number
- ✅ Timestamp in seconds

---

## ⚙️ **Requirements**

1. **Video must be analyzed first** with `analyze_frames=true`
2. **Original video file must exist** at the provided path
3. **Frame analyses must be available** (from previous analysis)

---

## 📝 **Complete Example**

```python
import requests

# Step 1: Analyze video
analysis_response = requests.post(
    "http://localhost:8000/api/v1/analysis/video",
    json={
        "video_path": "temp/video.mp4",
        "analyze_frames": True,  # Required!
        "detect_plays": True,
        "track_players": True
    }
)
video_id = analysis_response.json()["video_id"]
print(f"Video analyzed: {video_id}")

# Step 2: Generate visualization
visualize_response = requests.post(
    f"http://localhost:8000/api/v1/analysis/video/{video_id}/visualize",
    json={
        "original_video_path": "temp/video.mp4",
        "output_path": "output/video_visualized.mp4"
    }
)
output_path = visualize_response.json()["visualized_video"]
print(f"Visualized video saved: {output_path}")
```

---

## 🔍 **Troubleshooting**

### **Error: "Video analysis not found"**
- Make sure you analyzed the video first
- Check that `video_id` is correct

### **Error: "Frame analyses not available"**
- Re-run analysis with `analyze_frames=true`
- Previous analysis might have been done with `analyze_frames=false`

### **Error: "Original video not found"**
- Check that the `original_video_path` is correct
- Make sure the video file still exists

### **Video is too large / Processing is slow**
- Visualization processes all frames
- Large videos take longer
- Consider processing shorter clips

---

## 💡 **Tips**

1. **Use `analyze_frames=true`** during initial analysis
2. **Keep original video** until visualization is complete
3. **Specify output path** to save in a specific location
4. **Check file size** in response to verify output

---

## 🎯 **Quick Start**

```bash
# 1. Analyze
curl -X POST "http://localhost:8000/api/v1/analysis/video" \
  -H "Content-Type: application/json" \
  -d '{"video_path": "temp/video.mp4", "analyze_frames": true}'

# 2. Visualize (replace VIDEO_ID with actual ID)
curl -X POST "http://localhost:8000/api/v1/analysis/video/VIDEO_ID/visualize" \
  -H "Content-Type: application/json" \
  -d '{"original_video_path": "temp/video.mp4"}'
```

---

## 📂 **Output Location**

- Default: `{original_path}_visualized.mp4`
- Custom: Specify `output_path` in request
- Example: `temp/video.mp4` → `temp/video_visualized.mp4`

---

## ✅ **Result**

You'll get a new video file with all bounding boxes, labels, and analysis information drawn on each frame!

