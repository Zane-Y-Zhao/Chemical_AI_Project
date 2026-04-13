from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score, recall_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from torch.utils.data import DataLoader, Dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models import TransformerModel


@dataclass
class FoldMetrics:
    fold: int
    accuracy: float
    macro_f1: float
    macro_recall: float


class SequenceDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray):
        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.x)

    def __getitem__(self, idx: int):
        return self.x[idx], self.y[idx]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cross-validate Transformer on TE_processed.csv")
    parser.add_argument("--input", type=str, default="t-pre/TE_processed.csv")
    parser.add_argument("--window-size", type=int, default=20)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-windows", type=int, default=0, help="Optional cap for window samples (0 means all)")
    parser.add_argument("--out-json", type=str, default="runs/te_transformer/cv_metrics.json")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_data(csv_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Input file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    label_col = "STATUS" if "STATUS" in df.columns else df.columns[-1]

    x_df = df.drop(columns=[label_col])
    non_numeric = x_df.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric:
        x_df = x_df.drop(columns=non_numeric)

    y_raw = df[label_col].to_numpy()
    y = LabelEncoder().fit_transform(y_raw)
    x = x_df.to_numpy(dtype=np.float32)
    return x, y


def build_windows(features: np.ndarray, labels: np.ndarray, window_size: int) -> Tuple[np.ndarray, np.ndarray]:
    if len(features) < window_size:
        raise ValueError("Rows are fewer than window_size")

    x_list, y_list = [], []
    for i in range(len(features) - window_size + 1):
        end = i + window_size
        x_list.append(features[i:end])
        y_list.append(labels[end - 1])
    return np.asarray(x_list, dtype=np.float32), np.asarray(y_list, dtype=np.int64)


def train_one_fold(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    num_classes: int,
    batch_size: int,
    epochs: int,
    lr: float,
    device: torch.device,
) -> FoldMetrics:
    scaler = StandardScaler()
    scaler.fit(x_train.reshape(-1, x_train.shape[-1]))

    def transform(x: np.ndarray) -> np.ndarray:
        x2 = scaler.transform(x.reshape(-1, x.shape[-1]))
        return x2.reshape(x.shape).astype(np.float32)

    x_train = transform(x_train)
    x_val = transform(x_val)

    train_loader = DataLoader(SequenceDataset(x_train, y_train), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(SequenceDataset(x_val, y_val), batch_size=batch_size, shuffle=False)

    model = TransformerModel(
        input_size=x_train.shape[2],
        d_model=128,
        nhead=4,
        num_layers=2,
        output_size=num_classes,
        dropout=0.2,
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    best_state = None
    best_val_acc = -1.0

    for _ in range(epochs):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(device)
                logits = model(xb)
                preds = torch.argmax(logits, dim=1).cpu().numpy()
                all_preds.extend(preds.tolist())
                all_labels.extend(yb.numpy().tolist())

        val_acc = accuracy_score(all_labels, all_preds)
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for xb, yb in val_loader:
            xb = xb.to(device)
            logits = model(xb)
            preds = torch.argmax(logits, dim=1).cpu().numpy()
            all_preds.extend(preds.tolist())
            all_labels.extend(yb.numpy().tolist())

    return FoldMetrics(
        fold=-1,
        accuracy=float(accuracy_score(all_labels, all_preds)),
        macro_f1=float(f1_score(all_labels, all_preds, average="macro", zero_division=0)),
        macro_recall=float(recall_score(all_labels, all_preds, average="macro", zero_division=0)),
    )


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    x_raw, y_raw = load_data(Path(args.input))
    x_win, y_win = build_windows(x_raw, y_raw, args.window_size)

    if args.max_windows and 0 < args.max_windows < len(x_win):
        rng = np.random.default_rng(args.seed)
        keep_idx = rng.choice(len(x_win), size=args.max_windows, replace=False)
        keep_idx.sort()
        x_win = x_win[keep_idx]
        y_win = y_win[keep_idx]

    skf = StratifiedKFold(n_splits=args.n_splits, shuffle=True, random_state=args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    num_classes = int(np.unique(y_win).shape[0])

    fold_results = []
    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(x_win, y_win), start=1):
        metrics = train_one_fold(
            x_train=x_win[train_idx],
            y_train=y_win[train_idx],
            x_val=x_win[val_idx],
            y_val=y_win[val_idx],
            num_classes=num_classes,
            batch_size=args.batch_size,
            epochs=args.epochs,
            lr=args.lr,
            device=device,
        )
        metrics.fold = fold_idx
        fold_results.append(metrics)
        print(
            f"Fold {fold_idx}/{args.n_splits} | "
            f"acc={metrics.accuracy:.4f} | macro_f1={metrics.macro_f1:.4f} | macro_recall={metrics.macro_recall:.4f}"
        )

    accs = np.array([m.accuracy for m in fold_results], dtype=np.float64)
    f1s = np.array([m.macro_f1 for m in fold_results], dtype=np.float64)
    recalls = np.array([m.macro_recall for m in fold_results], dtype=np.float64)

    result = {
        "n_splits": args.n_splits,
        "window_size": args.window_size,
        "samples": int(len(x_win)),
        "class_count": num_classes,
        "folds": [m.__dict__ for m in fold_results],
        "summary": {
            "accuracy_mean": float(accs.mean()),
            "accuracy_std": float(accs.std(ddof=0)),
            "macro_f1_mean": float(f1s.mean()),
            "macro_f1_std": float(f1s.std(ddof=0)),
            "macro_recall_mean": float(recalls.mean()),
            "macro_recall_std": float(recalls.std(ddof=0)),
        },
    }

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Saved CV metrics to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
