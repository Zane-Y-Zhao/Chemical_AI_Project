from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge AutoResearch resume logs and plot a combined curve")
    parser.add_argument("--logs-dir", type=str, default="logs")
    parser.add_argument("--pattern", type=str, default="train_log_autoresearch_resume_*.txt")
    parser.add_argument("--output", type=str, default="logs/autoresearch_combined_curve.png")
    parser.add_argument("--merged-csv", type=str, default="logs/autoresearch_combined_history.csv")
    return parser.parse_args()


def load_rows(log_files: list[Path]) -> list[dict[str, str]]:
    rows: dict[int, dict[str, str]] = {}
    for log_file in log_files:
        with log_file.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                epoch = int(row["epoch"])
                rows[epoch] = row
    return [rows[epoch] for epoch in sorted(rows)]


def plot(rows: list[dict[str, str]], output: Path) -> None:
    epochs = [int(row["epoch"]) for row in rows]
    train_losses = [float(row["train_loss"]) for row in rows]
    val_losses = [float(row["val_loss"]) for row in rows]
    train_accs = [float(row["train_acc"]) for row in rows]
    val_accs = [float(row["val_acc"]) for row in rows]

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.suptitle("AutoResearch Transformer 全量训练曲线", fontsize=13)

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
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=300, bbox_inches="tight")
    plt.close()


def save_merged_csv(rows: list[dict[str, str]], merged_csv: Path) -> None:
    merged_csv.parent.mkdir(parents=True, exist_ok=True)
    with merged_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", "train_loss", "val_loss", "train_acc", "val_acc", "lr"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    logs_dir = Path(args.logs_dir)
    log_files = sorted(logs_dir.glob(args.pattern))

    if not log_files:
        raise FileNotFoundError(f"No logs found in {logs_dir.resolve()} matching {args.pattern}")

    rows = load_rows(log_files)
    output = Path(args.output)
    merged_csv = Path(args.merged_csv)

    save_merged_csv(rows, merged_csv)
    plot(rows, output)

    print("=" * 80)
    print("AutoResearch Combined Curve")
    print("=" * 80)
    print(f"log_files: {len(log_files)}")
    for log_file in log_files:
        print(f"- {log_file.resolve()}")
    print(f"merged_csv: {merged_csv.resolve()}")
    print(f"curve_path: {output.resolve()}")
    print(f"epochs_merged: {len(rows)}")
    print(f"epoch_range: {rows[0]['epoch']} -> {rows[-1]['epoch']}")


if __name__ == "__main__":
    main()