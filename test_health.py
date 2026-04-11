# 测试健康检查端点的脚本
import requests
import json

# API端点URL
url = "http://127.0.0.1:8001/health"

# 发送GET请求
try:
    response = requests.get(url)
    response.raise_for_status()  # 检查请求是否成功
    
    # 打印响应
    print("响应状态码:", response.status_code)
    print("响应内容:", json.dumps(response.json(), ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f"测试失败: {str(e)}")
