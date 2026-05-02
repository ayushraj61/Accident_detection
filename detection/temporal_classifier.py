"""
AI-AIDERS — LSTM Temporal Classifier

Takes a sequence of 16 frame feature vectors → outputs accident probability.
This is the model we train on Google Colab.

Architecture:
  Input:  (batch, 16 frames, 9 features)
  LSTM:   2 layers, hidden_size=64
  Output: (batch, 2) → [not_accident, accident]
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from config import (
    FEATURE_DIM,
    SEQUENCE_LENGTH,
    LSTM_HIDDEN_SIZE,
    LSTM_NUM_LAYERS,
    LSTM_DROPOUT,
    ACCIDENT_CONFIDENCE_THRESHOLD,
    MODEL_SAVE_PATH,
)


class AccidentLSTM(nn.Module):
    """
    LSTM-based binary classifier: accident vs non-accident.

    Why LSTM over simple MLP?
    A single frame can't tell accident from hard braking.
    LSTM sees the SEQUENCE — the pattern over time — which is
    what distinguishes a collision from a normal event.
    """

    def __init__(
        self,
        input_size: int = FEATURE_DIM,
        hidden_size: int = LSTM_HIDDEN_SIZE,
        num_layers: int = LSTM_NUM_LAYERS,
        dropout: float = LSTM_DROPOUT,
    ):
        super().__init__()

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,          # Input shape: (batch, seq, features)
            dropout=dropout if num_layers > 1 else 0.0,
            bidirectional=False,       # Unidirectional — we process real-time
        )

        # Attention layer — weights important frames more
        self.attention = nn.Linear(hidden_size, 1)

        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 2),          # Binary: [not_accident, accident]
        )

        self._init_weights()

    def _init_weights(self):
        """Xavier initialization for stable training."""
        for name, param in self.lstm.named_parameters():
            if "weight" in name:
                nn.init.xavier_uniform_(param)
            elif "bias" in name:
                nn.init.zeros_(param)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Tensor of shape (batch_size, seq_len, feature_dim)

        Returns:
            logits: Tensor of shape (batch_size, 2)
        """
        lstm_out, _ = self.lstm(x)
        # lstm_out: (batch, seq_len, hidden_size)

        # Attention: which frames matter most?
        attn_weights = F.softmax(self.attention(lstm_out), dim=1)
        # attn_weights: (batch, seq_len, 1)

        context = (attn_weights * lstm_out).sum(dim=1)
        # context: (batch, hidden_size)

        return self.classifier(context)

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Return softmax probabilities."""
        with torch.no_grad():
            logits = self.forward(x)
            return F.softmax(logits, dim=1)


class AccidentClassifier:
    """
    Inference wrapper for AccidentLSTM.
    Loads the trained model and runs inference on sequences.
    Falls back to heuristic IoU-based detection if model is untrained.
    """

    def __init__(self, model_path: str = MODEL_SAVE_PATH, device: str = "auto"):
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.model = AccidentLSTM()
        self._model_trained = self._load(model_path)
        self.model.to(self.device)
        self.model.eval()
        
        if self._model_trained:
            print(f"[Classifier] Trained LSTM loaded on {self.device}")
        else:
            print(f"[Classifier] Using HEURISTIC fallback (IoU + velocity analysis)")

    def _load(self, path: str) -> bool:
        """Returns True if a real trained model was loaded."""
        try:
            checkpoint = torch.load(path, map_location="cpu")
            self.model.load_state_dict(checkpoint["model_state_dict"])
            print(f"[Classifier] Weights loaded from {path}")
            return True
        except (FileNotFoundError, RuntimeError, KeyError):
            print(f"[Classifier] WARNING: No valid trained model at {path}.")
            print("[Classifier] Will use heuristic fallback for accident detection.")
            return False

    def predict(self, sequence: np.ndarray) -> dict:
        """
        Run inference on a sequence of frame features.
        Uses trained LSTM if available, otherwise falls back to heuristic analysis.
        """
        if self._model_trained:
            return self._lstm_predict(sequence)
        else:
            return self._heuristic_predict(sequence)

    def _lstm_predict(self, sequence: np.ndarray) -> dict:
        """LSTM-based prediction (original logic)."""
        x = torch.FloatTensor(sequence).unsqueeze(0).to(self.device)
        probs = self.model.predict_proba(x)
        accident_prob = float(probs[0, 1])

        is_accident = accident_prob >= ACCIDENT_CONFIDENCE_THRESHOLD
        severity = self._get_severity(accident_prob) if is_accident else None

        return {
            "is_accident": is_accident,
            "confidence": round(accident_prob, 4),
            "severity": severity,
        }

    def _heuristic_predict(self, sequence: np.ndarray) -> dict:
        """
        Heuristic-based accident detection using extracted feature vectors.
        
        Feature indices (from feature_extractor.py):
          0: vehicle_count (normalized 0-1)
          1: max_iou (collision indicator — HIGH = vehicles overlapping!)
          2: avg_confidence
          3: velocity_mean
          4: velocity_max  
          5: acceleration (sudden deceleration = crash)
          6: aspect_ratio_variance (vehicle deformation)
          7: scene_coverage
          8: new_stationary_count (vehicles that stopped moving)
        
        Accident signature:
          - High IoU in recent frames (vehicles physically overlapping)
          - Sudden velocity drop (moving → stopped)
          - High acceleration spike (sudden deceleration)
          - Increased stationary count after motion
        """
        # Analyze the last 8 frames (most recent half of the sequence)
        recent = sequence[-8:]
        
        max_iou_values = recent[:, 1]       # Feature 1: max IoU
        velocity_values = recent[:, 3]      # Feature 3: velocity mean
        accel_values = recent[:, 5]         # Feature 5: acceleration
        stationary_values = recent[:, 8]    # Feature 8: stationary count
        
        # --- Collision indicators ---
        peak_iou = float(np.max(max_iou_values))
        avg_iou = float(np.mean(max_iou_values))
        peak_accel = float(np.max(accel_values))
        avg_stationary = float(np.mean(stationary_values))
        
        # Velocity drop: compare first half vs second half of the window
        early_vel = float(np.mean(velocity_values[:4]))
        late_vel = float(np.mean(velocity_values[4:]))
        velocity_drop = max(0, early_vel - late_vel)
        
        # --- Score the accident likelihood ---
        score = 0.0
        
        # High IoU is the strongest signal (vehicles overlapping = collision)  
        if peak_iou > 0.25:
            score += 0.5
        elif peak_iou > 0.12:
            score += 0.35
        elif peak_iou > 0.04:
            score += 0.15
            
        # Sudden deceleration
        if peak_accel > 0.3:
            score += 0.2
        elif peak_accel > 0.15:
            score += 0.1
            
        # Velocity drop (moving → stopped)
        if velocity_drop > 0.2:
            score += 0.2
        elif velocity_drop > 0.1:
            score += 0.1
            
        # Vehicles became stationary after movement
        if avg_stationary > 0.3:
            score += 0.15
        elif avg_stationary > 0.1:
            score += 0.05
        
        # Average IoU sustained over multiple frames
        if avg_iou > 0.1:
            score += 0.1
            
        # Clamp to 0-1
        confidence = min(score, 0.99)
        is_accident = confidence >= ACCIDENT_CONFIDENCE_THRESHOLD
        severity = self._get_severity(confidence) if is_accident else None
        
        if confidence > 0.3:
            print(f"[Heuristic] IoU={peak_iou:.3f} accel={peak_accel:.3f} vel_drop={velocity_drop:.3f} "
                  f"stationary={avg_stationary:.3f} → score={confidence:.3f} {'🚨 ACCIDENT' if is_accident else ''}")
        
        return {
            "is_accident": is_accident,
            "confidence": round(confidence, 4),
            "severity": severity,
        }

    def _get_severity(self, confidence: float) -> str:
        from config import SEVERITY_THRESHOLDS
        for level, (low, high) in SEVERITY_THRESHOLDS.items():
            if low <= confidence < high:
                return level
        return "high"
