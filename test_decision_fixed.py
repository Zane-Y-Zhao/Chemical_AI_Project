# 测试决策端点的脚本
import requests
import json

# API端点URL
url = "http://127.0.0.1:8001/api/v1/decision"

# 测试数据
test_data = {
    "temperature": 85.5,
    "pressure": 4.2,
    "flow_rate": 10.5,
    "heat_value": 1250.8,
    "timestamp": "2026-04-10T14:30:00",
    "unit": "°C"
}

# 发送POST请求
try:
    response = requests.post(url, json=test_data)
    response.raise_for_status()  # 检查请求是否成功
    
    # 打印响应
    print("响应状态码:", response.status_code)
    print("响应内容:", json.dumps(response.json(), ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f"测试失败: {str(e)}")
    print(f"响应内容: {response.text if 'response' in locals() else 'No response'}")
