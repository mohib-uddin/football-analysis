"""
Model loader service - loads and manages CV models
"""
import sys
from pathlib import Path
import logging
import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from api.core.config import settings

logger = logging.getLogger(__name__)

class ModelLoader:
    """Manages loading and access to CV models"""
    
    def __init__(self):
        self.yolo_detector = None
        self.deep_sort_tracker = None
        self.perspective_transform = None
        self.models_loaded = False

    def _download_yolo_model(self, model_path: Path) -> bool:
        """Download YOLO model if it doesn't exist"""
        try:
            import torch
            logger.info(f"YOLO model not found at {model_path}")
            logger.info("Attempting to download YOLOv5m model...")
            
            # Create weights directory if it doesn't exist
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download from YOLOv5 releases
            url = "https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5m.pt"
            logger.info(f"Downloading from {url}")
            
            torch.hub.download_url_to_file(url, str(model_path), progress=True)
            
            if model_path.exists() and model_path.stat().st_size > 1_000_000:  # Check file is > 1MB
                logger.info(f"✓ Model downloaded successfully ({model_path.stat().st_size / 1024 / 1024:.1f} MB)")
                return True
            else:
                logger.error("Download failed or file is corrupted")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download YOLO model: {e}")
            logger.info("You can manually download from: https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5m.pt")
            logger.info(f"Place the file in: {model_path.parent}")
            return False

    def _download_deepsort_model(self, model_path: Path) -> bool:
        """Download DeepSORT model if it doesn't exist"""
        try:
            import torch
            logger.info(f"DeepSORT model not found at {model_path}")
            logger.info("Attempting to download DeepSORT model...")
            
            # Create weights directory if it doesn't exist
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Try multiple download sources
            urls = [
                "https://drive.google.com/uc?export=download&id=1_qwTWdzT9dWNudpusgKavj_4elGgbkUN",
                "https://github.com/ZQPei/deep_sort_pytorch/raw/master/deep_sort/deep/checkpoint/ckpt.t7",
            ]
            
            success = False
            for i, url in enumerate(urls, 1):
                try:
                    logger.info(f"Attempting download from source {i}/{len(urls)}...")
                    
                    # Try using requests first (better for Google Drive)
                    if "drive.google.com" in url:
                        # Google Drive requires special handling for large files
                        file_id = url.split('id=')[-1]
                        direct_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"
                        
                        session = requests.Session()
                        response = session.get(direct_url, stream=True, allow_redirects=True, timeout=30)
                        response.raise_for_status()
                        
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        logger.info(f"Downloading DeepSORT model (size: {total_size / 1024 / 1024:.1f} MB if known)...")
                        
                        with open(str(model_path), 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_size > 0:
                                        percent = (downloaded / total_size) * 100
                                        if downloaded % (1024 * 1024 * 5) < 8192:  # Print every 5 MB
                                            logger.info(f"Downloaded {downloaded / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB ({percent:.1f}%)")
                                    else:
                                        # Unknown size, just print every 5 MB
                                        if downloaded % (1024 * 1024 * 5) < 8192:
                                            logger.info(f"Downloaded {downloaded / 1024 / 1024:.1f} MB...")
                    else:
                        # For GitHub URLs, use torch.hub.download_url_to_file
                        torch.hub.download_url_to_file(url, str(model_path), progress=True)
                    
                    # Verify download
                    if model_path.exists() and model_path.stat().st_size > 1_000_000:  # Check file is > 1MB
                        logger.info(f"✓ Model downloaded successfully ({model_path.stat().st_size / 1024 / 1024:.1f} MB)")
                        success = True
                        break
                    else:
                        logger.warning(f"Download from source {i} failed or file is too small")
                        if model_path.exists():
                            model_path.unlink()  # Remove invalid file
                        
                except Exception as e:
                    logger.warning(f"Download from source {i} failed: {e}")
                    if model_path.exists():
                        model_path.unlink()  # Remove failed download
                    continue
            
            if not success:
                logger.error("All download attempts failed")
                logger.info("Manual download required:")
                logger.info("1. Download from: https://drive.google.com/uc?id=1_qwTWdzT9dWNudpusgKavj_4elGgbkUN")
                logger.info(f"2. Save as: {model_path}")
                logger.info("Alternatively, search for 'deep_sort_pytorch checkpoint.t7' online")
                return False
            
            return True
                
        except Exception as e:
            logger.error(f"Failed to download DeepSORT model: {e}")
            logger.info("Manual download required:")
            logger.info("1. Download from: https://drive.google.com/uc?id=1_qwTWdzT9dWNudpusgKavj_4elGgbkUN")
            logger.info(f"2. Save as: {model_path}")
            logger.info("Alternatively, search for 'deep_sort_pytorch checkpoint.t7' online")
            return False
    
    async def load_models(self):
        """Load all required models"""
        try:
            # Check if CV libraries are available
            try:
                import cv2
                import torch
            except ImportError as e:
                logger.warning(f"CV libraries not installed: {e}")
                logger.warning("API will run in limited mode (grading only, no video analysis)")
                logger.info("To enable video analysis, install: py -m pip install opencv-python torch torchvision")
                self.models_loaded = False
                return
            
            # Check GPU availability and log device info
            logger.info("=" * 60)
            logger.info("GPU ACCELERATION CHECK")
            logger.info("=" * 60)
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
                logger.info(f"✅ GPU DETECTED: {gpu_name}")
                logger.info(f"   GPU Count: {gpu_count}")
                logger.info(f"   GPU Memory: {gpu_memory:.2f} GB")
                logger.info(f"   CUDA Version: {torch.version.cuda}")
                logger.info("   Models will use GPU acceleration ⚡")
            else:
                logger.warning("⚠️  NO GPU DETECTED - Using CPU (much slower)")
                logger.warning("   For faster processing, install CUDA-enabled PyTorch:")
                logger.warning("   py -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
            logger.info("=" * 60)
            
            logger.info("Loading YOLO detector...")
            # Import with proper path handling
            birds_eye_view_path = str(Path(__file__).resolve().parent.parent.parent / "Bird's eye view")
            
            # Check if YOLO model file exists, download if not
            model_path = Path(settings.YOLO_MODEL_PATH)
            logger.info(f"Checking for YOLO model at: {model_path}")
            if not model_path.exists():
                logger.warning(f"❌ YOLO model not found")
                if not self._download_yolo_model(model_path):
                    logger.error("Failed to download YOLO model")
                logger.warning("API will run in limited mode (grading only, no video analysis)")
                self.models_loaded = False
                return
            else:
                logger.info(f"✓ YOLO model found ({model_path.stat().st_size / 1024 / 1024:.1f} MB)")
            
            # Temporarily add path for imports, then remove to avoid main.py import
            path_added = False
            if birds_eye_view_path not in sys.path:
                sys.path.insert(0, birds_eye_view_path)
                path_added = True
            
            try:
            from elements.yolo import YOLO
            self.yolo_detector = YOLO(
                model_path=str(model_path),
                conf_thres=0.4,
                iou_thres=0.5
            )
            finally:
                # Remove path immediately after import to prevent main.py discovery
                if path_added and birds_eye_view_path in sys.path:
                    sys.path.remove(birds_eye_view_path)
            
            # Verify GPU usage
            if torch.cuda.is_available():
                # Check if model is on GPU
                model_device = next(self.yolo_detector.yolo_model.parameters()).device
                if 'cuda' in str(model_device):
                    logger.info(f"✓ YOLO detector loaded on GPU: {model_device}")
                else:
                    logger.warning(f"⚠️  YOLO detector loaded on CPU: {model_device}")
                    logger.warning("   Performance will be slower - consider GPU installation")
            else:
                logger.info("✓ YOLO detector loaded on CPU")
            
            # Load DeepSORT tracker
            logger.info("Loading DeepSORT tracker...")
            deepsort_config = Path(settings.DEEPSORT_CONFIG_PATH)
            if not deepsort_config.exists():
                logger.error(f"❌ DeepSORT config not found at: {deepsort_config}")
                logger.warning("API will run in limited mode without player tracking")
                self.models_loaded = False
                return
            
            logger.info(f"✓ DeepSORT config found at: {deepsort_config}")
            
            # Check if DeepSORT model exists (path is relative to Bird's eye view directory)
            birds_eye_view_dir = Path(settings.BASE_DIR) / "Bird's eye view"
            deepsort_model_path = birds_eye_view_dir / "weights" / "deepsort_model.t7"
            logger.info(f"Checking for DeepSORT model at: {deepsort_model_path}")
            
            if not deepsort_model_path.exists():
                logger.warning(f"❌ DeepSORT model not found")
                if not self._download_deepsort_model(deepsort_model_path):
                    logger.error("Failed to download DeepSORT model")
                    logger.warning("API will run in limited mode without player tracking")
                    self.models_loaded = False
                    return
                # Verify the file was actually downloaded
                if not deepsort_model_path.exists():
                    logger.error("Download reported success but file not found")
                    logger.warning("API will run in limited mode without player tracking")
                    self.models_loaded = False
                    return
            
            # Verify file size is reasonable (should be at least 1MB)
            if deepsort_model_path.stat().st_size < 1_000_000:
                logger.error(f"DeepSORT model file is too small ({deepsort_model_path.stat().st_size} bytes). File may be corrupted.")
                logger.warning("API will run in limited mode without player tracking")
                self.models_loaded = False
                return
            
            logger.info(f"✓ DeepSORT model found ({deepsort_model_path.stat().st_size / 1024 / 1024:.1f} MB)")
            
            # Try to load DeepSORT tracker
            # Temporarily add path for imports
            path_added = False
            if birds_eye_view_path not in sys.path:
                sys.path.insert(0, birds_eye_view_path)
                path_added = True
            
            try:
                try:
            from elements.deep_sort import DEEPSORT
            self.deep_sort_tracker = DEEPSORT(
                        deepsort_config=str(deepsort_config)
                    )
                    logger.info("✓ DeepSORT tracker loaded successfully")
                except FileNotFoundError as e:
                    logger.error(f"❌ DeepSORT model file error: {e}")
                    logger.warning("API will run in limited mode without player tracking")
                    self.models_loaded = False
                    return
                except Exception as e:
                    logger.error(f"❌ Error loading DeepSORT tracker: {e}")
                    logger.warning("API will run in limited mode without player tracking")
                    self.models_loaded = False
                    return
            finally:
                # Remove path immediately after import
                if path_added and birds_eye_view_path in sys.path:
                    sys.path.remove(birds_eye_view_path)
            
            # Load Perspective Transform (optional - may fail on Windows due to FLANN library)
            logger.info("Loading Perspective Transform...")
            # Temporarily add path for imports
            path_added = False
            if birds_eye_view_path not in sys.path:
                sys.path.insert(0, birds_eye_view_path)
                path_added = True
            
            try:
                try:
            from elements.perspective_transform import Perspective_Transform
            self.perspective_transform = Perspective_Transform()
                    logger.info("✓ Perspective Transform loaded successfully")
                except ImportError as e:
                    if "FLANN" in str(e) or "pyflann" in str(e):
                        logger.warning("⚠ Perspective Transform unavailable (FLANN library issue)")
                        logger.warning("   This is common on Windows. Video analysis will work without bird's-eye view transform.")
                        logger.warning("   To fix: FLANN requires C++ compilation. For now, continuing without it.")
                        self.perspective_transform = None
                    else:
                        raise
                except Exception as e:
                    logger.warning(f"⚠ Perspective Transform failed to load: {e}")
                    logger.warning("   Video analysis will work without bird's-eye view transform.")
                    self.perspective_transform = None
            finally:
                # Remove path immediately after import
                if path_added and birds_eye_view_path in sys.path:
                    sys.path.remove(birds_eye_view_path)
            
            # Models are loaded if we have at least YOLO and DeepSORT (Perspective Transform is optional)
            self.models_loaded = True
            logger.info("=" * 60)
            logger.info("✅ ALL MODELS LOADED SUCCESSFULLY!")
            logger.info("Video analysis endpoint is now FULLY OPERATIONAL")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ ERROR LOADING MODELS: {e}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
            logger.warning("API will run in limited mode without CV models")
            logger.info("Check the error above and ensure all dependencies are installed")
            self.models_loaded = False
    
    def get_detector(self):
        """Get YOLO detector"""
        return self.yolo_detector
    
    def get_tracker(self):
        """Get DeepSORT tracker"""
        return self.deep_sort_tracker
    
    def get_perspective_transform(self):
        """Get perspective transform"""
        return self.perspective_transform
    
    def is_ready(self) -> bool:
        """Check if models are ready"""
        return self.models_loaded
