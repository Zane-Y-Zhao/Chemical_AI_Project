import torch
import sys

# 简单测试脚本
print("[TEST] 开始简单测试...", file=sys.stdout)
print(f"[TEST] Python版本：{sys.version}", file=sys.stdout)
print(f"[TEST] PyTorch版本：{torch.__version__}", file=sys.stdout)

# 测试PyTorch
print("[TEST] 测试PyTorch...", file=sys.stdout)
test_tensor = torch.tensor([1, 2, 3])
print(f"[TEST] PyTorch测试成功：{test_tensor}", file=sys.stdout)

# 测试模型导入
try:
    from models import TransformerModel
    print("[TEST] 模型导入成功", file=sys.stdout)
    # 测试模型初始化
    model = TransformerModel(input_size=15, d_model=128, nhead=4, num_layers=2, output_size=21, dim_feedforward=256, hidden_size=64)
    print("[TEST] 模型初始化成功", file=sys.stdout)
    # 测试模型前向传播
    test_input = torch.randn(1, 5, 15)
    output = model(test_input)
    print(f"[TEST] 模型前向传播成功，输出形状：{output.shape}", file=sys.stdout)
except Exception as e:
    print(f"[TEST] 模型测试失败：{str(e)}", file=sys.stdout)

# 测试qwen_interface导入
try:
    from qwen_interface import call_qwen_api
    print("[TEST] qwen_interface导入成功", file=sys.stdout)
    # 测试call_qwen_api函数
    test_prompt = "测试"  
    result = call_qwen_api(test_prompt)
    print(f"[TEST] call_qwen_api测试成功，返回类型：{type(result)}", file=sys.stdout)
except Exception as e:
    print(f"[TEST] qwen_interface测试失败：{str(e)}", file=sys.stdout)

print("[TEST] 简单测试完成！", file=sys.stdout)
