import requests
import json

# API端点
CONVERSATION_URL = "http://127.0.0.1:8001/api/v1/conversation"

# 测试多轮对话
def test_conversation():
    print("=== 测试多轮对话端点 ===")
    
    # 会话ID
    session_id = "test_session_456"
    
    try:
        # 第一轮：询问阀门状态
        print("\n第一轮对话：")
        print("用户：阀门状态如何？")
        
        first_request = {
            "session_id": session_id,
            "message": "阀门状态如何？"
        }
        
        print(f"发送请求：{json.dumps(first_request, ensure_ascii=False)}")
        response = requests.post(CONVERSATION_URL, json=first_request, headers={"Content-Type": "application/json"})
        print(f"响应状态码：{response.status_code}")
        
        if response.status_code == 200:
            first_response = response.json()
            print(f"系统：{first_response['response']}")
            print(f"依据：{first_response['context_trace']}")
        else:
            print(f"请求失败：{response.text}")
        
        # 第二轮：询问压力，验证上下文关联
        print("\n第二轮对话：")
        print("用户：它的压力是多少？")
        
        second_request = {
            "session_id": session_id,
            "message": "它的压力是多少？"
        }
        
        print(f"发送请求：{json.dumps(second_request, ensure_ascii=False)}")
        response = requests.post(CONVERSATION_URL, json=second_request, headers={"Content-Type": "application/json"})
        print(f"响应状态码：{response.status_code}")
        
        if response.status_code == 200:
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
        else:
            print(f"请求失败：{response.text}")
    
    except Exception as e:
        print(f"测试过程中出现错误：{str(e)}")

if __name__ == "__main__":
    test_conversation()
