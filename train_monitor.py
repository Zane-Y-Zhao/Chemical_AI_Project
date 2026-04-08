import torch
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import os
from datetime import datetime


class TrainMonitor:
    """模型训练监控器，记录损失、指标，可视化训练曲线"""

    def __init__(self, model, device, log_dir=r"D:\TE_Project1\logs"):
        self.model = model
        self.device = device
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        # 训练记录
        self.train_losses = []
        self.val_losses = []
        self.train_accs = []
        self.val_accs = []
        self.best_val_acc = 0.0
        self.best_model_path = None

        # 日志文件
        self.log_file = os.path.join(log_dir, f"train_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(self.log_file, "w") as f:
            f.write("Epoch,Train Loss,Val Loss,Train Acc,Val Acc\n")

    def log_epoch(self, epoch, train_loss, val_loss, train_acc, val_acc):
        """记录每个epoch的指标"""
        self.train_losses.append(train_loss)
        self.val_losses.append(val_loss)
        self.train_accs.append(train_acc)
        self.val_accs.append(val_acc)

        # 写入日志
        with open(self.log_file, "a") as f:
            f.write(f"{epoch + 1},{train_loss:.4f},{val_loss:.4f},{train_acc:.4f},{val_acc:.4f}\n")

        # 打印日志
        print(
            f"\nEpoch {epoch + 1:3d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Train Acc: {train_acc:.4f} | Val Acc: {val_acc:.4f}")

        # 保存最佳模型
        if val_acc > self.best_val_acc:
            self.best_val_acc = val_acc
            self.best_model_path = os.path.join(r"D:\TE_Project1\models",
                                                f"best_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth")
            torch.save(self.model.state_dict(), self.best_model_path)
            print(f"✅ 最佳模型已保存，验证集准确率: {val_acc:.4f}")

    def plot_curves(self, save_path=None):
        """绘制训练/验证损失和准确率曲线"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

        # 损失曲线
        ax1.plot(self.train_losses, label="Train Loss")
        ax1.plot(self.val_losses, label="Val Loss")
        ax1.set_title("Loss Curve")
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Loss")
        ax1.legend()
        ax1.grid(True)

        # 准确率曲线
        ax2.plot(self.train_accs, label="Train Acc")
        ax2.plot(self.val_accs, label="Val Acc")
        ax2.set_title("Accuracy Curve")
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Accuracy")
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        if save_path is None:
            save_path = os.path.join(self.log_dir, f"train_curves_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"✅ 训练曲线已保存到: {save_path}")

    def train_epoch(self, train_loader, criterion, optimizer):
        """训练一个epoch"""
        self.model.train()
        train_loss = 0.0
        correct = 0
        total = 0

        pbar = tqdm(train_loader, desc="Training")
        for batch in pbar:
            x, y = batch
            x = x.to(self.device)
            y = y.to(self.device)

            # 前向传播
            outputs = self.model(x)
            loss = criterion(outputs, y)

            # 反向传播+优化
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # 统计
            train_loss += loss.item() * x.size(0)
            _, predicted = torch.max(outputs.data, 1)
            total += y.size(0)
            correct += (predicted == y).sum().item()

            # 更新进度条
            pbar.set_postfix({"loss": loss.item()})

        train_loss = train_loss / total
        train_acc = correct / total
        return train_loss, train_acc

    def val_epoch(self, val_loader, criterion):
        """验证一个epoch"""
        self.model.eval()
        val_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            pbar = tqdm(val_loader, desc="Validating")
            for batch in pbar:
                x, y = batch
                x = x.to(self.device)
                y = y.to(self.device)

                outputs = self.model(x)
                loss = criterion(outputs, y)

                val_loss += loss.item() * x.size(0)
                _, predicted = torch.max(outputs.data, 1)
                total += y.size(0)
                correct += (predicted == y).sum().item()

                pbar.set_postfix({"loss": loss.item()})

        val_loss = val_loss / total
        val_acc = correct / total
        return val_loss, val_acc
