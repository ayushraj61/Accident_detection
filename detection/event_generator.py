"""
Event generator - creates event payloads and saves video clips
when the classifier detects an accident.
"""

import cv2
import uuid
import json
import os
import numpy as np
from datetime import datetime, timezone
from collections import deque
from typing import Optional
from config import (
    ROLLING_BUFFER_SECONDS,
    CLIP_SECONDS_BEFORE,
    CLIP_SECONDS_AFTER,
    TARGET_FPS,
    CLIPS_OUTPUT_DIR,
)


class RollingFrameBuffer:
    """Keeps last N seconds of video frames in memory for clip extraction."""

    def __init__(self, fps: int = TARGET_FPS, buffer_seconds: int = ROLLING_BUFFER_SECONDS):
        max_frames = fps * buffer_seconds
        self._buffer: deque = deque(maxlen=max_frames)
        self.fps = fps

    def push(self, frame: np.ndarray):
        self._buffer.append(frame.copy())

    def get_pre_event_frames(self, seconds_before: int = CLIP_SECONDS_BEFORE) -> list:
        """Get frames from N seconds before the current moment."""
        num_frames = seconds_before * self.fps
        available = list(self._buffer)
        return available[-num_frames:] if len(available) >= num_frames else available


class EventGenerator:
    """Handles clip extraction and event payload creation."""

    def __init__(
        self,
        camera_id: str,
        camera_lat: float,
        camera_lng: float,
        fps: int = TARGET_FPS,
        clips_dir: str = CLIPS_OUTPUT_DIR,
    ):
        self.camera_id = camera_id
        self.camera_lat = camera_lat
        self.camera_lng = camera_lng
        self.fps = fps
        self.clips_dir = clips_dir
        os.makedirs(clips_dir, exist_ok=True)

        self.frame_buffer = RollingFrameBuffer(fps=fps)
        self._post_event_frames: list = []
        self._capturing_post: bool = False
        self._post_frames_needed: int = CLIP_SECONDS_AFTER * fps
        self._pending_event: Optional[dict] = None

    def push_frame(self, frame: np.ndarray):
        """Buffer every frame. Also collects post-event frames if capturing."""
        self.frame_buffer.push(frame)

        if self._capturing_post:
            self._post_event_frames.append(frame.copy())
            if len(self._post_event_frames) >= self._post_frames_needed:
                self._finalize_event()

    def generate_event(self, confidence: float, severity: str, frame_idx: int) -> dict:
        """Create an event payload and start collecting post-accident frames."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        event = {
            "event_id": event_id,
            "camera_id": self.camera_id,
            "timestamp": timestamp,
            "frame_idx": frame_idx,
            "confidence": confidence,
            "severity": severity,
            "location": {
                "lat": self.camera_lat,
                "lng": self.camera_lng,
            },
            "clip_path": None,      # Filled after post-event frames collected
            "status": "PENDING_CLIP",
        }

        # Store pre-event frames and start collecting post-event
        self._pending_event = event
        self._pre_event_frames = self.frame_buffer.get_pre_event_frames()
        self._post_event_frames = []
        self._capturing_post = True

        print(f"[EventGenerator] Accident detected! event_id={event_id}, confidence={confidence:.3f}, severity={severity}")

        return event

    def _finalize_event(self):
        """Called internally once post-event frames are collected."""
        if self._pending_event is None:
            return

        all_frames = self._pre_event_frames + self._post_event_frames
        clip_path = self._save_clip(all_frames, self._pending_event["event_id"])

        self._pending_event["clip_path"] = clip_path
        self._pending_event["status"] = "READY"

        # Save JSON payload to disk
        json_path = os.path.join(
            self.clips_dir,
            f"{self._pending_event['event_id']}.json"
        )
        with open(json_path, "w") as f:
            json.dump(self._pending_event, f, indent=2)

        print(f"[EventGenerator] Clip saved: {clip_path}")
        print(f"[EventGenerator] Event payload: {json_path}")

        # Reset
        self._capturing_post = False
        self._pending_event = None
        self._pre_event_frames = []
        self._post_event_frames = []

    def _save_clip(self, frames: list, event_id: str) -> str:
        """Encode frames as H.264 mp4 and save to disk."""
        if not frames:
            return ""

        clip_path = os.path.join(self.clips_dir, f"{event_id}.mp4")
        h, w = frames[0].shape[:2]

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(clip_path, fourcc, self.fps, (w, h))

        for frame in frames:
            writer.write(frame)

        writer.release()
        return clip_path
