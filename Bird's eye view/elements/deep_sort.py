import torch
import os
import numpy as np
from pathlib import Path
from deep_sort_pytorch.utils.parser import get_config
from deep_sort_pytorch.deep_sort import DeepSort
from elements.assets import draw_boxes

class DEEPSORT():
    def __init__(self, deepsort_config):
        cfg = get_config()
        cfg.merge_from_file(deepsort_config)
        
        # Resolve the model path relative to the Bird's eye view directory
        # The config has "weights/deepsort_model.t7" which should be relative to Bird's eye view
        model_path = cfg.DEEPSORT.REID_CKPT
        if not os.path.isabs(model_path):
            # Get the Bird's eye view directory (parent of elements directory)
            birds_eye_view_dir = Path(__file__).resolve().parent.parent
            model_path = str(birds_eye_view_dir / model_path)
            # Update the config with the absolute path
            cfg.DEEPSORT.REID_CKPT = model_path
        
        # Verify the model file exists
        if not os.path.exists(model_path):
            error_msg = (
                f"DeepSORT model file not found at: {model_path}\n"
                f"Please download the DeepSORT checkpoint (ckpt.t7) and place it at the above path.\n"
                f"Common sources:\n"
                f"  - https://drive.google.com/uc?id=1_qwTWdzT9dWNudpusgKavj_4elGgbkUN\n"
                f"  - Search for 'deep_sort_pytorch checkpoint.t7' online"
            )
            raise FileNotFoundError(error_msg)
        
        self.deepsort = DeepSort(cfg.DEEPSORT.REID_CKPT,
                        max_dist=cfg.DEEPSORT.MAX_DIST, min_confidence=cfg.DEEPSORT.MIN_CONFIDENCE,
                        nms_max_overlap=cfg.DEEPSORT.NMS_MAX_OVERLAP, max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
                        max_age=cfg.DEEPSORT.MAX_AGE, n_init=cfg.DEEPSORT.N_INIT, nn_budget=cfg.DEEPSORT.NN_BUDGET,
                        use_cuda=True)

        print('DeepSort model loaded!')
    
    
    def detection_to_deepsort(self, objects, im0):
        xywh_bboxs = []
        confs = []

        # Adapt detections to deep sort input format
        for obj in objects:
            if obj['label'] == 'player':
                xyxy = [obj['bbox'][0][0], obj['bbox'][0][1], obj['bbox'][1][0], obj['bbox'][1][1]]
                conf = obj['score']
                # to deep sort format
                x_c, y_c, bbox_w, bbox_h = self.xyxy_to_xywh(*xyxy)
                xywh_obj = [x_c, y_c, bbox_w, bbox_h]
                xywh_bboxs.append(xywh_obj)
                confs.append([conf])

        # Handle empty detections case
        if len(xywh_bboxs) == 0:
            # Return empty outputs if no detections
            return np.array([], dtype=np.float32).reshape(0, 5)
        
        # Ensure proper 2D shape: (N, 4) for bboxes and (N, 1) for confidences
        xywhs = torch.Tensor(xywh_bboxs)
        confss = torch.Tensor(confs)
        
        # Ensure 2D shape
        if xywhs.dim() == 1:
            xywhs = xywhs.unsqueeze(0)
        if confss.dim() == 1:
            confss = confss.unsqueeze(0)
        
        if xywhs.shape[1] != 4:
            # Reshape if needed
            xywhs = xywhs.view(-1, 4)

        # pass detections to deepsort
        outputs = self.deepsort.update(xywhs, confss, im0)

        # draw boxes for visualization
        if len(outputs) > 0:
            bbox_xyxy = outputs[:, :4]
            identities = outputs[:, -1]
            draw_boxes(im0, bbox_xyxy, identities)
        
        return outputs
    

    def xyxy_to_xywh(self, *xyxy):
        """" Calculates the relative bounding box from absolute pixel values. """
        bbox_left = min([xyxy[0], xyxy[2]])
        bbox_top = min([xyxy[1], xyxy[3]])
        bbox_w = abs(xyxy[0] - xyxy[2])
        bbox_h = abs(xyxy[1] - xyxy[3])
        x_c = (bbox_left + bbox_w / 2)
        y_c = (bbox_top + bbox_h / 2)
        w = bbox_w
        h = bbox_h
        return x_c, y_c, w, h