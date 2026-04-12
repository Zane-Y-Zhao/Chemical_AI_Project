import torch
import json
import pandas as pd
from models import TransformerModel  # 引用你 GitHub 里的模型定义
from qwen_interface import call_qwen_api  # 假设这是你调用千问的接口


class AutoResearchAgent:
    def __init__(self, model_path, device="cuda"):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        # 1. [span_4](start_span)加载你训练好的 Transformer 预测模型[span_4](end_span)
        self.predictor = self.load_trained_model(model_path)
        self.predictor.eval()
        print("✅ Transformer 预测引擎加载成功，准备进入科研模式。")

    def load_trained_model(self, path):
        # [span_5](start_span)根据你 GitHub 里的配置加载最佳模型[span_5](end_span)
        model = TransformerModel(input_size=15, d_model=128, nhead=4, num_layers=2, output_size=21)
        model.load_state_dict(torch.load(path, map_location=self.device))
        return model.to(self.device)

    def simulate_and_verify(self, test_input, hypothesis_params):
        """
        [span_6](start_span)[核心步骤] 模拟推演：将千问提出的假设参数输入模型[span_6](end_span)
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
        [span_7](start_span)[核心逻辑] 构建“反思与验证”循环[span_7](end_span)
        """
        # [span_8](start_span)第一步：让千问根据当前工况提出 3 个优化假设[span_8](end_span)
        prompt = f"当前工况数据为 {current_data}。请提出3个针对余热回收优化的参数调整假设（如：温度提高5度）。"
        hypotheses = call_qwen_api(prompt)  # 返回 JSON 格式的假设列表

        results = []
        for h in hypotheses:
            # [span_9](start_span)第二步：自动执行模拟推演[span_9](end_span)
            prediction = self.simulate_and_verify(current_data, h)
            results.append({"hypothesis": h, "predicted_fault_risk": prediction})

        # [span_10](start_span)第三步：让千问根据模拟结果进行“批判性审查”并选出最优解[span_10](end_span)
        final_prompt = f"模拟推演结果如下：{results}。请选出最安全且节能的方案，并生成优化报告。"
        final_report = call_qwen_api(final_prompt)

        return final_report


# 使用示例
if __name__ == "__main__":
    # 指向你刚才跑成功的最佳模型文件
    agent = AutoResearchAgent(model_path="./models/best_model_xxx.pth")

    # 模拟一组实时传感器数据
    sample_data = torch.randn(1, 5, 15)
    report = agent.research_loop(sample_data)
    print(f"🔬 AutoResearch 研究报告：\n{report}")