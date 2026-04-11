import time
import subprocess
import requests

# 启动API服务器
print("启动API服务器...")
api_process = subprocess.Popen(["python", "api/main.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# 等待服务器启动
time.sleep(5)

# 检查服务器是否启动成功
try:
    response = requests.get("http://127.0.0.1:8001/health")
    if response.status_code == 200:
        print("✅ API服务器启动成功！")
        print("健康检查响应：", response.json())
        
        # 测试决策API
        print("\n测试决策API...")
        payload = {
            "temperature": 85.5,
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "unit": "°C"
        }
        response = requests.post("http://127.0.0.1:8001/api/v1/decision", json=payload, headers={"Content-Type": "application/json"})
        print("决策API响应状态码：", response.status_code)
        print("决策API响应内容：", response.json())
    else:
        print("❌ API服务器启动失败，健康检查返回状态码：", response.status_code)
except Exception as e:
    print("❌ API服务器启动失败，无法连接：", str(e))
    
    # 查看服务器启动日志
    stdout, stderr = api_process.communicate()
    print("\n服务器启动日志：")
    print(stdout.decode('utf-8'))
    print("\n服务器启动错误：")
    print(stderr.decode('utf-8'))
finally:
    # 终止API服务器
    api_process.terminate()
    try:
        api_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        api_process.kill()
