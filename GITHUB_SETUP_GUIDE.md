# GitHub Setup Guide

## ✅ **Step 1: Initialize Git Repository**

```bash
# Initialize git repository
git init

# Add remote (replace with your GitHub repo URL)
git remote add origin https://github.com/yourusername/your-repo-name.git

# Or if you already have a remote:
git remote -v  # Check current remotes
```

---

## ✅ **Step 2: Verify .gitignore**

The `.gitignore` file has been created with comprehensive rules to exclude:
- ✅ **Environment files** (`.env` with API keys)
- ✅ **Model files** (`*.pt`, `*.pth`, `*.t7` - large files)
- ✅ **Video files** (`*.mp4`, `*.avi`, etc.)
- ✅ **Python cache** (`__pycache__/`, `*.pyc`)
- ✅ **IDE files** (`.vscode/`, `.idea/`)
- ✅ **OS files** (`Thumbs.db`, `.DS_Store`)
- ✅ **Temporary files** (`temp/`, `output/`)

---

## ✅ **Step 3: Check What Will Be Committed**

```bash
# See what files would be added (before staging)
git status

# See detailed list of files that will be tracked
git ls-files

# Preview what will be committed
git add --dry-run .
```

---

## ✅ **Step 4: Stage and Commit Files**

```bash
# Stage all files (respects .gitignore)
git add .

# Check what's staged
git status

# Commit
git commit -m "Initial commit: FieldCoachAI API with video analysis and AI grading"

# Or with detailed message:
git commit -m "Initial commit

- Complete FastAPI backend with video analysis
- YOLOv5 + DeepSORT player tracking
- AI-powered grading with OpenAI integration
- Video visualization with bounding boxes
- Auto-detection of players and positions
- Batch grading optimization (92% fewer API calls)"
```

---

## ✅ **Step 5: Push to GitHub**

```bash
# If this is your first push
git branch -M main
git push -u origin main

# Or if branch already exists
git push origin main
```

---

## ⚠️ **Important: Before Pushing**

### **1. Check for Sensitive Files**

```bash
# Make sure .env is ignored
git check-ignore .env
# Should output: .env

# Check for other sensitive files
git check-ignore api/.env
git check-ignore **/.env
```

### **2. Verify Large Files Are Excluded**

```bash
# Check for video files
git ls-files | Select-String "\.mp4|\.avi|\.mov"

# Check for model files
git ls-files | Select-String "\.pt|\.pth|\.t7"

# Should return nothing (all ignored)
```

### **3. Review What's Being Committed**

```bash
# See all files that will be committed
git ls-files

# Check file sizes
git ls-files | ForEach-Object { 
    $size = (Get-Item $_).Length / 1MB
    if ($size -gt 1) { 
        Write-Host "$_ : $([math]::Round($size, 2)) MB" 
    }
}
```

---

## 📋 **Files That Should NOT Be Committed**

The `.gitignore` already excludes these, but verify:

- ❌ `.env` - Contains OpenAI API key
- ❌ `*.pt`, `*.pth`, `*.t7` - Large model files
- ❌ `*.mp4`, `*.avi` - Video files
- ❌ `temp/`, `output/` - Temporary directories
- ❌ `__pycache__/` - Python cache
- ❌ `.vscode/`, `.idea/` - IDE settings

---

## 📋 **Files That SHOULD Be Committed**

- ✅ Source code (`.py` files)
- ✅ Configuration files (`requirements-api.txt`, `config.py`)
- ✅ Documentation (`.md` files)
- ✅ API schemas and models
- ✅ Empty directories (with `.gitkeep` if needed)

---

## 🔒 **Security Checklist**

Before pushing, verify:

- [ ] `.env` file is NOT tracked
- [ ] No API keys in code comments
- [ ] No hardcoded credentials
- [ ] No sensitive data in commit history
- [ ] `.gitignore` is committed

---

## 🚀 **Quick Commands**

```bash
# Initialize and push
git init
git add .
git commit -m "Initial commit: FieldCoachAI API"
git branch -M main
git remote add origin https://github.com/yourusername/repo.git
git push -u origin main
```

---

## 📝 **Recommended Commit Message**

```bash
git commit -m "Initial commit: FieldCoachAI API

Features:
- Video analysis with YOLOv5 + DeepSORT
- AI-powered player grading with OpenAI
- Automatic player detection and position inference
- Video visualization with bounding boxes
- Batch grading optimization (92% fewer API calls)
- Comprehensive API documentation"
```

---

## 🛠️ **If You Need to Remove Already Tracked Files**

If you accidentally committed files that should be ignored:

```bash
# Remove from git but keep locally
git rm --cached .env
git rm --cached temp/*.mp4
git rm --cached "Bird's eye view/weights/*.pt"

# Commit the removal
git commit -m "Remove ignored files from tracking"
```

---

## ✅ **Verify Before Push**

```bash
# Final check
git status
git ls-files | Measure-Object -Line  # Count tracked files

# Should show reasonable number of files (not thousands)
```

---

## 📚 **Next Steps After Pushing**

1. **Create a README.md** describing the project
2. **Add GitHub Actions** for CI/CD (optional)
3. **Set up branch protection** (optional)
4. **Add CONTRIBUTING.md** (if open source)
5. **Add LICENSE** file

---

## 🎯 **Summary**

1. ✅ `.gitignore` created - excludes sensitive/large files
2. ✅ Verify no sensitive files are tracked
3. ✅ Initialize git repository
4. ✅ Stage and commit files
5. ✅ Push to GitHub

**Your repository is now ready!** 🚀

