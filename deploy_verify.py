# -*- coding: utf-8 -*-
"""
部署验证脚本
功能：检查开发环境与生产环境是否一致
"""

import os
import sys
import pandas as pd
import torch

print("================================================")
print("         TE项目 部署环境一致性验证脚本")
print("================================================")

# 1. Python 版本检查
print("\n【1】Python 环境检查")
print("Python 版本:", sys.version)

# 2. 关键文件是否存在
print("\n【2】关键文件完整性检查")
files = [
    "best_model.pth",
    "final_model.pth",
    "te_clean.csv",
    "models.py",
    "test_api.py",
    "performance_test.py"
]

for f in files:
    if os.path.exists(f):
        print(f"✅ {f} 存在")
    else:
        print(f"❌ {f} 缺失")

# 3. 数据一致性检查
print("\n【3】数据一致性检查")
try:
    df = pd.read_csv("te_clean.csv")
    print(f"数据形状: {df.shape}")
    if df.shape == (52, 501):
        print("✅ 数据维度与开发环境一致")
    else:
        print("⚠️  数据维度不一致")
except:
    print("❌ 数据加载失败")

# 4. 模型加载检查
print("\n【4】模型加载检查")
try:
    model = torch.load("final_model.pth")
    print("✅ 模型加载成功，环境兼容")
except:
    print("❌ 模型加载失败，环境不兼容")

# 5. 端口检查
print("\n【5】服务端口可用性检查")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(1)
port_result = sock.connect_ex(("127.0.0.1", 8001))
if port_result == 0:
    print("❌ 端口 8001 被占用")
else:
    print("✅ 端口 8001 空闲，可部署")

print("\n================================================")
print("           部署验证脚本执行完成")
print("================================================")
