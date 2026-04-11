# 测试会话上下文继承的脚本
import requests
import json

# API端点URL
url = "http://127.0.0.1:8001/api/v1/conversation"

# 测试数据1：第一次请求，包含阀门ID
test_data1 = {
    "session_id": "session_124",
    "message": "FV-202阀门状态如何？"
}

# 测试数据2：第二次请求，不包含阀门ID，应该自动关联前文的FV-202
test_data2 = {
    "session_id": "session_124",
    "message": "阀门状态如何？"
}

# 发送第一个POST请求
print("测试第一次请求（包含阀门ID）:")
try:
    response = requests.post(url, json=test_data1)
    response.raise_for_status()  # 检查请求是否成功
    
    # 打印响应
    print("响应状态码:", response.status_code)
    print("响应内容:", json.dumps(response.json(), ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f"测试失败: {str(e)}")

print("\n" + "="*80 + "\n")

# 发送第二个POST请求
print("测试第二次请求（不包含阀门ID，应该自动关联前文的FV-202）:")
try:
    response = requests.post(url, json=test_data2)
    response.raise_for_status()  # 检查请求是否成功
    
    # 打印响应
    print("响应状态码:", response.status_code)
    print("响应内容:", json.dumps(response.json(), ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f"测试失败: {str(e)}")
