"""
Dataset prep script - run locally before training.
Scans accident/normal video folders, runs YOLO + feature extraction,
and saves sequences.npy + labels.npy for training.

Usage:
  python prepare_dataset.py --accident-dir data/raw/accident --normal-dir data/raw/normal
"""

import os
import sys
import argparse
import numpy as np
import cv2
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(__file__))

from detector import VehicleDetector
from feature_extractor import FrameFeatureExtractor, SequenceBuffer
from config import SEQUENCE_LENGTH, FEATURE_DIM

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".MOV"}


def extract_sequences_from_video(
    video_path: str,
    detector: VehicleDetector,
    extractor: FrameFeatureExtractor,
    label: int,
    stride: int = 4,
) -> tuple:
    """Extract sliding window sequences from a single video file."""
    extractor.reset()
    seq_buffer = SequenceBuffer(sequence_length=SEQUENCE_LENGTH)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  [Warning] Cannot open: {video_path}")
        return np.array([]), np.array([])

    sequences = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_dets = detector.detect(frame, frame_idx)
        features = extractor.extract(frame_dets)
        seq_buffer.push(features)

        # Extract a sequence every `stride` frames
        if seq_buffer.is_ready() and frame_idx % stride == 0:
            sequences.append(seq_buffer.get_sequence())

        frame_idx += 1

    cap.release()

    if not sequences:
        return np.array([]), np.array([])

    seqs = np.array(sequences, dtype=np.float32)
    lbls = np.full(len(seqs), label, dtype=np.int64)
    return seqs, lbls


def prepare(accident_dir: str, normal_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    detector = VehicleDetector()
    extractor = FrameFeatureExtractor()

    all_sequences = []
    all_labels = []

    # --- Process accident videos ---
    accident_videos = [
        os.path.join(accident_dir, f)
        for f in os.listdir(accident_dir)
        if os.path.splitext(f)[1] in VIDEO_EXTENSIONS
    ]
    print(f"\n[Dataset] Processing {len(accident_videos)} accident videos...")
    for vpath in tqdm(accident_videos):
        seqs, lbls = extract_sequences_from_video(vpath, detector, extractor, label=1)
        if len(seqs) > 0:
            all_sequences.append(seqs)
            all_labels.append(lbls)

    # --- Process normal videos ---
    normal_videos = [
        os.path.join(normal_dir, f)
        for f in os.listdir(normal_dir)
        if os.path.splitext(f)[1] in VIDEO_EXTENSIONS
    ]
    print(f"\n[Dataset] Processing {len(normal_videos)} normal videos...")
    for vpath in tqdm(normal_videos):
        seqs, lbls = extract_sequences_from_video(vpath, detector, extractor, label=0)
        if len(seqs) > 0:
            all_sequences.append(seqs)
            all_labels.append(lbls)

    # --- Combine and save ---
    all_sequences = np.concatenate(all_sequences, axis=0)
    all_labels = np.concatenate(all_labels, axis=0)

    # Shuffle
    idx = np.random.permutation(len(all_sequences))
    all_sequences = all_sequences[idx]
    all_labels = all_labels[idx]

    seq_path = os.path.join(output_dir, "sequences.npy")
    lbl_path = os.path.join(output_dir, "labels.npy")

    np.save(seq_path, all_sequences)
    np.save(lbl_path, all_labels)

    print(f"\n[Dataset] Done!")
    print(f"  Total sequences:  {len(all_sequences)}")
    print(f"  Accident:         {all_labels.sum()}")
    print(f"  Normal:           {(all_labels == 0).sum()}")
    print(f"  Sequence shape:   {all_sequences[0].shape}")
    print(f"  Saved to:         {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare training dataset")
    parser.add_argument("--accident-dir", default="data/raw/accident")
    parser.add_argument("--normal-dir", default="data/raw/normal")
    parser.add_argument("--output-dir", default="data/processed")
    args = parser.parse_args()

    prepare(args.accident_dir, args.normal_dir, args.output_dir)
