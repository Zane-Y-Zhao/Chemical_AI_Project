import torch
import sys
import os
from auto_research import AutoResearchAgent

# 确保日志目录存在
log_dir = "./logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 日志文件
log_file = os.path.join(log_dir, "auto_research_test.log")

# 自定义日志函数
def log_message(message):
    """
    输出日志到控制台和文件
    """
    print(message, file=sys.stdout)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")

# 模拟高负荷工况数据
def create_high_load_data():
    """
    创建模拟高负荷工况的传感器数据
    """
    log_message("[PROCESS] 创建高负荷工况数据...")
    # 基础数据
    data = torch.randn(1, 5, 15)
    # 模拟高负荷工况，提高温度值（第5列）
    data[:, :, 5] += 10.0  # 提高温度
    data[:, :, 6] += 5.0   # 提高压力
    log_message(f"[PROCESS] 高负荷数据形状：{data.shape}")
    log_message(f"[PROCESS] 温度数据：{data[0, :, 5]}")
    log_message(f"[PROCESS] 压力数据：{data[0, :, 6]}")
    return data

# 详细测试函数
def test_detailed_process():
    log_message("[TEST] 开始详细测试高负荷工况场景...")
    log_message(f"[TEST] Python版本：{sys.version}")
    log_message(f"[TEST] PyTorch版本：{torch.__version__}")
    
    # 加载模型
    model_path = "./runs/te_transformer/best_transformer_te.pth"
    log_message(f"[TEST] 加载模型：{model_path}")
    
    try:
        agent = AutoResearchAgent(model_path=model_path)
        log_message("[TEST] 模型加载成功")
    except Exception as e:
        log_message(f"[ERROR] 模型加载失败：{str(e)}")
        return
    
    # 创建高负荷工况数据
    high_load_data = create_high_load_data()
    
    # 执行科研循环
    log_message("[TEST] 执行科研循环，模拟高负荷工况下的优化...")
    
    try:
        import time
        start_time = time.time()
        log_message(f"[TEST] 科研循环开始时间：{start_time}")
        
        report = agent.research_loop(high_load_data)
        
        end_time = time.time()
        log_message(f"[TEST] 科研循环结束时间：{end_time}")
        log_message(f"[TEST] 科研循环执行时间：{end_time - start_time:.2f}秒")
        
        log_message("[TEST] 科研循环执行成功")
        log_message("[TEST] AutoResearch 研究报告：")
        log_message(report)
    except Exception as e:
        log_message(f"[ERROR] 科研循环执行失败：{str(e)}")
        import traceback
        traceback_str = traceback.format_exc()
        log_message(f"[ERROR] 详细错误信息：{traceback_str}")
        print(traceback_str, file=sys.stdout)

    log_message("[TEST] 详细测试完成！")

if __name__ == "__main__":
    # 清空日志文件
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("AutoResearch 高负荷工况测试日志\n")
        f.write("="*60 + "\n")
    
    test_detailed_process()
