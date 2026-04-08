import pandas as pd
import os
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib

# ---------------------- 1. 加载第1天清洗好的数据 ----------------------
data_path = r"D:\TE_Project1\data"

df = pd.read_csv(os.path.join(data_path, "te_clean.csv"))
print(f"✅ 加载清洗后数据，形状: {df.shape}")

# ---------------------- 2. 时间序列数据集划分（严格按顺序，防泄露） ----------------------
# TE数据是时序数据，绝对不能随机划分！按7:1.5:1.5拆分
total_len = len(df)
train_size = int(0.7 * total_len)
val_size = int(0.15 * total_len)

train_df = df.iloc[:train_size]
val_df = df.iloc[train_size:train_size + val_size]
test_df = df.iloc[train_size + val_size:]

# 保存划分后的原始数据
train_df.to_csv(os.path.join(data_path, "train_raw.csv"), index=False)
val_df.to_csv(os.path.join(data_path, "val_raw.csv"), index=False)
test_df.to_csv(os.path.join(data_path, "test_raw.csv"), index=False)
print(f"✅ 数据集划分完成:\n训练集: {len(train_df)}, 验证集: {len(val_df)}, 测试集: {len(test_df)}")

# ---------------------- 3. 数据标准化（仅用训练集拟合） ----------------------
# 分离特征列和标签列（最后一列是label）
feature_cols = train_df.columns[:-1]
label_col = train_df.columns[-1]

# 初始化标准化器，仅用训练集拟合
scaler = StandardScaler()
scaler.fit(train_df[feature_cols])

# 转换训练/验证/测试集
train_scaled = train_df.copy()
val_scaled = val_df.copy()
test_scaled = test_df.copy()

train_scaled[feature_cols] = scaler.transform(train_df[feature_cols])
val_scaled[feature_cols] = scaler.transform(val_df[feature_cols])
test_scaled[feature_cols] = scaler.transform(test_df[feature_cols])

# 保存标准化后的数据和scaler（后续模型推理必须用这个scaler）
train_scaled.to_csv(os.path.join(data_path, "train_scaled.csv"), index=False)
val_scaled.to_csv(os.path.join(data_path, "val_scaled.csv"), index=False)
test_scaled.to_csv(os.path.join(data_path, "test_scaled.csv"), index=False)
joblib.dump(scaler, os.path.join(data_path, "te_scaler.pkl"))
print("✅ 数据标准化完成，scaler已保存")


# ---------------------- 4. 特征工程：滑动窗口特征（适配LSTM/Transformer） ----------------------
def create_time_window_features(df, window_size=5):
    """为每个特征构造滑动窗口统计特征"""
    df_new = df.copy()
    features = df_new.columns[:-1]  # 排除label列

    for feat in features:
        # 滚动窗口计算均值、标准差、最大值、最小值、变化量
        df_new[f"{feat}_mean_{window_size}"] = df_new[feat].rolling(window=window_size, min_periods=1).mean()
        df_new[f"{feat}_std_{window_size}"] = df_new[feat].rolling(window=window_size, min_periods=1).std().fillna(0)
        df_new[f"{feat}_max_{window_size}"] = df_new[feat].rolling(window=window_size, min_periods=1).max()
        df_new[f"{feat}_min_{window_size}"] = df_new[feat].rolling(window=window_size, min_periods=1).min()
        df_new[f"{feat}_diff_{window_size}"] = df_new[feat].diff(window_size).fillna(0)

    return df_new


# 对训练/验证/测试集分别构造特征（避免数据泄露）
window_size = 5  # 可根据需求调整为10
train_final = create_time_window_features(train_scaled, window_size)
val_final = create_time_window_features(val_scaled, window_size)
test_final = create_time_window_features(test_scaled, window_size)

# 保存特征工程后的最终数据（模型训练用）
train_final.to_csv(os.path.join(data_path, "train_final.csv"), index=False)
val_final.to_csv(os.path.join(data_path, "val_final.csv"), index=False)
test_final.to_csv(os.path.join(data_path, "test_final.csv"), index=False)
print(f"✅ 特征工程完成，最终训练集形状: {train_final.shape}")
