import requests
import json

# API端点
DECISION_URL = "http://127.0.0.1:8001/api/v1/decision"

# 测试双路径决策响应
def test_decision_path():
    print("=== 测试双路径决策响应 ===")
    
    try:
        # 构造低置信度请求（通过温度值来模拟低置信度场景）
        print("发送低置信度(0.75)请求...")
        
        request_data = {
            "temperature": 75.0,  # 温度适中，可能会触发低置信度
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2023-01-01T00:00:00",
            "unit": "°C"
        }
        
        print(f"发送请求：{json.dumps(request_data, ensure_ascii=False)}")
        response = requests.post(DECISION_URL, json=request_data, headers={"Content-Type": "application/json"})
        print(f"响应状态码：{response.status_code}")
        
        if response.status_code == 200:
            decision_response = response.json()
            print("\n=== 响应结果 ===")
            print(f"状态：{decision_response['status']}")
            print(f"建议：{decision_response['suggestion']}")
            print(f"决策：{decision_response['decision']['action']}")
            print(f"置信度：{decision_response['source_trace']['confidence']}")
            
            # 检查是否同时包含生成建议与案例集原文
            print("\n=== 验证结果 ===")
            if "智能建议" in decision_response['suggestion']:
                print("✅ 响应包含生成建议")
            else:
                print("❌ 响应未包含生成建议")
            
            if "检索到的知识片段" in decision_response['suggestion']:
                print("✅ 响应包含案例集原文")
            else:
                print("❌ 响应未包含案例集原文")
            
            if decision_response['source_trace']['confidence'] <= 0.75:
                print("✅ 置信度≤0.75，符合测试要求")
            else:
                print(f"❌ 置信度{decision_response['source_trace']['confidence']} > 0.75，不符合测试要求")
        else:
            print(f"请求失败：{response.text}")
    
    except Exception as e:
        print(f"测试过程中出现错误：{str(e)}")

if __name__ == "__main__":
    test_decision_path()
