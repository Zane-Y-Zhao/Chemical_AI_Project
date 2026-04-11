import sys
import os
from pathlib import Path

# 设置根目录并添加到sys.path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from knowledge_base.prompt_engineering import build_decision_prompt

# 模拟预测数据
prediction_data = {
    "prediction": "temperature_rise",
    "confidence": 0.94,
    "timestamp": "2026-04-11T14:30:00"
}

# 模拟检索结果（不包含安全操作规程）
class MockDoc:
    def __init__(self, content, source):
        self.page_content = content
        self.metadata = {"source": source}

# 模拟检索到的文档（不包含安全操作规程）
retrieved_docs = [
    MockDoc("余热回收温度阈值为100°C。低于此温度，烟气余热回收效率急剧下降。", "杨泽彤-参数配置表"),
    MockDoc("阀门开关逻辑：A-101温度>150°C且压力>2.5MPa时关闭FV-101。", "杨泽彤-操作规则文档")
]

# 模拟安全条款（空）
safety_docs = []

# 测试安全熔断机制
print("测试安全熔断机制...")
print("="*50)

try:
    # 构建提示词（这会触发安全熔断）
    prompt = build_decision_prompt(prediction_data, retrieved_docs, safety_docs)
    print(f"构建的提示词: {prompt}")
    
    if "[ERROR]" in prompt:
        print("\n✅ 安全熔断机制触发成功！")
        print(f"错误信息: {prompt}")
    else:
        print("\n❌ 安全熔断机制未触发")
        
except Exception as e:
    print(f"\n❌ 测试失败: {str(e)}")

print("="*50)
