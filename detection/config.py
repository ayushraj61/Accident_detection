"""
AI-AIDERS — Detection Module Configuration
All tunable parameters in one place.
"""

# YOLOv8 config
YOLO_MODEL_PATH = "../yolov8n.pt"   # swap to yolov8x.pt for higher accuracy
YOLO_CONFIDENCE_THRESHOLD = 0.25
YOLO_IOU_THRESHOLD = 0.45

# Vehicle class IDs in COCO dataset (what YOLO is trained on)
VEHICLE_CLASS_IDS = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Temporal classifier config
SEQUENCE_LENGTH = 16        # Number of frames per sequence fed to LSTM
FEATURE_DIM = 9             # Number of features extracted per frame
LSTM_HIDDEN_SIZE = 64
LSTM_NUM_LAYERS = 2
LSTM_DROPOUT = 0.3

# Accident detection thresholds
ACCIDENT_CONFIDENCE_THRESHOLD = 0.45   # Lowered to 0.45 for better sensitivity in demo
SEVERITY_THRESHOLDS = {
    "low":    (0.55, 0.65),
    "medium": (0.65, 0.80),
    "high":   (0.80, 1.00),
}

# Rolling buffer config
ROLLING_BUFFER_SECONDS = 60     # How many seconds of frames to keep in memory
CLIP_SECONDS_BEFORE = 5         # Seconds before event to include in clip
CLIP_SECONDS_AFTER = 5          # Seconds after event to include in clip
TARGET_FPS = 25

# Paths
MODEL_SAVE_PATH = "models/saved/lstm_classifier.pth"
CLIPS_OUTPUT_DIR = "../backend/data/clips"
