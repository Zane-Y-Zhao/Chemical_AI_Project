from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix, f1_score, recall_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from torch.utils.data import DataLoader, Dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models import TransformerModel


@dataclass
class SplitData:
    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray


class SequenceDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray):
        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.x)

    def __getitem__(self, idx: int):
        return self.x[idx], self.y[idx]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Transformer time-series model on TE_processed.csv")
    parser.add_argument("--input", type=str, default="t-pre/TE_processed.csv", help="Path to TE_processed.csv")
    parser.add_argument("--window-size", type=int, default=20, help="Sliding window size")
    parser.add_argument("--train-ratio", type=float, default=0.7, help="Train split ratio")
    parser.add_argument("--val-ratio", type=float, default=0.15, help="Validation split ratio")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--epochs", type=int, default=20, help="Training epochs")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--d-model", type=int, default=128, help="Transformer d_model")
    parser.add_argument("--nhead", type=int, default=4, help="Transformer attention heads")
    parser.add_argument("--num-layers", type=int, default=2, help="Transformer encoder layers")
    parser.add_argument("--dropout", type=float, default=0.2, help="Dropout")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--out-dir", type=str, default="runs/te_transformer", help="Output directory")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_and_prepare_data(csv_path: Path) -> Tuple[np.ndarray, np.ndarray, list[str], str]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Input file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.shape[1] < 2:
        raise ValueError("CSV must contain at least one feature column and one label column.")

    label_col = "STATUS" if "STATUS" in df.columns else df.columns[-1]
    feature_df = df.drop(columns=[label_col])

    # Drop metadata / non-numeric columns from model features.
    non_numeric_cols = feature_df.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric_cols:
        feature_df = feature_df.drop(columns=non_numeric_cols)

    if feature_df.empty:
        raise ValueError("No numeric feature columns found after filtering.")

    raw_labels = df[label_col].to_numpy()
    if pd.isna(raw_labels).any():
        raise ValueError("Label column contains missing values.")

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(raw_labels)
    x = feature_df.to_numpy(dtype=np.float32)

    return x, y, feature_df.columns.tolist(), label_col


def build_windows(features: np.ndarray, labels: np.ndarray, window_size: int) -> Tuple[np.ndarray, np.ndarray]:
    if len(features) < window_size:
        raise ValueError("Number of rows is smaller than window size.")

    sample_count = len(features) - window_size + 1
    x_list = []
    y_list = []
    for i in range(sample_count):
        end = i + window_size
        x_list.append(features[i:end])
        y_list.append(labels[end - 1])

    return np.asarray(x_list, dtype=np.float32), np.asarray(y_list, dtype=np.int64)


def split_by_time(x: np.ndarray, y: np.ndarray, train_ratio: float, val_ratio: float) -> SplitData:
    if train_ratio <= 0 or val_ratio <= 0 or (train_ratio + val_ratio) >= 1:
        raise ValueError("train_ratio and val_ratio must be > 0 and sum to < 1.")

    total = len(x)
    train_end = int(total * train_ratio)
    val_end = int(total * (train_ratio + val_ratio))

    if train_end < 1 or val_end <= train_end or val_end >= total:
        raise ValueError("Split sizes are invalid. Adjust train_ratio/val_ratio.")

    x_train, y_train = x[:train_end], y[:train_end]
    x_val, y_val = x[train_end:val_end], y[train_end:val_end]
    x_test, y_test = x[val_end:], y[val_end:]

    return SplitData(x_train, y_train, x_val, y_val, x_test, y_test)


def standardize_with_train_only(split: SplitData) -> Tuple[SplitData, StandardScaler]:
    scaler = StandardScaler()
    train_shape = split.x_train.shape

    x_train_2d = split.x_train.reshape(-1, train_shape[-1])
    scaler.fit(x_train_2d)

    def transform(x_arr: np.ndarray) -> np.ndarray:
        original_shape = x_arr.shape
        x_2d = x_arr.reshape(-1, original_shape[-1])
        x_scaled = scaler.transform(x_2d)
        return x_scaled.reshape(original_shape).astype(np.float32)

    return (
        SplitData(
            transform(split.x_train),
            split.y_train,
            transform(split.x_val),
            split.y_val,
            transform(split.x_test),
            split.y_test,
        ),
        scaler,
    )


def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device):
    model.eval()
    total_loss = 0.0
    total = 0
    correct = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for x_batch, y_batch in loader:
            x_batch = x_batch.to(device)
            y_batch = y_batch.to(device)

            outputs = model(x_batch)
            loss = criterion(outputs, y_batch)

            total_loss += loss.item() * x_batch.size(0)
            preds = torch.argmax(outputs, dim=1)
            total += y_batch.size(0)
            correct += (preds == y_batch).sum().item()

            all_preds.extend(preds.cpu().numpy().tolist())
            all_labels.extend(y_batch.cpu().numpy().tolist())

    avg_loss = total_loss / max(total, 1)
    acc = correct / max(total, 1)
    return avg_loss, acc, np.asarray(all_labels), np.asarray(all_preds)


def plot_curves(train_losses, val_losses, train_accs, val_accs, save_path: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    ax1.plot(train_losses, label="Train Loss")
    ax1.plot(val_losses, label="Val Loss")
    ax1.set_title("Loss Curve")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.legend()
    ax1.grid(True)

    ax2.plot(train_accs, label="Train Acc")
    ax2.plot(val_accs, label="Val Acc")
    ax2.set_title("Accuracy Curve")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close()


def plot_confusion_matrix(cm: np.ndarray, save_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set_title("Confusion Matrix")
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")

    thresh = cm.max() / 2.0 if cm.size else 0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], "d"), ha="center", va="center", color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    x_raw, y_raw, feature_cols, label_col = load_and_prepare_data(Path(args.input))
    x_win, y_win = build_windows(x_raw, y_raw, args.window_size)
    split = split_by_time(x_win, y_win, args.train_ratio, args.val_ratio)
    split, scaler = standardize_with_train_only(split)

    train_loader = DataLoader(SequenceDataset(split.x_train, split.y_train), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(SequenceDataset(split.x_val, split.y_val), batch_size=args.batch_size, shuffle=False)
    test_loader = DataLoader(SequenceDataset(split.x_test, split.y_test), batch_size=args.batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    num_classes = int(np.unique(y_raw).shape[0])

    model = TransformerModel(
        input_size=split.x_train.shape[2],
        d_model=args.d_model,
        nhead=args.nhead,
        num_layers=args.num_layers,
        output_size=num_classes,
        dropout=args.dropout,
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    train_losses = []
    val_losses = []
    train_accs = []
    val_accs = []

    best_val_acc = -1.0
    best_model_path = out_dir / "best_transformer_te.pth"

    print("=" * 80)
    print("TE Transformer Training")
    print("=" * 80)
    print(f"Input CSV: {Path(args.input).resolve()}")
    print(f"Label column: {label_col}")
    print(f"Feature count: {len(feature_cols)}")
    print(f"Class count: {num_classes}")
    print(f"Window size: {args.window_size}")
    print(f"Train/Val/Test samples: {len(split.x_train)}/{len(split.x_val)}/{len(split.x_test)}")
    print(f"Train label distribution: {dict(Counter(split.y_train.tolist()))}")
    print(f"Val label distribution: {dict(Counter(split.y_val.tolist()))}")
    print(f"Test label distribution: {dict(Counter(split.y_test.tolist()))}")

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        total = 0
        correct = 0

        for x_batch, y_batch in train_loader:
            x_batch = x_batch.to(device)
            y_batch = y_batch.to(device)

            optimizer.zero_grad()
            outputs = model(x_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * x_batch.size(0)
            preds = torch.argmax(outputs, dim=1)
            total += y_batch.size(0)
            correct += (preds == y_batch).sum().item()

        train_loss = running_loss / max(total, 1)
        train_acc = correct / max(total, 1)
        val_loss, val_acc, _, _ = evaluate(model, val_loader, criterion, device)

        train_losses.append(train_loss)
        val_losses.append(val_loss)
        train_accs.append(train_acc)
        val_accs.append(val_acc)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), best_model_path)

        print(
            f"Epoch {epoch:03d}/{args.epochs} | "
            f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
            f"Train Acc: {train_acc:.4f} | Val Acc: {val_acc:.4f}"
        )

    model.load_state_dict(torch.load(best_model_path, map_location=device))
    test_loss, test_acc, test_labels, test_preds = evaluate(model, test_loader, criterion, device)

    test_recall = recall_score(test_labels, test_preds, average="macro", zero_division=0)
    test_f1 = f1_score(test_labels, test_preds, average="macro", zero_division=0)
    cm = confusion_matrix(test_labels, test_preds)
    report = classification_report(test_labels, test_preds, digits=4, zero_division=0)

    curves_path = out_dir / "training_curves.png"
    cm_path = out_dir / "confusion_matrix.png"
    metrics_path = out_dir / "metrics.json"
    report_path = out_dir / "classification_report.txt"
    scaler_path = out_dir / "standard_scaler.npy"

    plot_curves(train_losses, val_losses, train_accs, val_accs, curves_path)
    plot_confusion_matrix(cm, cm_path)

    metrics = {
        "test_loss": float(test_loss),
        "test_accuracy": float(test_acc),
        "test_macro_recall": float(test_recall),
        "test_macro_f1": float(test_f1),
        "best_val_accuracy": float(best_val_acc),
        "window_size": int(args.window_size),
        "feature_count": int(len(feature_cols)),
        "class_count": int(num_classes),
    }

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with report_path.open("w", encoding="utf-8") as f:
        f.write(report)

    # Save scaler statistics for reproducibility.
    np.save(scaler_path, np.vstack([scaler.mean_, scaler.scale_]))

    print("=" * 80)
    print("Test Results")
    print("=" * 80)
    print(f"Test Loss: {test_loss:.4f}")
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Test Macro Recall: {test_recall:.4f}")
    print(f"Test Macro F1: {test_f1:.4f}")
    print("Classification report:")
    print(report)
    print("Saved artifacts:")
    print(f"- Best model: {best_model_path.resolve()}")
    print(f"- Metrics: {metrics_path.resolve()}")
    print(f"- Curves: {curves_path.resolve()}")
    print(f"- Confusion matrix: {cm_path.resolve()}")
    print(f"- Class report: {report_path.resolve()}")
    print(f"- Scaler stats: {scaler_path.resolve()}")


if __name__ == "__main__":
    main()
