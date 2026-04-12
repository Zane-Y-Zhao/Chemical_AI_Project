import requests
import time
import concurrent.futures
import json
import statistics

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

invalid_unit_data = {
    "temperature": 358.65,  # 85.5°C in Kelvin
    "pressure": 4.2,
    "flow_rate": 10.5,
    "heat_value": 1250.8,
    "timestamp": "2026-04-12T14:30:00",
    "unit": "K"
}

def send_request(data):
    """发送单个请求并返回响应时间和状态码"""
    start_time = time.time()
    try:
        response = requests.post(BASE_URL, json=data)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        return response_time, response.status_code
    except Exception as e:
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        return response_time, 500

def test_single_user():
    """场景1：单用户连续请求"""
    print("=== 场景1：单用户连续请求 ===")
    response_times = []
    
    for i in range(10):
        response_time, status_code = send_request(test_data)
        response_times.append(response_time)
        print(f"请求 {i+1}: 响应时间 = {response_time:.2f}ms, 状态码 = {status_code}")
    
    avg_time = statistics.mean(response_times)
    min_time = min(response_times)
    max_time = max(response_times)
    p95 = sorted(response_times)[int(len(response_times) * 0.95)]
    
    print(f"\n统计结果:")
    print(f"平均响应时间: {avg_time:.2f}ms")
    print(f"最小响应时间: {min_time:.2f}ms")
    print(f"最大响应时间: {max_time:.2f}ms")
    print(f"95% 响应时间: {p95:.2f}ms")
    print(f"是否满足要求（平均延迟≤600ms）: {'✓' if avg_time ≤ 600 else '✗'}")
    print()
    
    return avg_time

def test_concurrent_users():
    """场景2：100并发请求"""
    print("=== 场景2：100并发请求 ===")
    response_times = []
    status_codes = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(send_request, test_data) for _ in range(100)]
        for future in concurrent.futures.as_completed(futures):
            response_time, status_code = future.result()
            response_times.append(response_time)
            status_codes.append(status_code)
    
    avg_time = statistics.mean(response_times)
    min_time = min(response_times)
    max_time = max(response_times)
    p95 = sorted(response_times)[int(len(response_times) * 0.95)]
    success_rate = status_codes.count(200) / len(status_codes) * 100
    
    print(f"\n统计结果:")
    print(f"平均响应时间: {avg_time:.2f}ms")
    print(f"最小响应时间: {min_time:.2f}ms")
    print(f"最大响应时间: {max_time:.2f}ms")
    print(f"95% 响应时间: {p95:.2f}ms")
    print(f"成功率: {success_rate:.2f}%")
    print(f"是否满足要求（95百分位延迟≤800ms）: {'✓' if p95 ≤ 800 else '✗'}")
    print()
    
    return p95

def test_mixed_load():
    """场景3：混合负载（80%正常请求+20%单位错误请求）"""
    print("=== 场景3：混合负载 ===")
    response_times = []
    status_codes = []
    
    # 80个正常请求
    for _ in range(80):
        response_time, status_code = send_request(test_data)
        response_times.append(response_time)
        status_codes.append(status_code)
    
    # 20个错误请求
    for _ in range(20):
        response_time, status_code = send_request(invalid_unit_data)
        response_times.append(response_time)
        status_codes.append(status_code)
    
    avg_time = statistics.mean(response_times)
    error_response_times = [rt for rt, sc in zip(response_times, status_codes) if sc == 422]
    error_avg_time = statistics.mean(error_response_times) if error_response_times else 0
    success_rate = status_codes.count(200) / len(status_codes) * 100
    
    print(f"\n统计结果:")
    print(f"平均响应时间: {avg_time:.2f}ms")
    print(f"错误请求平均响应时间: {error_avg_time:.2f}ms")
    print(f"成功率: {success_rate:.2f}%")
    print(f"是否满足要求（错误请求响应时间≤200ms）: {'✓' if error_avg_time ≤ 200 else '✗'}")
    print(f"是否满足要求（主流程请求成功率≥99.9%）: {'✓' if success_rate ≥ 99.9 else '✗'}")
    print()
    
    return error_avg_time, success_rate

def main():
    print("开始性能测试...")
    print("=" * 50)
    
    # 测试场景1
    avg_time_single = test_single_user()
    
    # 测试场景2
    p95_concurrent = test_concurrent_users()
    
    # 测试场景3
    error_avg_time, success_rate = test_mixed_load()
    
    print("=" * 50)
    print("性能测试总结:")
    print(f"场景1（单用户）平均延迟: {avg_time_single:.2f}ms {'✓' if avg_time_single ≤ 600 else '✗'}")
    print(f"场景2（100并发）95百分位延迟: {p95_concurrent:.2f}ms {'✓' if p95_concurrent ≤ 800 else '✗'}")
    print(f"场景3（混合负载）错误请求响应时间: {error_avg_time:.2f}ms {'✓' if error_avg_time ≤ 200 else '✗'}")
    print(f"场景3（混合负载）主流程请求成功率: {success_rate:.2f}% {'✓' if success_rate ≥ 99.9 else '✗'}")
    print("=" * 50)

if __name__ == "__main__":
    main()
