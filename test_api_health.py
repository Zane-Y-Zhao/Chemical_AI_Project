import requests
import sys

# 设置标准输出编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def test_api_health():
    # 测试健康检查端点
    resp = requests.get("http://127.0.0.1:8001/health")
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    print("✅ Health check passed")
    
    # 测试决策API端点
    test_data = {
        "temperature": 85.5,
        "pressure": 4.2,
        "flow_rate": 10.5,
        "heat_value": 1250.8,
        "timestamp": "2026-04-10T14:30:00",
        "unit": "°C"
    }
    resp = requests.post("http://127.0.0.1:8001/api/v1/decision", json=test_data)
    assert resp.status_code == 200, f"Decision API failed: {resp.status_code}"
    print("✅ Decision API check passed")

if __name__ == "__main__":
    test_api_health()
