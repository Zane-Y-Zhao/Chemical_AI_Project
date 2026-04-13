import torch
import sys
import os

# 确保日志目录存在
log_dir = "./logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 日志文件
log_file = os.path.join(log_dir, "auto_research_simulation.log")

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

# 模拟千问API调用
def mock_call_qwen_api(prompt):
    """
    模拟千问API调用，返回预设的假设
    """
    log_message("[QWen] 模拟调用千问API...")
    log_message(f"[QWen] 提示词：{prompt[:100]}...")
    
    # 模拟高负荷工况下的假设
    if "高负荷" in prompt or "温度" in prompt:
        return [
            {"temp_change": 5, "description": "提高温度5度（180℃）"},
            {"temp_change": -5, "description": "降低温度5度（170℃）"},
            {"temp_change": -3, "description": "降低温度3度（172℃）"}
        ]
    else:
        return [
            {"temp_change": 5, "description": "提高温度5度"},
            {"temp_change": -3, "description": "降低温度3度"},
            {"temp_change": 0, "description": "保持温度不变"}
        ]

# 模拟模型预测
def mock_predict(model, input_data):
    """
    模拟模型预测，返回预设的结果
    """
    # 模拟不同温度下的故障风险预测
    # 温度越高，故障风险越高
    temperature = input_data[0, 0, 5]
    if temperature > 15:  # 模拟180℃的情况
        return 1  # 高风险
    elif temperature > 10:  # 模拟175℃的情况
        return 0  # 低风险
    else:
        return 0  # 低风险

# 模拟科研循环
def mock_research_loop(current_data):
    """
    模拟科研循环，输出所有过程步骤
    """
    log_message("[PROCESS] 第一步：让千问根据当前工况提出 3 个优化假设...")
    
    # 构建提示词
    prompt = f"当前工况数据为 {current_data}。请提出3个针对余热回收优化的参数调整假设（如：温度提高5度）。"
    
    # 调用模拟的千问API
    hypotheses = mock_call_qwen_api(prompt)
    log_message(f"[PROCESS] 千问返回的假设：{hypotheses}")

    log_message("[PROCESS] 第二步：执行模拟推演...")
    results = []
    for i, h in enumerate(hypotheses):
        log_message(f"[PROCESS] 测试假设 {i+1}：{h}")
        
        # 模拟修改输入数据
        simulated_input = current_data.clone()
        simulated_input[:, :, 5] += h.get("temp_change", 0)
        
        # 模拟模型预测
        prediction = mock_predict(None, simulated_input)
        
        # 模拟应力计算
        current_temp = current_data[0, 0, 5].item()
        new_temp = simulated_input[0, 0, 5].item()
        # 简单模拟应力与温度的关系
        stress = 150 + new_temp * 2
        
        log_message(f"[PROCESS] 假设 {i+1} 结果：")
        log_message(f"[PROCESS] - 温度变化：{h.get('temp_change', 0)}度")
        log_message(f"[PROCESS] - 新温度：{new_temp:.1f}℃")
        log_message(f"[PROCESS] - 预测故障风险：{prediction}")
        log_message(f"[PROCESS] - 预测应力：{stress:.1f}MPa")
        
        results.append({
            "hypothesis": h, 
            "predicted_fault_risk": prediction,
            "stress": stress,
            "temperature": new_temp
        })

    log_message("[PROCESS] 第三步：分析模拟结果...")
    log_message(f"[PROCESS] 模拟推演结果：{results}")
    
    # 分析结果，找出最优方案
    best_option = None
    min_risk = float('inf')
    min_stress = float('inf')
    
    for result in results:
        if result["predicted_fault_risk"] < min_risk:
            min_risk = result["predicted_fault_risk"]
            best_option = result
        elif result["predicted_fault_risk"] == min_risk:
            if result["stress"] < min_stress:
                min_stress = result["stress"]
                best_option = result
    
    log_message("[PROCESS] 第四步：生成优化报告...")
    
    # 生成优化报告
    report = f"""
    AutoResearch 高负荷工况优化报告
    ================================
    
    1. 初始工况分析
       - 温度：{current_data[0, 0, 5].item():.1f}℃
       - 压力：{current_data[0, 0, 6].item():.1f}MPa
       - 状态：高负荷
    
    2. 优化假设分析
    """
    
    for i, result in enumerate(results):
        report += f"   {i+1}. {result['hypothesis']['description']}\n"
        report += f"      - 新温度：{result['temperature']:.1f}℃\n"
        report += f"      - 预测应力：{result['stress']:.1f}MPa\n"
        report += f"      - 故障风险：{'高' if result['predicted_fault_risk'] > 0 else '低'}\n"
        if result['stress'] > 180:
            report += f"      - 状态：[WARNING] 应力超标\n"
        else:
            report += f"      - 状态：[OK] 安全\n"
        report += "\n"
    
    report += f"3. 最优方案\n"
    report += f"   - 推荐方案：{best_option['hypothesis']['description']}\n"
    report += f"   - 推荐温度：{best_option['temperature']:.1f}℃\n"
    report += f"   - 预测应力：{best_option['stress']:.1f}MPa\n"
    report += f"   - 故障风险：{'高' if best_option['predicted_fault_risk'] > 0 else '低'}\n"
    report += f"   - 状态：{'[WARNING] 应力超标' if best_option['stress'] > 180 else '[OK] 安全'}\n"
    
    report += "\n4. 结论\n"
    if best_option['stress'] <= 180:
        report += "   [OK] AutoResearch 成功避免了潜在的安全事故\n"
        report += "   [OK] 推荐方案在安全范围内，同时保持了较高的能量回收效率\n"
    else:
        report += "   [WARNING] 所有方案均存在安全风险，建议进一步调整参数\n"
    
    log_message("[PROCESS] 生成优化报告完成")
    log_message(f"[PROCESS] 报告内容：\n{report}")
    
    return report

# 主测试函数
def test_simulation():
    """
    测试模拟的AutoResearch系统
    """
    log_message("[TEST] 开始模拟测试高负荷工况场景...")
    log_message(f"[TEST] Python版本：{sys.version}")
    log_message(f"[TEST] PyTorch版本：{torch.__version__}")
    
    # 创建高负荷工况数据
    high_load_data = create_high_load_data()
    
    # 执行模拟科研循环
    log_message("[TEST] 执行模拟科研循环...")
    report = mock_research_loop(high_load_data)
    
    log_message("[TEST] 模拟测试完成！")
    log_message("[TEST] 最终优化报告：")
    log_message(report)

if __name__ == "__main__":
    # 清空日志文件
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("AutoResearch 高负荷工况模拟测试日志\n")
        f.write("="*60 + "\n")
    
    test_simulation()
