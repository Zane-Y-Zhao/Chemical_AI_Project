from locust import HttpUser, task, between, SequentialTaskSet
import json
import random

class DecisionAPITestUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def test_temperature_rise(self):
        """测试温度升高场景"""
        self.client.post("/api/v1/decision", json={
            "temperature": 85.5,
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-12T14:30:00",
            "unit": "°C"
        })
    
    @task
    def test_normal(self):
        """测试正常场景"""
        self.client.post("/api/v1/decision", json={
            "temperature": 75.0,
            "pressure": 4.0,
            "flow_rate": 10.0,
            "heat_value": 1000.0,
            "timestamp": "2026-04-12T14:35:00",
            "unit": "°C"
        })
    
    @task
    def test_pressure_drop(self):
        """测试压力下降场景"""
        self.client.post("/api/v1/decision", json={
            "temperature": 75.0,
            "pressure": 3.0,
            "flow_rate": 10.0,
            "heat_value": 1000.0,
            "timestamp": "2026-04-12T14:40:00",
            "unit": "°C"
        })
    
    @task(1)
    def test_invalid_unit(self):
        """测试无效单位场景"""
        self.client.post("/api/v1/decision", json={
            "temperature": 300,
            "pressure": 4.0,
            "flow_rate": 10.0,
            "heat_value": 1000.0,
            "timestamp": "2026-04-12T14:45:00",
            "unit": "K"
        })

class SingleUserTest(SequentialTaskSet):
    """单用户连续请求测试"""
    @task
    def test_single_user(self):
        for i in range(10):
            self.client.post("/api/v1/decision", json={
                "temperature": 85.5,
                "pressure": 4.2,
                "flow_rate": 10.5,
                "heat_value": 1250.8,
                "timestamp": f"2026-04-12T14:30:{i:02d}",
                "unit": "°C"
            })

class SingleUser(HttpUser):
    """单用户测试类"""
    tasks = [SingleUserTest]
    wait_time = between(0.5, 1)

class MixedLoadTest(SequentialTaskSet):
    """混合负载测试"""
    @task
    def test_mixed_load(self):
        # 80%正常请求，20%错误请求
        if random.random() < 0.8:
            # 正常请求
            self.client.post("/api/v1/decision", json={
                "temperature": random.uniform(70, 90),
                "pressure": random.uniform(3.5, 4.5),
                "flow_rate": random.uniform(9, 11),
                "heat_value": random.uniform(1000, 1300),
                "timestamp": "2026-04-12T14:30:00",
                "unit": "°C"
            })
        else:
            # 错误请求
            self.client.post("/api/v1/decision", json={
                "temperature": random.uniform(290, 370),
                "pressure": random.uniform(3.5, 4.5),
                "flow_rate": random.uniform(9, 11),
                "heat_value": random.uniform(1000, 1300),
                "timestamp": "2026-04-12T14:30:00",
                "unit": "K"
            })

class MixedLoadUser(HttpUser):
    """混合负载测试类"""
    tasks = [MixedLoadTest]
    wait_time = between(0.5, 1.5)
