from locust import HttpUser, task, between, LoadTestShape
import json
import random

class ChemicalAIUser(HttpUser):
    wait_time = between(0.1, 0.2)  # 模拟用户请求间隔
    
    @task(8)  # 80%的正常请求
    def normal_request(self):
        # 构造正常请求数据
        payload = {
            "temperature": random.uniform(70, 90),
            "pressure": random.uniform(3.0, 5.0),
            "flow_rate": random.uniform(8.0, 12.0),
            "heat_value": random.uniform(1200, 1300),
            "timestamp": "2026-04-11T12:00:00",
            "unit": "°C"
        }
        
        # 发送POST请求
        self.client.post("/api/v1/decision", json=payload, headers={"Content-Type": "application/json"})
    
    @task(2)  # 20%的错误请求（单位错误）
    def error_request(self):
        # 构造错误请求数据（使用K单位）
        payload = {
            "temperature": random.uniform(343, 363),  # 70-90°C in Kelvin
            "pressure": random.uniform(3.0, 5.0),
            "flow_rate": random.uniform(8.0, 12.0),
            "heat_value": random.uniform(1200, 1300),
            "timestamp": "2026-04-11T12:00:00",
            "unit": "K"
        }
        
        # 发送POST请求
        self.client.post("/api/v1/decision", json=payload, headers={"Content-Type": "application/json"})

class CustomLoadShape(LoadTestShape):
    """自定义负载测试形状"""
    stages = [
        # 场景1：单用户连续请求（模拟杨泽彤人工验证）
        {"duration": 60, "users": 1, "spawn_rate": 1},
        # 场景2：100并发请求（模拟赵元卿大屏实时刷新）
        {"duration": 120, "users": 100, "spawn_rate": 10},
        # 场景3：混合负载（80%正常请求+20%单位错误请求）
        {"duration": 180, "users": 50, "spawn_rate": 5}
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data
        
        return None
