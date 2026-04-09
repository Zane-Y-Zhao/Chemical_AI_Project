import pandas as pd
import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score, recall_score, f1_score
import joblib

# 导入Transformer模型（替换原LSTMModel）
from models import TransformerModel
from train_monitor import TrainMonitor

# ---------------------- 1. 配置参数（完全保留，无需修改） ----------------------
data_path = r"D:\TE_Project1\data"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
window_size = 5  # 和data_processor.py中保持一致
batch_size = 32
epochs = 20
lr = 0.001

# ---------------------- 2. 加载数据（完全保留，无需修改） ----------------------
# 加载特征工程后的数据
train_df = pd.read_csv(os.path.join(data_path, "train_final.csv"))
val_df = pd.read_csv(os.path.join(data_path, "val_final.csv"))
test_df = pd.read_csv(os.path.join(data_path, "test_final.csv"))
scaler = joblib.load(os.path.join(data_path, "te_scaler.pkl"))

# 分离特征和标签（最后一列是label）
feature_cols = train_df.columns[:-1]
X_train, y_train = train_df[feature_cols].values, train_df["label"].values
X_val, y_val = val_df[feature_cols].values, val_df["label"].values
X_test, y_test = test_df[feature_cols].values, test_df["label"].values


# ---------------------- 3. 构造时序数据集（完全保留，无需修改） ----------------------
class TEDataset(Dataset):
    def __init__(self, X, y, window_size):
        self.X = X
        self.y = y
        self.window_size = window_size
        self.n_samples = len(X) - window_size + 1

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        # 取窗口大小的序列
        x_seq = self.X[idx:idx + self.window_size]
        y_label = self.y[idx + self.window_size - 1]
        return torch.tensor(x_seq, dtype=torch.float32), torch.tensor(y_label, dtype=torch.long)


# 创建数据集和DataLoader
train_dataset = TEDataset(X_train, y_train, window_size)
val_dataset = TEDataset(X_val, y_val, window_size)
test_dataset = TEDataset(X_test, y_test, window_size)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

# ---------------------- 4. 初始化模型、损失函数、优化器（仅修改模型部分） ----------------------
input_size = len(feature_cols)  # 特征工程后的特征数
# 替换LSTMModel为TransformerModel，参数完全适配
model = TransformerModel(
    input_size=input_size,
    d_model=128,
    nhead=4,
    num_layers=2,
    output_size=2
).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=lr)

# ---------------------- 5. 初始化训练监控器（完全保留，无需修改） ----------------------
monitor = TrainMonitor(model, device)

# ---------------------- 6. 训练循环（完全保留，无需修改） ----------------------
for epoch in range(epochs):
    # 训练一个epoch
    train_loss, train_acc = monitor.train_epoch(train_loader, criterion, optimizer)
    # 验证一个epoch
    val_loss, val_acc = monitor.val_epoch(val_loader, criterion)
    # 记录epoch指标
    monitor.log_epoch(epoch, train_loss, val_loss, train_acc, val_acc)

# ---------------------- 7. 训练完成，绘制曲线（完全保留，无需修改） ----------------------
monitor.plot_curves()

# ---------------------- 8. 测试集评估（完全保留，无需修改） ----------------------
print("\n" + "=" * 50)
print("📊 测试集最终评估")
print("=" * 50)
test_loss, test_acc = monitor.val_epoch(test_loader, criterion)
print(f"测试集损失: {test_loss:.4f} | 测试集准确率: {test_acc:.4f}")

# 计算召回率、F1分数
model.eval()
test_preds = []
test_labels = []
with torch.no_grad():
    for batch in test_loader:
        x, y = batch
        x = x.to(device)
        outputs = model(x)
        _, preds = torch.max(outputs, 1)
        test_preds.extend(preds.cpu().numpy())
        test_labels.extend(y.numpy())

test_recall = recall_score(test_labels, test_preds)
test_f1 = f1_score(test_labels, test_preds)
print(f"测试集召回率: {test_recall:.4f} | 测试集F1分数: {test_f1:.4f}")
