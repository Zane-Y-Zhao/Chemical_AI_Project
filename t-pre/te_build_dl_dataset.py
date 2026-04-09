"""将 TE_processed.csv 转换为深度学习接口格式。

功能:
1) 按时序滑窗构造样本 (X.shape = [样本数, 时间步, 特征数])。
2) 按时间顺序划分训练集和测试集。
3) 支持返回 numpy 数组或 torch tensor。

使用示例:
- 返回 numpy:
  python te_build_dl_dataset.py --return-type numpy

- 返回 torch:
  python te_build_dl_dataset.py --return-type torch
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


def build_time_series_windows(
    features: np.ndarray,
    labels: np.ndarray,
    window_size: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """按时序滑窗构造样本。

    说明:
    - 第 i 个样本的输入为 features[i : i + window_size]
    - 第 i 个样本的标签取窗口末尾时刻: labels[i + window_size - 1]
    """
    num_rows = features.shape[0]
    if num_rows < window_size:
        raise ValueError(
            f"数据行数({num_rows})小于窗口大小({window_size})，无法构造样本。"
        )

    sample_count = num_rows - window_size + 1
    x_list = []
    y_list = []

    for start in range(sample_count):
        end = start + window_size
        x_list.append(features[start:end])
        y_list.append(labels[end - 1])

    x = np.asarray(x_list, dtype=np.float32)
    y = np.asarray(y_list)
    return x, y


def split_train_test_by_time(
    x: np.ndarray,
    y: np.ndarray,
    test_ratio: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """按时间顺序划分训练集和测试集，不打乱顺序。"""
    if not (0.0 < test_ratio < 1.0):
        raise ValueError("test_ratio 必须在 (0, 1) 之间。")

    total = x.shape[0]
    test_size = int(total * test_ratio)
    test_size = max(1, test_size)
    train_size = total - test_size

    if train_size <= 0:
        raise ValueError("训练集为空，请减小 test_ratio 或增加数据量。")

    x_train = x[:train_size]
    y_train = y[:train_size]
    x_test = x[train_size:]
    y_test = y[train_size:]
    return x_train, y_train, x_test, y_test


def to_torch_if_needed(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    return_type: str,
):
    """按需将 numpy 转为 torch tensor。"""
    if return_type == "numpy":
        return x_train, y_train, x_test, y_test

    if return_type == "torch":
        try:
            import torch
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "未安装 torch，请先执行: pip install torch"
            ) from exc

        # 输入转 float32，标签按分类任务转 long
        x_train_t = torch.tensor(x_train, dtype=torch.float32)
        x_test_t = torch.tensor(x_test, dtype=torch.float32)
        y_train_t = torch.tensor(y_train, dtype=torch.long)
        y_test_t = torch.tensor(y_test, dtype=torch.long)
        return x_train_t, y_train_t, x_test_t, y_test_t

    raise ValueError("return_type 仅支持: numpy 或 torch")


def build_dl_dataset(
    input_csv: Path,
    window_size: int = 20,
    test_ratio: float = 0.2,
    return_type: str = "numpy",
):
    """主流程: 读取 CSV -> 滑窗 -> 划分 -> 返回数组/张量。"""
    if not input_csv.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_csv}")

    df = pd.read_csv(input_csv)
    if df.shape[1] < 2:
        raise ValueError("输入数据至少需要 2 列（特征 + 标签）。")

    # 按需求: 最后一列视为标签
    label_col = df.columns[-1]
    feature_df = df.iloc[:, :-1]
    label_series = df.iloc[:, -1]

    # 若前两列是来源信息（字符串），自动剔除，避免模型输入包含非数值列
    non_numeric_cols = feature_df.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric_cols:
        feature_df = feature_df.drop(columns=non_numeric_cols)

    if feature_df.empty:
        raise ValueError("特征列为空，无法构造模型输入。")

    features = feature_df.to_numpy(dtype=np.float32)
    labels = pd.to_numeric(label_series, errors="coerce").to_numpy()

    # 标签若有缺失值，直接报错提示
    if np.isnan(labels).any():
        raise ValueError("标签列存在无法转换为数值的内容，请先清洗标签列。")

    # 如果标签本质是整数类别，转成 int64 更适合分类任务
    if np.allclose(labels, np.round(labels)):
        labels = labels.astype(np.int64)

    x, y = build_time_series_windows(features, labels, window_size=window_size)
    x_train, y_train, x_test, y_test = split_train_test_by_time(x, y, test_ratio=test_ratio)

    return to_torch_if_needed(x_train, y_train, x_test, y_test, return_type=return_type)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 TE_processed.csv 转为深度学习时序输入")
    parser.add_argument(
        "--input",
        type=str,
        default="data/TE_processed.csv",
        help="输入 CSV 路径，默认 data/TE_processed.csv",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=20,
        help="时序窗口大小，默认 20",
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.2,
        help="测试集比例，默认 0.2",
    )
    parser.add_argument(
        "--return-type",
        type=str,
        choices=["numpy", "torch"],
        default="numpy",
        help="返回类型: numpy 或 torch，默认 numpy",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    x_train, y_train, x_test, y_test = build_dl_dataset(
        input_csv=Path(args.input),
        window_size=args.window_size,
        test_ratio=args.test_ratio,
        return_type=args.return_type,
    )

    print("=" * 80)
    print(f"输入文件: {Path(args.input).resolve()}")
    print(f"窗口大小: {args.window_size}")
    print(f"测试集比例: {args.test_ratio}")
    print(f"返回类型: {args.return_type}")
    print("=" * 80)

    print(f"X_train 形状: {tuple(x_train.shape)}")
    print(f"y_train 形状: {tuple(y_train.shape)}")
    print(f"X_test  形状: {tuple(x_test.shape)}")
    print(f"y_test  形状: {tuple(y_test.shape)}")

    # 展示关键目标形状: (样本数, 时间步, 特征数)
    print("=" * 80)
    print("模型输入张量形状说明:")
    print("X_* 形状均为 (样本数, 时间步, 特征数)")


if __name__ == "__main__":
    main()
