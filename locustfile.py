from locust import HttpUser, task, between
import json
import time

class DecisionApiUser(HttpUser):
    wait_time = between(0.1, 0.2)  # 模拟用户请求间隔
    
    @task
    def get_decision(self):
        # 构造请求数据
        payload = {
            "temperature": 85.5,
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "unit": "°C"
        }
        
        # 发送POST请求
        self.client.post("/api/v1/decision", json=payload, headers={"Content-Type": "application/json"})
