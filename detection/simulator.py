"""
Edge device simulator - runs the full detection pipeline on a video file.

Usage:
  python simulator.py --video path/to/video.mp4 --camera-id CAM_001
  python simulator.py --video path/to/video.mp4 --show
"""

import cv2
import argparse
import sys
import os
import time
import json
import datetime
from config import CLIPS_OUTPUT_DIR

try:
    import redis
except ImportError:
    redis = None

sys.path.insert(0, os.path.dirname(__file__))

from detector import VehicleDetector
from feature_extractor import FrameFeatureExtractor, SequenceBuffer
from temporal_classifier import AccidentClassifier
from event_generator import EventGenerator
from config import (
    SEQUENCE_LENGTH,
    TARGET_FPS,
    MODEL_SAVE_PATH,
)


def run_simulation(
    video_path: str,
    camera_id: str = "CAM_001",
    camera_lat: float = 28.6139,
    camera_lng: float = 77.2090,
    show: bool = False,
    model_path: str = MODEL_SAVE_PATH,
):
    """Main loop - reads video, runs YOLO + features + LSTM, publishes alerts."""

    print(f"\n{'='*60}")
    print("  AI-AIDERS Edge Simulator")
    print(f"{'='*60}")
    print(f"  Video:     {video_path}")
    print(f"  Camera:    {camera_id} ({camera_lat}, {camera_lng})")
    print(f"  Model:     {model_path}")
    print(f"{'='*60}\n")

    # --- Initialize pipeline components ---
    detector = VehicleDetector()
    extractor = FrameFeatureExtractor()
    seq_buffer = SequenceBuffer(sequence_length=SEQUENCE_LENGTH)
    classifier = AccidentClassifier(model_path=model_path)
    event_gen = EventGenerator(
        camera_id=camera_id,
        camera_lat=camera_lat,
        camera_lng=camera_lng,
    )

    # --- Connect to Redis ---
    r_client = None
    if redis is not None:
        try:
            r_client = redis.Redis(host='127.0.0.1', port=6379, db=0)
            r_client.ping()
            print("[Simulator] Connected to Redis Pub/Sub")
        except redis.ConnectionError:
            print("[Simulator] WARNING: Redis not found on localhost:6379. Alerts won't be broadcasted.")
            r_client = None
    else:
        print("[Simulator] WARNING: 'redis' pip package missing. Alerts won't be broadcasted.")

    # --- Open video ---
    if video_path == "0":
        print("[Simulator] Attaching to local hardware webcam (Device 0)...")
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(video_path)
        
    if not cap.isOpened():
        print(f"[Error] Cannot open video source: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps is None or fps > 120:
        fps = TARGET_FPS
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    stream_type = "Endless Live Feed" if video_path == "0" else f"{total_frames} frames"
    print(f"[Simulator] Video Source: {stream_type} @ ~{fps:.1f} fps")

    frame_idx = 0
    events_detected = []
    cooldown_frames = 0         # Prevent duplicate events for same accident
    COOLDOWN = int(fps * 10)    # 10 second cooldown after detection to avoid duplicates

    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # --- Push frame to event generator buffer ---
        event_gen.push_frame(frame)

        # --- YOLO detection ---
        frame_dets = detector.detect(frame, frame_idx)

        # --- Extract features ---
        features = extractor.extract(frame_dets)
        seq_buffer.push(features)

        # --- Draw detections on frame (optional) ---
        if show:
            frame = _draw_detections(frame, frame_dets)

        # --- Run LSTM when sequence is full ---
        if seq_buffer.is_ready() and cooldown_frames == 0:
            sequence = seq_buffer.get_sequence()
            result = classifier.predict(sequence)

            if result["is_accident"]:
                event = event_gen.generate_event(
                    confidence=result["confidence"],
                    severity=result["severity"],
                    frame_idx=frame_idx,
                )
                events_detected.append(event)
                cooldown_frames = COOLDOWN

                # --- NEW: Collect 5s of post-event frames before sending alert ---
                print(f"[Simulator] Accident detected! Buffering 5s of aftermath...")
                post_frames = []
                post_needed = int(fps * 5)
                
                # Capture next 5s
                for _ in range(post_needed):
                    ret, post_f = cap.read()
                    if not ret: break
                    post_frames.append(post_f)
                    frame_idx += 1
                
                # Combine pre and post
                pre_frames = event_gen.frame_buffer.get_pre_event_frames(5)
                all_frames = pre_frames + post_frames

                # --- Try to save video clip ---
                clip_filename = None
                thumbnail_b64 = None
                try:
                    import base64
                    if all_frames and len(all_frames) > 10:
                        os.makedirs(CLIPS_OUTPUT_DIR, exist_ok=True)
                        raw_path = os.path.join(CLIPS_OUTPUT_DIR, f"{event['event_id']}_raw.mp4")
                        final_path = os.path.join(CLIPS_OUTPUT_DIR, f"{event['event_id']}.mp4")
                        clip_filename = f"{event['event_id']}.mp4"
                        
                        h, w = all_frames[0].shape[:2]
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        writer = cv2.VideoWriter(raw_path, fourcc, int(fps), (w, h))
                        for f in all_frames:
                            writer.write(f)
                        writer.release()
                        
                        import subprocess as clip_proc
                        try:
                            clip_proc.run([
                                "ffmpeg", "-y", "-i", raw_path,
                                "-c:v", "libx264", "-preset", "ultrafast",
                                "-crf", "28", "-movflags", "+faststart",
                                "-pix_fmt", "yuv420p", final_path
                            ], capture_output=True, timeout=15)
                            if os.path.exists(raw_path): os.remove(raw_path)
                            print(f"[Simulator] Saved H.264 highlight ({len(all_frames)} frames): {final_path}")
                        except Exception as ffmpeg_err:
                            if os.path.exists(raw_path): os.rename(raw_path, final_path)
                        
                        impact_frame = pre_frames[-1] if pre_frames else all_frames[0]
                        _, jpeg_buf = cv2.imencode('.jpg', impact_frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                        thumbnail_b64 = base64.b64encode(jpeg_buf.tobytes()).decode('utf-8')
                except Exception as clip_err:
                    print(f"[Simulator] Clip encoding failed: {clip_err}")

                # --- Broadcast to Backend ---
                if r_client:
                    payload = {
                        "id": event["event_id"],
                        "severity": result["severity"],
                        "confidence": float(result["confidence"]),
                        "lat": camera_lat,
                        "lng": camera_lng,
                        "status": "pending",
                        "video_clip_url": f"/clips/{clip_filename}" if clip_filename else None,
                        "thumbnail_b64": thumbnail_b64,
                        "created_at": datetime.datetime.utcnow().isoformat()
                    }
                    r_client.publish("emergency_alerts", json.dumps(payload))
                    print(f"[Simulator] Alert published to Redis: {event['event_id']}")

                if show:
                    _draw_alert(frame, result)

        if cooldown_frames > 0:
            cooldown_frames -= 1

        # --- Show frame ---
        if show:
            progress = f"Frame {frame_idx}/{total_frames}"
            cv2.putText(frame, progress, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow("AI-AIDERS Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        frame_idx += 1

    # --- Cleanup ---
    cap.release()
    if show:
        cv2.destroyAllWindows()

    elapsed = time.time() - start_time

    # --- Summary ---
    print(f"\n{'='*60}")
    print("  SIMULATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Frames processed: {frame_idx}")
    print(f"  Time taken:       {elapsed:.1f}s")
    print(f"  Processing speed: {frame_idx/elapsed:.1f} fps")
    print(f"  Events detected:  {len(events_detected)}")
    for i, evt in enumerate(events_detected, 1):
        print(f"\n  Event {i}:")
        print(f"    ID:         {evt['event_id']}")
        print(f"    Timestamp:  {evt['timestamp']}")
        print(f"    Confidence: {evt['confidence']}")
        print(f"    Severity:   {evt['severity']}")
        print(f"    Clip:       {evt.get('clip_path', 'generating...')}")
    print(f"{'='*60}\n")

    return events_detected


def _draw_detections(frame, frame_dets) -> object:
    """Draw bounding boxes on frame."""
    import cv2
    h, w = frame.shape[:2]
    for det in frame_dets.detections:
        x1 = int(det.x1 * w)
        y1 = int(det.y1 * h)
        x2 = int(det.x2 * w)
        y2 = int(det.y2 * h)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{det.class_name} {det.confidence:.2f}"
        cv2.putText(frame, label, (x1, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return frame


def _draw_alert(frame, result: dict):
    """Draw red ACCIDENT DETECTED overlay."""
    import cv2
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 200), -1)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
    text = f"ACCIDENT DETECTED  conf={result['confidence']:.2f}  severity={result['severity']}"
    cv2.putText(frame, text, (10, 50),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-AIDERS Edge Simulator")
    parser.add_argument("--video", required=True, help="Path to input video file")
    parser.add_argument("--camera-id", default="CAM_001", help="Camera identifier")
    parser.add_argument("--lat", type=float, default=28.6139, help="Camera GPS latitude")
    parser.add_argument("--lng", type=float, default=77.2090, help="Camera GPS longitude")
    parser.add_argument("--show", action="store_true", help="Show live detection window")
    parser.add_argument("--model", default=MODEL_SAVE_PATH, help="Path to LSTM model weights")

    args = parser.parse_args()

    run_simulation(
        video_path=args.video,
        camera_id=args.camera_id,
        camera_lat=args.lat,
        camera_lng=args.lng,
        show=args.show,
        model_path=args.model,
    )
