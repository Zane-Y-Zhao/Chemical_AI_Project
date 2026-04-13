from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import LabelEncoder, StandardScaler
from torch.utils.data import DataLoader, Dataset


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-torch.log(torch.tensor(10000.0)) / d_model))
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[: x.size(1)].unsqueeze(0)
        return self.dropout(x)


class TransformerModel(nn.Module):
    def __init__(
        self,
        input_size: int,
        d_model: int = 64,
        nhead: int = 2,
        num_layers: int = 1,
        output_size: int = 21,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.d_model = d_model
        self.embedding = nn.Linear(input_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=128,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.embedding(x) * torch.sqrt(torch.tensor(self.d_model, dtype=torch.float32, device=x.device))
        x = self.pos_encoder(x)
        x = self.transformer_encoder(x)
        x = x[:, -1, :]
        return self.fc(x)


class SequenceDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray):
        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.x)

    def __getitem__(self, idx: int):
        return self.x[idx], self.y[idx]


@dataclass
class SplitData:
    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resume AutoResearch Transformer training without re-initialization")
    parser.add_argument("--ckpt-path", type=str, default="last_checkpoint_autoresearch.pth")
    parser.add_argument("--best-path", type=str, default="best_model_autoresearch.pth")
    parser.add_argument("--extra-epochs", type=int, default=100)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_and_prepare_data(csv_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Input file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    label_col = "STATUS" if "STATUS" in df.columns else df.columns[-1]
    feature_df = df.drop(columns=[label_col])

    non_numeric_cols = feature_df.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric_cols:
        feature_df = feature_df.drop(columns=non_numeric_cols)

    if feature_df.empty:
        raise ValueError("No numeric feature columns found after filtering")

    y_raw = df[label_col].to_numpy()
    y = LabelEncoder().fit_transform(y_raw)
    x = feature_df.to_numpy(dtype=np.float32)
    return x, y


def build_windows(features: np.ndarray, labels: np.ndarray, look_back: int) -> Tuple[np.ndarray, np.ndarray]:
    if len(features) < look_back:
        raise ValueError(f"Rows ({len(features)}) are smaller than look_back ({look_back})")

    x_list, y_list = [], []
    for i in range(len(features) - look_back + 1):
        end = i + look_back
        x_list.append(features[i:end])
        y_list.append(labels[end - 1])

    return np.asarray(x_list, dtype=np.float32), np.asarray(y_list, dtype=np.int64)


def split_by_time(x: np.ndarray, y: np.ndarray, train_ratio: float, val_ratio: float) -> SplitData:
    total = len(x)
    train_end = int(total * train_ratio)
    val_end = int(total * (train_ratio + val_ratio))

    if train_end <= 0 or val_end <= train_end or val_end >= total:
        raise ValueError("Invalid split produced by train_ratio/val_ratio")

    return SplitData(
        x_train=x[:train_end],
        y_train=y[:train_end],
        x_val=x[train_end:val_end],
        y_val=y[train_end:val_end],
    )


def standardize_with_train(split: SplitData) -> SplitData:
    scaler = StandardScaler()
    scaler.fit(split.x_train.reshape(-1, split.x_train.shape[-1]))

    def transform(x_arr: np.ndarray) -> np.ndarray:
        shape = x_arr.shape
        x2 = scaler.transform(x_arr.reshape(-1, shape[-1]))
        return x2.reshape(shape).astype(np.float32)

    return SplitData(
        x_train=transform(split.x_train),
        y_train=split.y_train,
        x_val=transform(split.x_val),
        y_val=split.y_val,
    )


def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device) -> Tuple[float, float]:
    model.eval()
    total_loss = 0.0
    total = 0
    correct = 0

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

    return total_loss / max(total, 1), correct / max(total, 1)


def plot_training_curve(log_path: Path, curve_path: Path) -> None:
    epochs = []
    train_losses = []
    val_losses = []
    train_accs = []
    val_accs = []

    with log_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            epochs.append(int(row["epoch"]))
            train_losses.append(float(row["train_loss"]))
            val_losses.append(float(row["val_loss"]))
            train_accs.append(float(row["train_acc"]))
            val_accs.append(float(row["val_acc"]))

    if not epochs:
        return

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.suptitle("AutoResearch Transformer 训练曲线", fontsize=13)

    ax1.plot(epochs, train_losses, label="Train Loss")
    ax1.plot(epochs, val_losses, label="Val Loss")
    ax1.set_title("Loss Curve")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.grid(True)
    ax1.legend()

    ax2.plot(epochs, train_accs, label="Train Acc")
    ax2.plot(epochs, val_accs, label="Val Acc")
    ax2.set_title("Accuracy Curve")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.grid(True)
    ax2.legend()

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    curve_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(curve_path, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    ckpt_path = Path(args.ckpt_path)
    best_path = Path(args.best_path)

    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path.resolve()}")

    checkpoint = torch.load(ckpt_path, map_location="cpu")
    if not isinstance(checkpoint, dict) or "model_state" not in checkpoint:
        raise ValueError("Invalid checkpoint format; expected dict with model_state")

    cfg = checkpoint.get("config", {})
    data_path = Path(cfg.get("data_path", "t-pre/TE_processed.csv"))
    look_back = int(cfg.get("look_back", 20))
    train_ratio = float(cfg.get("train_ratio", 0.7))
    val_ratio = float(cfg.get("val_ratio", 0.15))
    batch_size = int(cfg.get("batch_size", 128))
    lr = float(cfg.get("lr", 1e-3))
    weight_decay = float(cfg.get("weight_decay", 1e-4))
    d_model = int(cfg.get("d_model", 64))
    nhead = int(cfg.get("nhead", 2))
    num_layers = int(cfg.get("num_layers", 1))
    dropout = float(cfg.get("dropout", 0.3))

    device = torch.device(args.device if args.device == "cpu" or torch.cuda.is_available() else "cpu")

    x_raw, y_raw = load_and_prepare_data(data_path)
    x_win, y_win = build_windows(x_raw, y_raw, look_back)
    split = split_by_time(x_win, y_win, train_ratio, val_ratio)
    split = standardize_with_train(split)

    train_loader = DataLoader(SequenceDataset(split.x_train, split.y_train), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(SequenceDataset(split.x_val, split.y_val), batch_size=batch_size, shuffle=False)

    num_classes = int(np.unique(y_win).shape[0])
    model = TransformerModel(
        input_size=split.x_train.shape[2],
        d_model=d_model,
        nhead=nhead,
        num_layers=num_layers,
        output_size=num_classes,
        dropout=dropout,
    ).to(device)

    model.load_state_dict(checkpoint["model_state"], strict=True)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    if "optimizer_state" in checkpoint and checkpoint["optimizer_state"]:
        optimizer.load_state_dict(checkpoint["optimizer_state"])

    start_epoch = int(checkpoint.get("epoch", 0)) + 1
    end_epoch = start_epoch + int(args.extra_epochs) - 1
    best_val_loss = float(checkpoint.get("best_val_loss", float("inf")))
    best_epoch = int(checkpoint.get("best_epoch", checkpoint.get("epoch", 0)))

    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"train_log_autoresearch_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    curve_path = log_dir / f"autoresearch_resume_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    with log_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "val_loss", "train_acc", "val_acc", "lr"]) 

    print("=" * 80)
    print("AutoResearch Resume Training")
    print(f"device: {device}")
    print(f"checkpoint: {ckpt_path.resolve()}")
    print(f"resume epoch: {start_epoch}")
    print(f"target epoch: {end_epoch}")
    print(f"train_size: {len(split.x_train)} | val_size: {len(split.x_val)}")
    print(f"log_file: {log_path.resolve()}")
    print(f"curve_file: {curve_path.resolve()}")

    try:
        for epoch in range(start_epoch, end_epoch + 1):
            model.train()
            total_loss = 0.0
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

                total_loss += loss.item() * x_batch.size(0)
                preds = torch.argmax(outputs, dim=1)
                total += y_batch.size(0)
                correct += (preds == y_batch).sum().item()

            train_loss = total_loss / max(total, 1)
            train_acc = correct / max(total, 1)
            val_loss, val_acc = evaluate(model, val_loader, criterion, device)
            current_lr = optimizer.param_groups[0]["lr"]

            with log_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([epoch, f"{train_loss:.6f}", f"{val_loss:.6f}", f"{train_acc:.6f}", f"{val_acc:.6f}", f"{current_lr:.8f}"])

            print(
                f"Epoch {epoch:03d} | "
                f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
                f"Train Acc: {train_acc:.4f} | Val Acc: {val_acc:.4f} | LR: {current_lr:.2e}"
            )

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch
                torch.save(
                    {
                        "epoch": epoch,
                        "model_state": model.state_dict(),
                        "optimizer_state": optimizer.state_dict(),
                        "best_val_loss": best_val_loss,
                        "best_epoch": best_epoch,
                        "config": cfg,
                    },
                    best_path,
                )
                print(f"✅ Best model updated at epoch {epoch}, val_loss={best_val_loss:.6f}")

            torch.save(
                {
                    "epoch": epoch,
                    "model_state": model.state_dict(),
                    "optimizer_state": optimizer.state_dict(),
                    "best_val_loss": best_val_loss,
                    "best_epoch": best_epoch,
                    "config": cfg,
                },
                ckpt_path,
            )
    except KeyboardInterrupt:
        torch.save(
            {
                "epoch": epoch if "epoch" in locals() else start_epoch - 1,
                "model_state": model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
                "best_val_loss": best_val_loss,
                "best_epoch": best_epoch,
                "config": cfg,
            },
            ckpt_path,
        )
        print("\n[Interrupted] Current checkpoint has been saved.")

    plot_training_curve(log_path, curve_path)
    print("=" * 80)
    print(f"Resume training finished: {start_epoch} -> {min(end_epoch, int(torch.load(ckpt_path, map_location='cpu').get('epoch', end_epoch)))}")
    print(f"best_val_loss: {best_val_loss:.6f} at epoch {best_epoch}")
    print(f"best_model_path: {best_path.resolve()}")
    print(f"checkpoint_path: {ckpt_path.resolve()}")
    print(f"log_path: {log_path.resolve()}")
    print(f"curve_path: {curve_path.resolve()}")


if __name__ == "__main__":
    main()
