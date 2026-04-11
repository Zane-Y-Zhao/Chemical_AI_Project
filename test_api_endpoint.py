import requests

# 测试决策API端点
url = "http://127.0.0.1:8001/api/v1/decision"
headers = {"Content-Type": "application/json"}
data = {
    "temperature": 85.5,
    "pressure": 4.2,
    "flow_rate": 10.5,
    "heat_value": 1250.8,
    "timestamp": "2026-04-10T14:30:00",
    "unit": "°C"
}

print("测试决策API端点...")
try:
    response = requests.post(url, headers=headers, json=data)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容长度: {len(response.content)}")
    print("API端点测试成功！")
except Exception as e:
    print(f"错误: {str(e)}")
