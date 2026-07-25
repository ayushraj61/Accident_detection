"""
Vehicle detector using YOLOv8.
Filters only vehicle classes from COCO and returns normalized bounding boxes.
"""

import numpy as np
from dataclasses import dataclass
from typing import List
from ultralytics import YOLO
from config import YOLO_MODEL_PATH, YOLO_CONFIDENCE_THRESHOLD, VEHICLE_CLASS_IDS


@dataclass
class Detection:
    """Single vehicle detection in a frame."""
    class_id: int
    class_name: str
    confidence: float
    x1: float       # Normalized bounding box (0-1)
    y1: float
    x2: float
    y2: float
    track_id: int = -1  # Unique ID from YOLO tracker, -1 if no tracking

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2

    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        return self.width / (self.height + 1e-6)


@dataclass
class FrameDetections:
    """All vehicle detections in a single frame."""
    frame_idx: int
    detections: List[Detection]

    @property
    def count(self) -> int:
        return len(self.detections)

    @property
    def is_empty(self) -> bool:
        return len(self.detections) == 0


class VehicleDetector:
    """Runs YOLOv8 and keeps only vehicle detections."""

    def __init__(self, model_path: str = YOLO_MODEL_PATH):
        print(f"[Detector] Loading YOLOv8 from {model_path}")
        self.model = YOLO(model_path)
        self.model.fuse()   # Fuse layers for faster inference
        print("[Detector] Model ready.")

    def detect(self, frame: np.ndarray, frame_idx: int = 0) -> FrameDetections:
        """Run detection on a single frame and return filtered vehicle detections."""
        h, w = frame.shape[:2]
        results = self.model.track(
            frame,
            persist=True,
            conf=YOLO_CONFIDENCE_THRESHOLD,
            verbose=False
        )[0]

        detections = []
        for box in results.boxes:
            class_id = int(box.cls[0])
            if class_id not in VEHICLE_CLASS_IDS:
                continue    # Skip non-vehicles

            # Normalize bounding box to 0-1 range
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            track_id = int(box.id[0]) if box.id is not None else -1

            detections.append(Detection(
                class_id=class_id,
                class_name=VEHICLE_CLASS_IDS[class_id],
                confidence=float(box.conf[0]),
                x1=x1 / w,
                y1=y1 / h,
                x2=x2 / w,
                y2=y2 / h,
                track_id=track_id,
            ))

        return FrameDetections(frame_idx=frame_idx, detections=detections)


def compute_iou(d1: Detection, d2: Detection) -> float:
    """Compute Intersection over Union between two detections."""
    ix1 = max(d1.x1, d2.x1)
    iy1 = max(d1.y1, d2.y1)
    ix2 = min(d1.x2, d2.x2)
    iy2 = min(d1.y2, d2.y2)

    intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    union = d1.area + d2.area - intersection

    return intersection / (union + 1e-6)


def max_pairwise_iou(detections: List[Detection]) -> float:
    """Find the max IoU between any two vehicles. High overlap = possible collision."""
    if len(detections) < 2:
        return 0.0

    max_iou = 0.0
    for i in range(len(detections)):
        for j in range(i + 1, len(detections)):
            iou = compute_iou(detections[i], detections[j])
            max_iou = max(max_iou, iou)

    return max_iou
