"""
AI-AIDERS — LSTM Training Script

Run this on Google Colab (free T4 GPU).
Trains the AccidentLSTM on extracted feature sequences.

Before running:
  1. Prepare dataset using prepare_dataset.py (run locally)
  2. Upload data/processed/ folder to Colab or Google Drive
  3. Run this script on Colab

Output:
  models/saved/lstm_classifier.pth  — trained weights
  models/saved/training_metrics.json — accuracy, loss curves
"""

import os
import sys
import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from sklearn.metrics import classification_report, confusion_matrix

sys.path.insert(0, os.path.dirname(__file__))
from temporal_classifier import AccidentLSTM
from config import (
    FEATURE_DIM,
    SEQUENCE_LENGTH,
    LSTM_HIDDEN_SIZE,
    LSTM_NUM_LAYERS,
    LSTM_DROPOUT,
    MODEL_SAVE_PATH,
)

# Training config
BATCH_SIZE = 32
EPOCHS = 50
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
TRAIN_SPLIT = 0.8
PATIENCE = 8            # Early stopping patience
DATA_DIR = "data/processed"


class AccidentDataset(Dataset):
    """
    Loads preprocessed feature sequences from disk.

    Expected structure:
      data/processed/
        sequences.npy     — shape (N, SEQUENCE_LENGTH, FEATURE_DIM)
        labels.npy        — shape (N,) — 0=normal, 1=accident
    """

    def __init__(self, data_dir: str = DATA_DIR):
        seq_path = os.path.join(data_dir, "sequences.npy")
        lbl_path = os.path.join(data_dir, "labels.npy")

        if not os.path.exists(seq_path) or not os.path.exists(lbl_path):
            raise FileNotFoundError(
                f"Dataset not found at {data_dir}.\n"
                "Run prepare_dataset.py first to generate sequences.npy and labels.npy"
            )

        self.sequences = np.load(seq_path).astype(np.float32)
        self.labels = np.load(lbl_path).astype(np.int64)

        assert len(self.sequences) == len(self.labels), "Sequence/label count mismatch"
        print(f"[Dataset] Loaded {len(self.sequences)} sequences")
        print(f"[Dataset] Accidents: {self.labels.sum()} | Normal: {(self.labels==0).sum()}")

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return (
            torch.FloatTensor(self.sequences[idx]),
            torch.LongTensor([self.labels[idx]])[0],
        )


def get_class_weights(dataset: AccidentDataset) -> torch.Tensor:
    """
    Compute class weights to handle imbalanced dataset.
    Accident clips are rare — we need to weight them higher.
    """
    labels = dataset.labels
    n_total = len(labels)
    n_accident = labels.sum()
    n_normal = n_total - n_accident

    weight_normal = n_total / (2 * n_normal)
    weight_accident = n_total / (2 * n_accident)

    print(f"[Training] Class weights — normal: {weight_normal:.3f}, accident: {weight_accident:.3f}")
    return torch.FloatTensor([weight_normal, weight_accident])


def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for sequences, labels in loader:
        sequences = sequences.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        logits = model(sequences)
        loss = criterion(logits, labels)
        loss.backward()

        # Gradient clipping — prevents exploding gradients in LSTM
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()

        total_loss += loss.item() * len(labels)
        preds = logits.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += len(labels)

    return total_loss / total, correct / total


def eval_epoch(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for sequences, labels in loader:
            sequences = sequences.to(device)
            labels = labels.to(device)

            logits = model(sequences)
            loss = criterion(logits, labels)

            total_loss += loss.item() * len(labels)
            preds = logits.argmax(dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(all_labels)
    accuracy = sum(p == l for p, l in zip(all_preds, all_labels)) / len(all_labels)

    return avg_loss, accuracy, all_preds, all_labels


def train(data_dir: str = DATA_DIR, save_path: str = MODEL_SAVE_PATH):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n[Training] Device: {device}")

    # --- Dataset ---
    dataset = AccidentDataset(data_dir)
    n_train = int(len(dataset) * TRAIN_SPLIT)
    n_val = len(dataset) - n_train
    train_ds, val_ds = random_split(dataset, [n_train, n_val])

    class_weights = get_class_weights(dataset).to(device)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    # --- Model ---
    model = AccidentLSTM(
        input_size=FEATURE_DIM,
        hidden_size=LSTM_HIDDEN_SIZE,
        num_layers=LSTM_NUM_LAYERS,
        dropout=LSTM_DROPOUT,
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"[Training] Model parameters: {total_params:,}")

    # --- Optimizer & Loss ---
    optimizer = Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", patience=3, factor=0.5)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    # --- Training Loop ---
    best_val_loss = float("inf")
    patience_counter = 0
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}

    print(f"\n[Training] Starting: {EPOCHS} epochs, batch={BATCH_SIZE}, lr={LEARNING_RATE}")
    print("-" * 60)

    for epoch in range(1, EPOCHS + 1):
        train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_acc, val_preds, val_labels = eval_epoch(model, val_loader, criterion, device)

        scheduler.step(val_loss)

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)

        print(f"Epoch {epoch:3d}/{EPOCHS} | "
              f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} | "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}")

        # --- Save best model ---
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_loss,
                "val_acc": val_acc,
                "config": {
                    "feature_dim": FEATURE_DIM,
                    "sequence_length": SEQUENCE_LENGTH,
                    "hidden_size": LSTM_HIDDEN_SIZE,
                    "num_layers": LSTM_NUM_LAYERS,
                }
            }, save_path)
            print(f"           ✓ Best model saved (val_loss={val_loss:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                print(f"\n[Training] Early stopping at epoch {epoch}")
                break

    # --- Final evaluation ---
    print("\n" + "=" * 60)
    print("FINAL EVALUATION ON VALIDATION SET")
    print("=" * 60)
    print(classification_report(val_labels, val_preds, target_names=["Normal", "Accident"]))
    print("Confusion Matrix:")
    print(confusion_matrix(val_labels, val_preds))

    # --- Save metrics ---
    metrics_path = os.path.join(os.path.dirname(save_path), "training_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(history, f, indent=2)
    print(f"\n[Training] Metrics saved: {metrics_path}")
    print(f"[Training] Model saved:   {save_path}")


if __name__ == "__main__":
    train()
