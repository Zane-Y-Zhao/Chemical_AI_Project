import time
import json
import concurrent.futures
import requests
import statistics

# API端点
API_URL = "http://127.0.0.1:8001/api/v1/decision"

# 构造正常请求数据
def get_normal_payload():
    import random
    return {
        "temperature": random.uniform(70, 90),
        "pressure": random.uniform(3.0, 5.0),
        "flow_rate": random.uniform(8.0, 12.0),
        "heat_value": random.uniform(1200, 1300),
        "timestamp": "2026-04-11T12:00:00",
        "unit": "°C"
    }

# 构造错误请求数据（单位错误）
def get_error_payload():
    import random
    return {
        "temperature": random.uniform(343, 363),  # 70-90°C in Kelvin
        "pressure": random.uniform(3.0, 5.0),
        "flow_rate": random.uniform(8.0, 12.0),
        "heat_value": random.uniform(1200, 1300),
        "timestamp": "2026-04-11T12:00:00",
        "unit": "K"
    }

# 发送请求
def send_request(payload):
    start_time = time.time()
    try:
        response = requests.post(API_URL, json=payload, headers={"Content-Type": "application/json"})
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # 转换为毫秒
        return {
            "status": response.status_code,
            "latency": latency,
            "time": start_time
        }
    except Exception as e:
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # 转换为毫秒
        return {
            "status": 500,
            "latency": latency,
            "error": str(e),
            "time": start_time
        }

# 场景1：单用户连续请求（模拟杨泽彤人工验证）
def test_scenario_1(duration=60):
    print("=== 场景1：单用户连续请求 ===")
    print(f"测试持续时间：{duration}秒")
    
    start_time = time.time()
    latencies = []
    requests_count = 0
    
    while time.time() - start_time < duration:
        payload = get_normal_payload()
        result = send_request(payload)
        latencies.append(result["latency"])
        requests_count += 1
        time.sleep(0.1)  # 模拟用户思考时间
    
    # 计算性能指标
    if latencies:
        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        print(f"总请求数：{requests_count}")
        print(f"平均延迟：{avg_latency:.2f} 毫秒")
        print(f"95百分位延迟：{p95_latency:.2f} 毫秒")
        print(f"最大延迟：{max_latency:.2f} 毫秒")
        print(f"最小延迟：{min_latency:.2f} 毫秒")
        
        # 验证是否达标
        if avg_latency <= 600:
            print("✅ 平均延迟≤600ms，达标")
        else:
            print("❌ 平均延迟>600ms，未达标")
    else:
        print("❌ 未收集到测试数据")

# 场景2：100并发请求（模拟赵元卿大屏实时刷新）
def test_scenario_2(concurrent_users=100, total_requests=1000):
    print("\n=== 场景2：100并发请求 ===")
    print(f"并发用户数：{concurrent_users}")
    print(f"总请求数：{total_requests}")
    
    latencies = []
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = []
        for _ in range(total_requests):
            payload = get_normal_payload()
            futures.append(executor.submit(send_request, payload))
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            latencies.append(result["latency"])
            
            # 每100个请求打印一次进度
            if len(latencies) % 100 == 0:
                print(f"已完成 {len(latencies)}/{total_requests} 个请求")
    
    # 计算性能指标
    if latencies:
        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = total_requests / total_time
        
        print(f"总耗时：{total_time:.2f} 秒")
        print(f"吞吐量：{throughput:.2f} 请求/秒")
        print(f"平均延迟：{avg_latency:.2f} 毫秒")
        print(f"95百分位延迟：{p95_latency:.2f} 毫秒")
        print(f"最大延迟：{max_latency:.2f} 毫秒")
        print(f"最小延迟：{min_latency:.2f} 毫秒")
        
        # 验证是否达标
        if p95_latency <= 800:
            print("✅ 95百分位延迟≤800ms，达标")
        else:
            print("❌ 95百分位延迟>800ms，未达标")
    else:
        print("❌ 未收集到测试数据")

# 场景3：混合负载（80%正常请求+20%单位错误请求）
def test_scenario_3(concurrent_users=50, total_requests=1000):
    print("\n=== 场景3：混合负载 ===")
    print(f"并发用户数：{concurrent_users}")
    print(f"总请求数：{total_requests}")
    print("请求比例：80%正常请求 + 20%单位错误请求")
    
    latencies = []
    error_latencies = []
    success_count = 0
    error_count = 0
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = []
        for i in range(total_requests):
            # 80%的正常请求，20%的错误请求
            if i % 5 != 0:  # 80%的概率
                payload = get_normal_payload()
            else:  # 20%的概率
                payload = get_error_payload()
            futures.append(executor.submit(send_request, payload))
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            latencies.append(result["latency"])
            
            if result["status"] == 200:
                success_count += 1
            elif result["status"] == 422:
                error_latencies.append(result["latency"])
                error_count += 1
            
            # 每100个请求打印一次进度
            if len(latencies) % 100 == 0:
                print(f"已完成 {len(latencies)}/{total_requests} 个请求")
    
    # 计算性能指标
    if latencies:
        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = total_requests / total_time
        success_rate = (success_count / total_requests) * 100
        
        print(f"总耗时：{total_time:.2f} 秒")
        print(f"吞吐量：{throughput:.2f} 请求/秒")
        print(f"平均延迟：{avg_latency:.2f} 毫秒")
        print(f"95百分位延迟：{p95_latency:.2f} 毫秒")
        print(f"最大延迟：{max_latency:.2f} 毫秒")
        print(f"最小延迟：{min_latency:.2f} 毫秒")
        print(f"成功请求数：{success_count}")
        print(f"错误请求数：{error_count}")
        print(f"成功率：{success_rate:.2f}%")
        
        # 验证错误请求响应时间
        if error_latencies:
            avg_error_latency = statistics.mean(error_latencies)
            print(f"错误请求平均响应时间：{avg_error_latency:.2f} 毫秒")
            if avg_error_latency <= 200:
                print("✅ 错误请求响应时间≤200ms，达标")
            else:
                print("❌ 错误请求响应时间>200ms，未达标")
        else:
            print("⚠️  未收集到错误请求数据")
        
        # 验证主流程请求成功率
        if success_rate >= 99.9:
            print("✅ 主流程请求成功率≥99.9%，达标")
        else:
            print("❌ 主流程请求成功率<99.9%，未达标")
    else:
        print("❌ 未收集到测试数据")

# 检查日志文件中是否有CRITICAL级别错误
def check_logs():
    print("\n=== 检查日志文件 ===")
    
    log_file = "logs/decision_api.log"
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            logs = f.read()
            
        if "CRITICAL" in logs:
            print("❌ 日志文件中存在CRITICAL级别错误")
        else:
            print("✅ 日志文件中无CRITICAL级别错误")
    except Exception as e:
        print(f"⚠️  无法读取日志文件：{str(e)}")

if __name__ == "__main__":
    # 检查API服务是否可用
    print("检查API服务状态...")
    try:
        response = requests.get("http://127.0.0.1:8001/health")
        if response.status_code == 200:
            print("✅ API服务正常运行")
        else:
            print(f"❌ API服务状态异常：{response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ API服务不可用：{str(e)}")
        exit(1)
    
    # 运行场景测试
    test_scenario_1()
    test_scenario_2()
    test_scenario_3()
    
    # 检查日志
    check_logs()
    
    print("\n=== 性能压测完成 ===")
