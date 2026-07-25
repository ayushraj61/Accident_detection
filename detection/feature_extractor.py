"""
Feature extraction from YOLO detections.

Converts per-frame detections into a 9-value feature vector
that captures things like vehicle overlap, velocity, acceleration, etc.
These features are what the LSTM actually learns from.
"""

import numpy as np
from typing import List, Optional
from collections import deque
from detector import FrameDetections, Detection, max_pairwise_iou
from config import FEATURE_DIM, SEQUENCE_LENGTH


class FrameFeatureExtractor:
    """Extracts a 9-dim feature vector from each frame's detections."""

    def __init__(self):
        self._prev_centers: dict = {}   # Vehicle centers in prev frame by track_id
        self._prev_velocity: float = 0.0                  # Avg velocity of previous frame

    def reset(self):
        """Call at start of each new video."""
        self._prev_centers.clear()
        self._prev_velocity = 0.0

    def extract(self, frame_dets: FrameDetections) -> np.ndarray:
        """Extract 9 features from one frame's detections."""
        dets = frame_dets.detections
        features = np.zeros(FEATURE_DIM, dtype=np.float32)

        # --- Feature 0: Vehicle count (normalized) ---
        features[0] = min(len(dets), 10) / 10.0

        # --- Feature 1: Max pairwise IoU ---
        features[1] = max_pairwise_iou(dets)

        # --- Feature 2: Average detection confidence ---
        if dets:
            features[2] = np.mean([d.confidence for d in dets])

        # --- Features 3, 4, 5: Velocity and acceleration ---
        curr_tracked_centers = {d.track_id: (d.center_x, d.center_y) for d in dets if d.track_id != -1}

        if self._prev_centers and curr_tracked_centers:
            velocity_mean, velocity_max = self._compute_velocity(
                self._prev_centers, curr_tracked_centers
            )
            acceleration = abs(velocity_mean - self._prev_velocity)
        else:
            velocity_mean = 0.0
            velocity_max = 0.0
            acceleration = 0.0

        features[3] = min(velocity_mean, 1.0)
        features[4] = min(velocity_max, 1.0)
        features[5] = min(acceleration, 1.0)

        # Update state
        self._prev_centers = curr_tracked_centers
        self._prev_velocity = velocity_mean

        # --- Feature 6: Aspect ratio variance ---
        if len(dets) >= 2:
            ratios = [d.aspect_ratio for d in dets]
            features[6] = min(float(np.var(ratios)), 1.0)

        # --- Feature 7: Scene coverage ---
        if dets:
            total_area = sum(d.area for d in dets)
            features[7] = min(total_area, 1.0)

        # --- Feature 8: Stationary vehicle ratio ---
        if dets and self._prev_centers:
            stationary = self._count_stationary(curr_tracked_centers, threshold=0.01)
            features[8] = stationary / max(len(dets), 1)

        return features

    def _get_centers(self, dets: List[Detection]) -> np.ndarray:
        """Get center coordinates of all detections as array."""
        if not dets:
            return np.zeros((0, 2), dtype=np.float32)
        return np.array([[d.center_x, d.center_y] for d in dets], dtype=np.float32)

    def _compute_velocity(self, prev_centers: dict, curr_centers: dict):
        """Compute avg and max velocity using tracked vehicle positions."""
        velocities = []
        for track_id, curr_center in curr_centers.items():
            if track_id in prev_centers:
                prev = prev_centers[track_id]
                dist = np.linalg.norm(np.array(curr_center) - np.array(prev))
                velocities.append(float(dist))

        if not velocities:
            return 0.0, 0.0

        return float(np.mean(velocities)), float(np.max(velocities))

    def _count_stationary(self, curr_centers: dict, threshold: float) -> int:
        """Count tracked vehicles with near-zero velocity."""
        if not self._prev_centers or not curr_centers:
            return 0

        count = 0
        for track_id, curr_center in curr_centers.items():
            if track_id in self._prev_centers:
                prev = self._prev_centers[track_id]
                dist = np.linalg.norm(np.array(curr_center) - np.array(prev))
                if dist < threshold:
                    count += 1
        return count


class SequenceBuffer:
    """Sliding window buffer. Collects SEQUENCE_LENGTH frames then yields to LSTM."""

    def __init__(self, sequence_length: int = SEQUENCE_LENGTH):
        self.sequence_length = sequence_length
        self._buffer: deque = deque(maxlen=sequence_length)

    def push(self, features: np.ndarray):
        """Add a frame's features to the buffer."""
        self._buffer.append(features)

    def is_ready(self) -> bool:
        """True when buffer has enough frames for a full sequence."""
        return len(self._buffer) == self.sequence_length

    def get_sequence(self) -> np.ndarray:
        """Return current buffer contents as a numpy array."""
        return np.array(list(self._buffer), dtype=np.float32)

    def reset(self):
        self._buffer.clear()
