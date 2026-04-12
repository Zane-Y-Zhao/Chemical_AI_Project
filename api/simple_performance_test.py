import requests
import time
import json

BASE_URL = "http://127.0.0.1:8006/api/v1/decision"

# 测试数据
test_data = {
    "temperature": 85.5,
    "pressure": 4.2,
    "flow_rate": 10.5,
    "heat_value": 1250.8,
    "timestamp": "2026-04-12T14:30:00",
    "unit": "°C"
}

def send_request(data):
    """发送单个请求并返回响应时间和状态码"""
    start_time = time.time()
    try:
        response = requests.post(BASE_URL, json=data)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        return response_time, response.status_code, response.json()
    except Exception as e:
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        return response_time, 500, str(e)

def main():
    print("开始简化性能测试...")
    print("=" * 50)
    
    # 测试场景1：单用户连续请求
    print("=== 场景1：单用户连续请求 ===")
    response_times = []
    
    for i in range(5):
        response_time, status_code, response_data = send_request(test_data)
        response_times.append(response_time)
        print(f"请求 {i+1}: 响应时间 = {response_time:.2f}ms, 状态码 = {status_code}")
        if status_code == 200:
            print(f"  建议: {response_data.get('suggestion', 'N/A')}")
            print(f"  执行时间: {response_data.get('execution_time_ms', 'N/A')}ms")
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"\n统计结果:")
        print(f"平均响应时间: {avg_time:.2f}ms")
        print(f"最小响应时间: {min_time:.2f}ms")
        print(f"最大响应时间: {max_time:.2f}ms")
        print(f"是否满足要求（平均延迟<=600ms）: {'OK' if avg_time <= 600 else 'FAIL'}")
    
    print("=" * 50)
    print("简化性能测试完成!")

if __name__ == "__main__":
    main()
