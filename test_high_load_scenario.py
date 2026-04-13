import torch
import sys
from auto_research import AutoResearchAgent

# 模拟高负荷工况数据
def create_high_load_data():
    """
    创建模拟高负荷工况的传感器数据
    """
    # 基础数据
    data = torch.randn(1, 5, 15)
    # 模拟高负荷工况，提高温度值（第5列）
    data[:, :, 5] += 10.0  # 提高温度
    data[:, :, 6] += 5.0   # 提高压力
    return data

# 测试函数
def test_high_load_scenario():
    print("[TEST] 开始测试高负荷工况场景...", file=sys.stdout)
    
    # 加载模型
    model_path = "./runs/te_transformer/best_transformer_te.pth"
    print(f"[TEST] 加载模型：{model_path}", file=sys.stdout)
    agent = AutoResearchAgent(model_path=model_path)
    
    # 创建高负荷工况数据
    print("[TEST] 创建高负荷工况数据...", file=sys.stdout)
    high_load_data = create_high_load_data()
    print(f"[TEST] 高负荷数据形状：{high_load_data.shape}", file=sys.stdout)
    print(f"[TEST] 温度数据：{high_load_data[0, :, 5]}", file=sys.stdout)
    
    # 执行科研循环
    print("[TEST] 执行科研循环，模拟高负荷工况下的优化...", file=sys.stdout)
    report = agent.research_loop(high_load_data)
    
    # 输出结果
    print("[TEST] 测试完成！", file=sys.stdout)
    print("[TEST] AutoResearch 研究报告：", file=sys.stdout)
    print(report, file=sys.stdout)

if __name__ == "__main__":
    test_high_load_scenario()
