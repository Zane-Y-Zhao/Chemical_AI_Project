import torch
import json
import pandas as pd
import sys
from models import TransformerModel  # 引用模型定义
from qwen_interface import call_qwen_api  # 调用千问的接口


class AutoResearchAgent:
    def __init__(self, model_path, device="cuda"):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        print(f"[INFO] 使用设备：{self.device}", file=sys.stdout)
        # 1. 加载训练好的 Transformer 预测模型
        print(f"[INFO] 开始加载模型：{model_path}", file=sys.stdout)
        self.predictor = self.load_trained_model(model_path)
        self.predictor.eval()
        print("[INFO] Transformer 预测引擎加载成功，准备进入科研模式。", file=sys.stdout)

    def load_trained_model(self, path):
        # 根据配置加载最佳模型
        model = TransformerModel(
            input_size=15, 
            d_model=128, 
            nhead=4, 
            num_layers=2, 
            output_size=21, 
            dim_feedforward=256, 
            hidden_size=64
        )
        model.load_state_dict(torch.load(path, map_location=self.device))
        return model.to(self.device)

    def simulate_and_verify(self, test_input, hypothesis_params):
        """
        [核心步骤] 模拟推演：将千问提出的假设参数输入模型
        """
        # 模拟修改输入特征（比如尝试提高温度或压力）
        simulated_input = test_input.clone()
        # 假设第 5 列是温度，根据 LLM 的建议进行调整
        simulated_input[:, :, 5] += hypothesis_params.get("temp_change", 0)

        with torch.no_grad():
            output = self.predictor(simulated_input)
            _, pred = torch.max(output, 1)
        return pred.item()

    def research_loop(self, current_data):
        """
        [核心逻辑] 构建“反思与验证”循环
        """
        import sys
        import os
        
        # 确保日志目录存在
        log_dir = "./logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 日志文件
        log_file = os.path.join(log_dir, "auto_research_test.log")
        
        # 自定义日志函数
        def log(message):
            print(message, file=sys.stdout)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        
        # 第一步：让千问根据当前工况提出 3 个优化假设
        log("[PROCESS] 第一步：让千问根据当前工况提出 3 个优化假设...")
        json_example = '[{"temp_change": 5, "description": "提高温度5度"}, {"temp_change": -3, "description": "降低温度3度"}, {"temp_change": 0, "description": "保持温度不变"}]'
        prompt = '当前工况数据为 ' + str(current_data) + '。请提出3个针对余热回收优化的参数调整假设（如：温度提高5度）。返回格式应为JSON数组，每个元素包含temp_change和description字段，例如：' + json_example
        log("[PROCESS] 调用千问API...")
        
        try:
            hypotheses = call_qwen_api(prompt)  # 返回 JSON 格式的假设列表
            log(f"[PROCESS] 千问返回的假设：{hypotheses}")
        except Exception as e:
            log(f"[ERROR] 调用千问API失败：{str(e)}")
            # 返回默认假设
            hypotheses = [
                {"temp_change": 5, "description": "提高温度5度"},
                {"temp_change": -3, "description": "降低温度3度"},
                {"temp_change": 0, "description": "保持温度不变"}
            ]
            log(f"[PROCESS] 使用默认假设：{hypotheses}")

        results = []
        for i, h in enumerate(hypotheses):
            # 第二步：自动执行模拟推演
            log(f"[PROCESS] 第二步：执行第 {i+1} 个假设的模拟推演...")
            log(f"[PROCESS] 假设 {i+1}：{h}")
            try:
                prediction = self.simulate_and_verify(current_data, h)
                results.append({"hypothesis": h, "predicted_fault_risk": prediction})
                log(f"[PROCESS] 第 {i+1} 个假设的预测结果：{prediction}")
            except Exception as e:
                log(f"[ERROR] 模拟推演失败：{str(e)}")

        # 第三步：让千问根据模拟结果进行“批判性审查”并选出最优解
        log("[PROCESS] 第三步：让千问根据模拟结果进行批判性审查...")
        log(f"[PROCESS] 模拟推演结果：{results}")
        final_prompt = '模拟推演结果如下：' + str(results) + '。请选出最安全且节能的方案，并生成优化报告。'
        log("[PROCESS] 调用千问API生成最终报告...")
        
        try:
            final_report = call_qwen_api(final_prompt)
            log(f"[PROCESS] 千问返回的最终报告：{final_report}")
        except Exception as e:
            log(f"[ERROR] 生成最终报告失败：{str(e)}")
            final_report = "[ERROR] 生成最终报告失败"

        return final_report


# 使用示例
if __name__ == "__main__":
    import sys
    print("[INFO] 启动 AutoResearch 智能科研代理...", file=sys.stdout)
    # 指向最佳模型文件
    model_path = "./runs/te_transformer/best_transformer_te.pth"
    print(f"[INFO] 加载模型：{model_path}", file=sys.stdout)
    agent = AutoResearchAgent(model_path=model_path)

    # 模拟一组实时传感器数据
    print("[INFO] 生成模拟传感器数据...", file=sys.stdout)
    sample_data = torch.randn(1, 5, 15)
    print(f"[INFO] 模拟数据形状：{sample_data.shape}", file=sys.stdout)
    
    print("[INFO] 开始科研循环...", file=sys.stdout)
    report = agent.research_loop(sample_data)
    print(f"[INFO] AutoResearch 研究报告：\n{report}", file=sys.stdout)
    print("[INFO] 科研任务完成！", file=sys.stdout)

