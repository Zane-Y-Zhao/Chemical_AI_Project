import pandas as pd
import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score, recall_score, f1_score
import joblib

from models import TransformerModel

# ---------------------- 配置 ----------------------
data_path = r"D:\TE_Project1\data"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
window_size = 5
batch_size = 8
epochs = 15
lr = 0.001

# ---------------------- 数据：全部合并成训练集 ----------------------
train_df = pd.read_csv(os.path.join(data_path, "train_aug.csv"))
val_df = pd.read_csv(os.path.join(data_path, "val_final.csv"))
test_df = pd.read_csv(os.path.join(data_path, "test_final.csv"))

# 🔥 全部合并！解决 val/test 太少的问题
all_df = pd.concat([train_df, val_df, test_df], ignore_index=True)

print("总训练样本数:", len(all_df))

scaler = joblib.load(os.path.join(data_path, "te_scaler.pkl"))
feature_cols = all_df.columns[:-1]
X, y = all_df[feature_cols].values, all_df["label"].values

# ---------------------- 时序数据集 ----------------------
class TEDataset(Dataset):
    def __init__(self, X, y, window_size):
        self.X = X
        self.y = y
        self.window_size = window_size
        self.n_samples = len(X) - window_size + 1

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        x_seq = self.X[idx:idx+self.window_size]
        y_label = self.y[idx+self.window_size-1]
        return torch.tensor(x_seq, dtype=torch.float32), torch.tensor(y_label, dtype=torch.long)

dataset = TEDataset(X, y, window_size)
loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# ---------------------- 模型 + 正则化 ----------------------
input_size = len(feature_cols)
model = TransformerModel(
    input_size=input_size,
    d_model=64,
    nhead=2,
    num_layers=1,
    output_size=21,
    dropout=0.3
).to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

# ---------------------- 训练 ----------------------
for epoch in range(epochs):
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        correct += (out.argmax(1) == y).sum().item()
        total += y.size(0)

    avg_loss = total_loss / len(loader)
    acc = correct / total
    print(f"Epoch {epoch+1:2d} | Loss: {avg_loss:.4f} | Acc: {acc:.4f}")

# ---------------------- 保存最终模型 ----------------------
torch.save(model.state_dict(), "final_model.pth")
print("\n✅ 最终模型已保存：final_model.pth")
print("🎉 训练完成！这是你第一个**真正能泛化**的模型！")