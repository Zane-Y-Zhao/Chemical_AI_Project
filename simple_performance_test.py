import time
import json
import requests

# API端点
API_URL = "http://127.0.0.1:8001/api/v1/decision"

# 构造请求数据
def get_payload():
    return {
        "temperature": 85.5,
        "pressure": 4.2,
        "flow_rate": 10.5,
        "heat_value": 1250.8,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "unit": "°C"
    }

# 发送请求
def send_request():
    start_time = time.time()
    try:
        response = requests.post(API_URL, json=get_payload(), headers={"Content-Type": "application/json"})
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

# 性能测试
def run_performance_test(total_requests=100):
    print(f"开始性能测试：共 {total_requests} 个请求")
    
    latencies = []
    start_time = time.time()
    
    for i in range(total_requests):
        result = send_request()
        latencies.append(result["latency"])
        
        # 每10个请求打印一次进度
        if (i + 1) % 10 == 0:
            print(f"已完成 {i + 1}/{total_requests} 个请求")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # 计算性能指标
    latencies.sort()
    avg_latency = sum(latencies) / len(latencies)
    p95_latency = latencies[int(len(latencies) * 0.95)]
    max_latency = max(latencies)
    min_latency = min(latencies)
    
    # 计算吞吐量
    throughput = total_requests / total_time
    
    # 打印测试结果
    print("\n性能测试结果：")
    print(f"总请求数：{total_requests}")
    print(f"总耗时：{total_time:.2f} 秒")
    print(f"吞吐量：{throughput:.2f} 请求/秒")
    print(f"平均延迟：{avg_latency:.2f} 毫秒")
    print(f"95百分位延迟：{p95_latency:.2f} 毫秒")
    print(f"最大延迟：{max_latency:.2f} 毫秒")
    print(f"最小延迟：{min_latency:.2f} 毫秒")
    
    # 检查是否达标
    avg_latency_ok = avg_latency <= 600
    p95_latency_ok = p95_latency <= 800
    
    print("\n达标检查：")
    print(f"平均延迟≤600ms：{'✅ 达标' if avg_latency_ok else '❌ 未达标'}")
    print(f"95百分位延迟≤800ms：{'✅ 达标' if p95_latency_ok else '❌ 未达标'}")
    
    if avg_latency_ok and p95_latency_ok:
        print("\n🎉 所有性能指标均达标！")
    else:
        print("\n⚠️  部分性能指标未达标，请优化系统。")

if __name__ == "__main__":
    run_performance_test(total_requests=100)
