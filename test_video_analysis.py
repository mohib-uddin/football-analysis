"""
Test script to verify video analysis is working properly
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from api.services.model_loader import ModelLoader
from api.core.config import settings
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_model_loading():
    """Test that all models load correctly"""
    print("="*60)
    print("Testing Model Loading")
    print("="*60)
    
    model_loader = ModelLoader()
    await model_loader.load_models()
    
    print(f"\n✓ Models loaded: {model_loader.is_ready()}")
    print(f"✓ YOLO detector: {'Available' if model_loader.get_detector() else 'Not available'}")
    print(f"✓ DeepSORT tracker: {'Available' if model_loader.get_tracker() else 'Not available'}")
    print(f"✓ Perspective transform: {'Available' if model_loader.get_perspective_transform() else 'Not available'}")
    
    if model_loader.is_ready():
        print("\n✅ All models loaded successfully!")
        return True
    else:
        print("\n⚠️  Models not loaded. Check:")
        print("   1. CV libraries installed (opencv-python, torch, torchvision)")
        print("   2. YOLO weights downloaded to:", settings.YOLO_MODEL_PATH)
        print("   3. DeepSORT config exists at:", settings.DEEPSORT_CONFIG_PATH)
        return False

def check_requirements():
    """Check if all required packages are installed"""
    print("\n" + "="*60)
    print("Checking Requirements")
    print("="*60)
    
    required = {
        'cv2': 'opencv-python',
        'torch': 'torch',
        'torchvision': 'torchvision',
        'numpy': 'numpy',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'openai': 'openai'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"Install with: py -m pip install {' '.join(missing)}")
        return False
    else:
        print("\n✅ All required packages installed!")
        return True

def check_model_files():
    """Check if model files exist"""
    print("\n" + "="*60)
    print("Checking Model Files")
    print("="*60)
    
    yolo_path = Path(settings.YOLO_MODEL_PATH)
    deepsort_config = Path(settings.DEEPSORT_CONFIG_PATH)
    
    print(f"YOLO model: {yolo_path}")
    if yolo_path.exists():
        print(f"  ✓ Found ({yolo_path.stat().st_size / 1024 / 1024:.1f} MB)")
    else:
        print(f"  ✗ Not found")
        print(f"  Download from: https://docs.google.com/uc?export=download&id=1EaBmCzl4xnuebfoQnxU1xQgNmBy7mWi2")
        print(f"  Place in: {yolo_path.parent}")
    
    print(f"\nDeepSORT config: {deepsort_config}")
    if deepsort_config.exists():
        print(f"  ✓ Found")
    else:
        print(f"  ✗ Not found")
    
    return yolo_path.exists() and deepsort_config.exists()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("FieldCoachAI Video Analysis - System Check")
    print("="*60)
    
    # Check requirements
    reqs_ok = check_requirements()
    
    # Check model files
    files_ok = check_model_files()
    
    # Test model loading
    if reqs_ok:
        models_ok = asyncio.run(test_model_loading())
    else:
        models_ok = False
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    if reqs_ok and files_ok and models_ok:
        print("✅ System is ready for video analysis!")
        print("\nNext steps:")
        print("  1. Start API: cd api && py main.py")
        print("  2. Test video upload: POST /api/v1/analysis/video/upload")
        print("  3. Analyze video: POST /api/v1/analysis/video")
    else:
        print("⚠️  System needs configuration:")
        if not reqs_ok:
            print("  - Install missing packages")
        if not files_ok:
            print("  - Download model weights")
        if not models_ok:
            print("  - Fix model loading issues")
    
    print()

