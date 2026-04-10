import torch
import numpy as np
from models import TransformerModel

# 设备
device = torch.device("cpu")

# ！！！这里必须和你训练时完全一样！！！
input_size = 3000  # 你的特征数量是3000，不是15
model = TransformerModel(
    input_size=input_size,
    d_model=64,
    nhead=2,
    num_layers=1,
    output_size=21,
    dropout=0.3
).to(device)

# 加载模型
model.load_state_dict(torch.load("final_model.pth", map_location=device))
model.eval()

# 构造正确形状的输入
test_input = torch.randn(1, 5, input_size)  # [1, 窗口5, 特征3000]

# 推理
with torch.no_grad():
    output = model(test_input)
    pred = output.argmax(1).item()

print("✅ 模型接口测试成功！")
print("输入形状:", test_input.shape)
print("模型预测故障类别:", pred)