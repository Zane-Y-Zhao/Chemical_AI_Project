from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import LabelEncoder, StandardScaler
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

from train_monitor import TrainMonitor


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
        seq_len = x.size(1)
        x = x + self.pe[:seq_len].unsqueeze(0)
        return self.dropout(x)


class TransformerModel(nn.Module):
    """Encoder-only 时序 Transformer，保留 look_back 序列输入范式。"""

    def __init__(
        self,
        input_size: int,
        d_model: int = 32,
        nhead: int = 2,
        num_layers: int = 1,
        output_size: int = 21,
        dropout: float = 0.4,
        dim_feedforward: int = 64,
    ):
        super().__init__()
        self.d_model = d_model

        # 正则化改造：输入层和嵌入层都加 BN，降低过拟合和训练抖动
        self.bn_input = nn.BatchNorm1d(input_size)
        self.embedding = nn.Linear(input_size, d_model)
        self.bn_embed = nn.BatchNorm1d(d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # 头部简化：减少冗余容量，保留分类能力
        self.head = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Dropout(dropout),
            nn.Linear(d_model, 32),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(32, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, T, F]
        b, t, f = x.shape

        x = self.bn_input(x.reshape(-1, f)).reshape(b, t, f)
        x = self.embedding(x)
        x = self.bn_embed(x.reshape(-1, self.d_model)).reshape(b, t, self.d_model)

        scale = torch.sqrt(torch.tensor(self.d_model, dtype=torch.float32, device=x.device))
        x = x * scale
        x = self.pos_encoder(x)
        x = self.transformer_encoder(x)

        x = x[:, -1, :]
        return self.head(x)


class TEDataset(Dataset):
    def __init__(
        self,
        x: np.ndarray,
        y: np.ndarray,
        augment: bool = False,
        noise_std: float = 0.0,
        feature_dropout: float = 0.0,
    ):
        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
        self.augment = augment
        self.noise_std = noise_std
        self.feature_dropout = feature_dropout

    def __len__(self) -> int:
        return len(self.x)

    def __getitem__(self, idx: int):
        x = self.x[idx]
        if self.augment:
            if self.noise_std > 0:
                x = x + torch.randn_like(x) * self.noise_std
            if self.feature_dropout > 0:
                # 轻量特征级dropout，增强泛化
                mask = (torch.rand_like(x) > self.feature_dropout).float()
                x = x * mask
        return x, self.y[idx]


class EMA:
    def __init__(self, model: nn.Module, decay: float = 0.999):
        self.decay = decay
        self.shadow = {
            name: parameter.detach().clone()
            for name, parameter in model.named_parameters()
            if parameter.requires_grad
        }

    @torch.no_grad()
    def update(self, model: nn.Module) -> None:
        for name, parameter in model.named_parameters():
            if not parameter.requires_grad:
                continue
            self.shadow[name].mul_(self.decay).add_(parameter.detach(), alpha=1.0 - self.decay)

    def apply_to(self, model: nn.Module) -> dict[str, torch.Tensor]:
        backup = {}
        for name, parameter in model.named_parameters():
            if not parameter.requires_grad:
                continue
            backup[name] = parameter.detach().clone()
            parameter.data.copy_(self.shadow[name].data)
        return backup

    def restore(self, model: nn.Module, backup: dict[str, torch.Tensor]) -> None:
        for name, parameter in model.named_parameters():
            if name in backup:
                parameter.data.copy_(backup[name].data)


@dataclass
class Config:
    data_path: str = "t-pre/TE_processed.csv"
    look_back: int = 20
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    batch_size: int = 128
    epochs: int = 40
    lr: float = 3e-4
    weight_decay: float = 1e-3
    d_model: int = 32
    nhead: int = 2
    num_layers: int = 1
    dropout: float = 0.4
    dim_feedforward: int = 64
    early_stop_patience: int = 8
    early_stop_min_delta: float = 1e-4
    grad_clip: float = 1.0
    seed: int = 42
    num_workers: int = 0
    max_rows: int = 0
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    curve_path: str = "logs/figure2_loss_accuracy.png"
    use_weighted_sampler: bool = True
    class_weight_power: float = 0.5
    min_train_samples_per_class: int = 16
    augment_noise_std: float = 0.01
    augment_feature_dropout: float = 0.03
    ema_decay: float = 0.999


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def detect_label_col(df: pd.DataFrame) -> str:
    if "label" in df.columns:
        return "label"
    if "STATUS" in df.columns:
        return "STATUS"
    return df.columns[-1]


def build_windows(features: np.ndarray, labels: np.ndarray, look_back: int) -> tuple[np.ndarray, np.ndarray]:
    if len(features) < look_back:
        raise ValueError(f"样本数({len(features)})小于look_back({look_back})")

    n = len(features) - look_back + 1
    x = np.asarray([features[i : i + look_back] for i in range(n)], dtype=np.float32)
    y = np.asarray([labels[i + look_back - 1] for i in range(n)], dtype=np.int64)
    return x, y


def split_group_time_series(
    df: pd.DataFrame,
    feature_cols: list[str],
    label_values: np.ndarray,
    look_back: int,
    train_ratio: float,
    val_ratio: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    数据层修复：按 source_file 分组，各组内保持时间顺序划分，避免
    1) 跨文件窗口拼接污染
    2) 某些 source/类别只出现在验证集导致“验证失效”
    """
    if "source_file" not in df.columns:
        full_x = df[feature_cols].to_numpy(dtype=np.float32)
        full_y = label_values
        x_win, y_win = build_windows(full_x, full_y, look_back)
        train_end = int(len(x_win) * train_ratio)
        val_end = int(len(x_win) * (train_ratio + val_ratio))
        return x_win[:train_end], y_win[:train_end], x_win[train_end:val_end], y_win[train_end:val_end]

    train_x_list: list[np.ndarray] = []
    train_y_list: list[np.ndarray] = []
    val_x_list: list[np.ndarray] = []
    val_y_list: list[np.ndarray] = []

    for _, group in df.groupby("source_file", sort=False):
        idx = group.index.to_numpy()
        gx = df.loc[idx, feature_cols].to_numpy(dtype=np.float32)
        gy = label_values[idx]

        if len(gx) < look_back + 2:
            continue

        x_win, y_win = build_windows(gx, gy, look_back)
        g_total = len(x_win)
        g_train_end = int(g_total * train_ratio)
        g_val_end = int(g_total * (train_ratio + val_ratio))

        # 保证每组 train/val 非空
        g_train_end = min(max(g_train_end, 1), g_total - 2)
        g_val_end = min(max(g_val_end, g_train_end + 1), g_total - 1)

        train_x_list.append(x_win[:g_train_end])
        train_y_list.append(y_win[:g_train_end])
        val_x_list.append(x_win[g_train_end:g_val_end])
        val_y_list.append(y_win[g_train_end:g_val_end])

    if not train_x_list or not val_x_list:
        raise ValueError("分组时序划分失败，请检查数据量或 look_back 设置")

    return (
        np.concatenate(train_x_list, axis=0),
        np.concatenate(train_y_list, axis=0),
        np.concatenate(val_x_list, axis=0),
        np.concatenate(val_y_list, axis=0),
    )


def load_data(cfg: Config):
    path = Path(cfg.data_path)
    if not path.exists():
        raise FileNotFoundError(f"找不到数据文件: {path.resolve()}")

    df = pd.read_csv(path)
    if cfg.max_rows > 0:
        df = df.head(cfg.max_rows)

    label_col = detect_label_col(df)

    feature_df = df.drop(columns=[label_col])
    non_numeric_cols = feature_df.select_dtypes(exclude=[np.number]).columns.tolist()
    # 保留 source_file 供分组切分使用，其它非数值列剔除
    drop_cols = [c for c in non_numeric_cols if c != "source_file"]
    if drop_cols:
        feature_df = feature_df.drop(columns=drop_cols)

    if "source_file" in feature_df.columns:
        numeric_feature_cols = [c for c in feature_df.columns if c != "source_file"]
    else:
        numeric_feature_cols = feature_df.columns.tolist()

    if len(numeric_feature_cols) == 0:
        raise ValueError("没有可用数值特征")

    raw_labels = df[label_col].to_numpy()
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(raw_labels)

    split_df = feature_df.copy()
    x_train, y_train, x_val, y_val = split_group_time_series(
        split_df,
        numeric_feature_cols,
        y,
        cfg.look_back,
        cfg.train_ratio,
        cfg.val_ratio,
    )

    scaler = StandardScaler()
    scaler.fit(x_train.reshape(-1, x_train.shape[-1]))

    def transform(x_arr: np.ndarray) -> np.ndarray:
        shape = x_arr.shape
        x2d = x_arr.reshape(-1, shape[-1])
        x2d = scaler.transform(x2d)
        return x2d.reshape(shape).astype(np.float32)

    x_train = transform(x_train)
    x_val = transform(x_val)

    # 数据修正：若验证集中存在训练未见类，从验证集迁移少量样本到训练集
    train_labels = set(np.unique(y_train).tolist())
    val_labels = set(np.unique(y_val).tolist())
    unseen = sorted(list(val_labels - train_labels))
    if unseen:
        move_indices = []
        for cls in unseen:
            cls_idx = np.where(y_val == cls)[0]
            take_n = min(max(cfg.min_train_samples_per_class, 1), len(cls_idx))
            move_indices.extend(cls_idx[:take_n].tolist())

        if move_indices:
            move_indices = np.array(sorted(set(move_indices)), dtype=np.int64)
            keep_mask = np.ones(len(y_val), dtype=bool)
            keep_mask[move_indices] = False

            x_train = np.concatenate([x_train, x_val[move_indices]], axis=0)
            y_train = np.concatenate([y_train, y_val[move_indices]], axis=0)
            x_val = x_val[keep_mask]
            y_val = y_val[keep_mask]

    info = {
        "label_col": label_col,
        "feature_count": x_train.shape[-1],
        "class_count": int(np.unique(y).shape[0]),
        "train_size": len(x_train),
        "val_size": len(x_val),
        "train_label_set": set(np.unique(y_train).tolist()),
        "val_label_set": set(np.unique(y_val).tolist()),
    }

    return x_train, y_train, x_val, y_val, info


def run_train_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    grad_clip: float,
) -> tuple[float, float]:
    model.train()
    total_loss = 0.0
    total_correct = 0
    total = 0

    use_amp = device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    for x, y in loader:
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)

        with torch.amp.autocast("cuda", enabled=use_amp):
            logits = model(x)
            loss = criterion(logits, y)

        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        scaler.step(optimizer)
        scaler.update()

        total_loss += loss.item() * x.size(0)
        total_correct += (logits.argmax(1) == y).sum().item()
        total += y.size(0)

    return total_loss / max(total, 1), total_correct / max(total, 1)


@torch.no_grad()
def run_val_epoch(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device) -> tuple[float, float]:
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total = 0

    for x, y in loader:
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)
        logits = model(x)
        loss = criterion(logits, y)

        total_loss += loss.item() * x.size(0)
        total_correct += (logits.argmax(1) == y).sum().item()
        total += y.size(0)

    return total_loss / max(total, 1), total_correct / max(total, 1)


def train(cfg: Config) -> None:
    set_seed(cfg.seed)

    x_train, y_train, x_val, y_val, info = load_data(cfg)

    device = torch.device(cfg.device)
    train_dataset = TEDataset(
        x_train,
        y_train,
        augment=True,
        noise_std=cfg.augment_noise_std,
        feature_dropout=cfg.augment_feature_dropout,
    )
    val_dataset = TEDataset(x_val, y_val, augment=False)

    train_counts = np.bincount(y_train, minlength=info["class_count"]).astype(np.float64)
    train_counts = np.maximum(train_counts, 1.0)
    class_weights_np = (train_counts.sum() / train_counts) ** cfg.class_weight_power
    class_weights_np = class_weights_np / class_weights_np.mean()
    class_weights = torch.tensor(class_weights_np, dtype=torch.float32, device=device)

    if cfg.use_weighted_sampler:
        sample_weights = class_weights_np[y_train]
        train_sampler = WeightedRandomSampler(
            weights=torch.tensor(sample_weights, dtype=torch.double),
            num_samples=len(sample_weights),
            replacement=True,
        )
        train_loader = DataLoader(
            train_dataset,
            batch_size=cfg.batch_size,
            sampler=train_sampler,
            num_workers=cfg.num_workers,
            pin_memory=(device.type == "cuda"),
        )
    else:
        train_loader = DataLoader(
            train_dataset,
            batch_size=cfg.batch_size,
            shuffle=True,
            num_workers=cfg.num_workers,
            pin_memory=(device.type == "cuda"),
        )

    val_loader = DataLoader(
        val_dataset,
        batch_size=cfg.batch_size,
        shuffle=False,
        num_workers=cfg.num_workers,
        pin_memory=(device.type == "cuda"),
    )

    model = TransformerModel(
        input_size=info["feature_count"],
        d_model=cfg.d_model,
        nhead=cfg.nhead,
        num_layers=cfg.num_layers,
        output_size=info["class_count"],
        dropout=cfg.dropout,
        dim_feedforward=cfg.dim_feedforward,
    ).to(device)

    # 训练策略优化：标签平滑 + AdamW + L2 + 降学习率
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05, weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay, betas=(0.9, 0.95))
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=2, min_lr=1e-6
    )
    ema = EMA(model, decay=cfg.ema_decay)

    monitor = TrainMonitor(model, device, log_dir="logs", model_dir="models")

    best_val_loss = float("inf")
    best_path = Path("models/best_overfit_fixed.pth")
    early_stop_count = 0

    print("=" * 80)
    print("Overfitting Fix Training")
    print(f"device: {device}")
    print(f"label_col: {info['label_col']}")
    print(f"feature_count: {info['feature_count']} | class_count: {info['class_count']}")
    print(f"train_size: {info['train_size']} | val_size: {info['val_size']}")
    unseen_in_train = info["val_label_set"] - info["train_label_set"]
    if unseen_in_train:
        print(f"[警告] 验证集存在训练未见类别: {sorted(list(unseen_in_train))}")
    else:
        print("[检查] 训练/验证类别覆盖一致")
    print(f"[class_weight] min={class_weights.min().item():.3f} max={class_weights.max().item():.3f}")

    for epoch in range(cfg.epochs):
        train_loss, train_acc = run_train_epoch(model, train_loader, criterion, optimizer, device, cfg.grad_clip)
        ema.update(model)

        # 用 EMA 权重做验证，通常更稳、更抗过拟合
        ema_backup = ema.apply_to(model)
        val_loss, val_acc = run_val_epoch(model, val_loader, criterion, device)
        ema.restore(model, ema_backup)

        monitor.log_epoch(epoch, train_loss, val_loss, train_acc, val_acc)
        scheduler.step(val_loss)

        if val_loss < best_val_loss - cfg.early_stop_min_delta:
            best_val_loss = val_loss
            torch.save(model.state_dict(), best_path)
            early_stop_count = 0
        else:
            early_stop_count += 1

        current_lr = optimizer.param_groups[0]["lr"]
        print(f"[lr] {current_lr:.2e} | best_val_loss={best_val_loss:.6f} | early_stop_count={early_stop_count}")

        if early_stop_count >= cfg.early_stop_patience:
            print(f"[Early Stopping] 连续 {cfg.early_stop_patience} 个epoch无改进，停止训练")
            break

    if best_path.exists():
        model.load_state_dict(torch.load(best_path, map_location=device))

    monitor.plot_curves(save_path=cfg.curve_path)
    print("=" * 80)
    print(f"FINAL_BEST_VAL_LOSS={best_val_loss:.6f}")
    print(f"CURVE_PATH={cfg.curve_path}")
    print(f"BEST_MODEL_PATH={best_path}")


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Overfitting-robust time-series Transformer training")
    parser.add_argument("--data-path", type=str, default="t-pre/TE_processed.csv")
    parser.add_argument("--look-back", type=int, default=20)
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--d-model", type=int, default=32)
    parser.add_argument("--nhead", type=int, default=2)
    parser.add_argument("--num-layers", type=int, default=1)
    parser.add_argument("--dropout", type=float, default=0.4)
    parser.add_argument("--dim-feedforward", type=int, default=64)
    parser.add_argument("--early-stop-patience", type=int, default=8)
    parser.add_argument("--early-stop-min-delta", type=float, default=1e-4)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--device", type=str, default=("cuda" if torch.cuda.is_available() else "cpu"))
    parser.add_argument("--curve-path", type=str, default="logs/figure2_loss_accuracy.png")
    parser.add_argument("--no-weighted-sampler", action="store_true")
    parser.add_argument("--class-weight-power", type=float, default=0.5)
    parser.add_argument("--min-train-samples-per-class", type=int, default=16)
    parser.add_argument("--augment-noise-std", type=float, default=0.01)
    parser.add_argument("--augment-feature-dropout", type=float, default=0.03)
    parser.add_argument("--ema-decay", type=float, default=0.999)

    args = parser.parse_args()
    return Config(
        data_path=args.data_path,
        look_back=args.look_back,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        batch_size=args.batch_size,
        epochs=args.epochs,
        lr=args.lr,
        weight_decay=args.weight_decay,
        d_model=args.d_model,
        nhead=args.nhead,
        num_layers=args.num_layers,
        dropout=args.dropout,
        dim_feedforward=args.dim_feedforward,
        early_stop_patience=args.early_stop_patience,
        early_stop_min_delta=args.early_stop_min_delta,
        grad_clip=args.grad_clip,
        seed=args.seed,
        num_workers=args.num_workers,
        max_rows=args.max_rows,
        device=args.device,
        curve_path=args.curve_path,
        use_weighted_sampler=(not args.no_weighted_sampler),
        class_weight_power=args.class_weight_power,
        min_train_samples_per_class=args.min_train_samples_per_class,
        augment_noise_std=args.augment_noise_std,
        augment_feature_dropout=args.augment_feature_dropout,
        ema_decay=args.ema_decay,
    )


def main() -> None:
    cfg = parse_args()
    train(cfg)


if __name__ == "__main__":
    main()
