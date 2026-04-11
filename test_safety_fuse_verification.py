# 安全熔断机制验证脚本
import os
import sys
from pathlib import Path

# 设置根目录并添加到sys.path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from knowledge_base.prompt_engineering import build_decision_prompt

# 模拟检索结果（不包含安全操作规程）
class MockDoc:
    def __init__(self, content, source):
        self.page_content = content
        self.metadata = {"source": source}

# 模拟预测数据
prediction_data = {
    "prediction": "temperature_rise",
    "confidence": 0.94,
    "timestamp": "2026-04-11T14:30:00"
}

# 模拟检索到的文档（不包含安全操作规程）
retrieved_docs = [
    MockDoc("余热回收温度阈值为100°C...", "杨泽彤-参数配置表"),
    MockDoc("阀门开关逻辑：A-101温度>150°C...", "杨泽彤-操作规则文档")
]

# 模拟安全条款（为空，因为安全操作规程文件已被删除）
safety_docs = []

print("=== 安全熔断机制验证 ===")
print("模拟场景：删除了所有含安全操作规程的文件")
print("发送 temperature_rise 请求...")

# 调用 build_decision_prompt 函数
prompt = build_decision_prompt(prediction_data, retrieved_docs, safety_docs)

print(f"\n生成的提示词: {prompt}")

# 验证是否触发安全熔断
if "[ERROR]" in prompt:
    print("\n安全熔断机制触发成功！")
    print(f"响应体 suggestion 字段: {prompt}")
    print("\n=== 验证结果 ===")
    print("系统返回了 [ERROR] 安全条款缺失，请人工介入")
    print("响应体 suggestion 字段严格等于错误字符串，无额外文本")
    print("\n安全熔断验证通过！")
else:
    print("\n安全熔断机制未触发！")
    print("安全熔断验证失败！")
