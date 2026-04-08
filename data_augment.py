import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import os


class TEDataAugmentor:
    """TE时序数据增强工具，仅作用于训练集"""

    def __init__(self, noise_std=0.01, scale_range=(0.9, 1.1), warp_strength=0.1):
        self.noise_std = noise_std
        self.scale_range = scale_range
        self.warp_strength = warp_strength

    def add_gaussian_noise(self, x):
        """添加高斯噪声，模拟传感器噪声"""
        noise = np.random.normal(0, self.noise_std, size=x.shape)
        return x + noise

    def scale_signal(self, x):
        """信号缩放，模拟工况波动"""
        scale = np.random.uniform(*self.scale_range)
        return x * scale

    def time_warp(self, x):
        """时间扭曲，模拟时序波动"""
        seq_len = x.shape[0]
        warp = np.random.uniform(-self.warp_strength, self.warp_strength, size=seq_len)
        time = np.arange(seq_len) + np.cumsum(warp)
        time = np.clip(time, 0, seq_len - 1)
        f = interp1d(time, x, axis=0, kind='linear', fill_value="extrapolate")
        return f(np.arange(seq_len))

    def augment_dataset(self, X, y, augment_ratio=2):
        """
        增强数据集
        X: 原始特征 (n_samples, seq_len, feature_dim)
        y: 标签 (n_samples,)
        augment_ratio: 增强倍数（2表示生成2倍新样本）
        """
        n_samples, seq_len, feature_dim = X.shape
        X_aug_list = [X]
        y_aug_list = [y]

        for _ in range(augment_ratio):
            X_new = np.zeros_like(X)
            for i in range(n_samples):
                x_aug = self.add_gaussian_noise(X[i])
                x_aug = self.scale_signal(x_aug)
                x_aug = self.time_warp(x_aug)
                X_new[i] = x_aug
            X_aug_list.append(X_new)
            y_aug_list.append(y)

        X_aug = np.concatenate(X_aug_list, axis=0)
        y_aug = np.concatenate(y_aug_list, axis=0)
        print(f"✅ 数据增强完成，原始样本: {n_samples}, 增强后: {len(X_aug)}")
        return X_aug, y_aug


# ---------------------- 工具使用示例 ----------------------
if __name__ == "__main__":
    # 加载训练集
    data_path = r"D:\TE_Project1\data"

    train_df = pd.read_csv(os.path.join(data_path, "train_final.csv"))
    feature_cols = train_df.columns[:-1]
    X = train_df[feature_cols].values
    y = train_df["label"].values

    # 初始化增强器
    augmentor = TEDataAugmentor()
    # 模拟时序样本（将一维数据转为(样本数, 窗口大小, 特征数)）
    window_size = 5
    n_samples = len(X) - window_size + 1
    X_seq = np.array([X[i:i + window_size] for i in range(n_samples)])
    y_seq = y[window_size - 1:]

    # 增强数据集
    X_aug, y_aug = augmentor.augment_dataset(X_seq, y_seq, augment_ratio=2)
    print(f"增强后特征形状: {X_aug.shape}, 标签形状: {y_aug.shape}")
