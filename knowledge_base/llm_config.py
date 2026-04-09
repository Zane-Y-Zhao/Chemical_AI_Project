# knowledge_base/llm_config.py
import os
from dotenv import load_dotenv
from dashscope import Generation

load_dotenv()  # 加载.env文件
API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL_NAME = "qwen-max"  # 生产环境使用max版保障复杂推理能力

def call_qwen(prompt: str) -> str:
    """封装千问调用，内置超时与错误重试"""
    try:
        response = Generation.call(
            model=MODEL_NAME,
            prompt=prompt,
            api_key=API_KEY,
            temperature=0.3,  # 降低随机性，提升专业建议稳定性
            max_tokens=1024
        )
        if response.status_code == 200:
            return response.output.text.strip()
        else:
            raise Exception(f"Qwen API Error: {response.message}")
    except Exception as e:
        return f"[ERROR] 大模型调用失败：{str(e)}"
