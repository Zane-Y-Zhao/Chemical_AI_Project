# knowledge_base/llm_config.py
import os
import time
from dotenv import load_dotenv
from dashscope import Generation

load_dotenv()  # 加载.env文件
API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL_NAME = "qwen-max"  # 生产环境使用max版保障复杂推理能力

def call_qwen(prompt: str) -> str:
    """封装千问调用，内置超时与错误重试"""
    print(f"[DEBUG] 开始调用大模型，prompt: {prompt[:50]}...")
    start_time = time.time()
    try:
        print(f"[DEBUG] API_KEY: {API_KEY[:10]}...")
        print(f"[DEBUG] MODEL_NAME: {MODEL_NAME}")
        
        response = Generation.call(
            model=MODEL_NAME,
            prompt=prompt,
            api_key=API_KEY,
            temperature=0.5,  # 平衡保守性和灵活性
            max_tokens=2048,  # 增加最大token数，支持更复杂的回答
            top_p=0.9,  # 控制生成的多样性
            timeout=15  # 增加超时时间，确保复杂问题有足够时间处理
        )
        end_time = time.time()
        print(f"[DEBUG] 大模型调用完成，耗时：{end_time - start_time:.2f}s")
        print(f"[DEBUG] 响应状态码：{response.status_code}")
        
        if response.status_code == 200:
            result = response.output.text.strip()
            print(f"[DEBUG] 响应内容：{result[:100]}...")
            return result
        else:
            error_message = f"Qwen API Error: {response.message}"
            print(f"[DEBUG] {error_message}")
            raise Exception(error_message)
    except Exception as e:
        end_time = time.time()
        print(f"[DEBUG] 大模型调用失败，耗时：{end_time - start_time:.2f}s")
        print(f"[DEBUG] 错误：{str(e)}")
        return f"[ERROR] 大模型调用失败：{str(e)}"

