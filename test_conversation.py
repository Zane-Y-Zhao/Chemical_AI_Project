import requests
import json

# API端点
CONVERSATION_URL = "http://127.0.0.1:8001/api/v1/conversation"

# 测试多轮对话
def test_conversation():
    print("=== 测试多轮对话端点 ===")
    
    # 会话ID
    session_id = "test_session_123"
    
    # 第一轮：询问阀门状态
    print("\n第一轮对话：")
    print("用户：阀门状态如何？")
    
    first_request = {
        "session_id": session_id,
        "message": "阀门状态如何？"
    }
    
    response = requests.post(CONVERSATION_URL, json=first_request, headers={"Content-Type": "application/json"})
    first_response = response.json()
    
    print(f"系统：{first_response['response']}")
    print(f"依据：{first_response['context_trace']}")
    
    # 第二轮：询问压力，验证上下文关联
    print("\n第二轮对话：")
    print("用户：它的压力是多少？")
    
    second_request = {
        "session_id": session_id,
        "message": "它的压力是多少？"
    }
    
    response = requests.post(CONVERSATION_URL, json=second_request, headers={"Content-Type": "application/json"})
    second_response = response.json()
    
    print(f"系统：{second_response['response']}")
    print(f"依据：{second_response['context_trace']}")
    
    # 检查第二轮响应是否关联了前文
    print("\n=== 验证结果 ===")
    if "FV-101" in second_response['response']:
        print("✅ 第二轮响应成功关联了前文的阀门ID FV-101")
    else:
        print("❌ 第二轮响应未关联前文的阀门ID")
    
    if "压力" in second_response['response']:
        print("✅ 第二轮响应包含了压力信息")
    else:
        print("❌ 第二轮响应未包含压力信息")
    
    if "依据" in second_response['context_trace']:
        print("✅ 第二轮响应包含了操作依据")
    else:
        print("❌ 第二轮响应未包含操作依据")

if __name__ == "__main__":
    test_conversation()
