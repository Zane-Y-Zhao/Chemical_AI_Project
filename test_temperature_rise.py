import requests
import json

# API 端点
url = "http://localhost:8006/api/v1/decision"

# 请求数据
data = {
    "temperature": 85.5,
    "pressure": 4.2,
    "flow_rate": 10.5,
    "heat_value": 1250.8,
    "timestamp": "2026-04-11T14:30:00",
    "unit": "°C"
}

# 发送请求
try:
    response = requests.post(url, json=data, timeout=10)
    # 打印响应
    print("响应状态码:", response.status_code)
    print("响应内容:", json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print("请求失败:", str(e))
