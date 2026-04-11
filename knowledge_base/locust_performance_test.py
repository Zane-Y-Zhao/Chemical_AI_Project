from locust import HttpUser, task, between
import time

class RAGRetrievalUser(HttpUser):
    wait_time = between(0.5, 1.5)
    
    @task
    def test_hybrid_retrieval(self):
        """测试混合检索模式的性能"""
        # 测试高频查询
        high_freq_queries = [
            "temperature_rise",
            "压力",
            "flow"
        ]
        
        # 测试模糊查询
        fuzzy_queries = [
            "flow_instability",
            "压力波动"
        ]
        
        # 测试普通查询
        normal_queries = [
            "循环水系统失衡处置",
            "阀门FV-101在什么条件下必须关闭？"
        ]
        
        # 随机选择一个查询类型
        import random
        query_type = random.choice(["high_freq", "fuzzy", "normal"])
        
        if query_type == "high_freq":
            query = random.choice(high_freq_queries)
        elif query_type == "fuzzy":
            query = random.choice(fuzzy_queries)
        else:
            query = random.choice(normal_queries)
        
        # 发送请求到 API 端点
        # 注意：这里需要根据实际的 API 端点进行调整
        # 假设 API 端点为 /api/v1/retrieve
        self.client.post("/api/v1/retrieve", json={"query": query})

    @task(2)
    def test_temperature_rise(self):
        """测试 temperature_rise 高频查询的性能"""
        self.client.post("/api/v1/retrieve", json={"query": "temperature_rise"})

    @task
    def test_flow_instability(self):
        """测试 flow_instability 模糊查询的性能"""
        self.client.post("/api/v1/retrieve", json={"query": "flow_instability"})

if __name__ == "__main__":
    import subprocess
    # 启动 locust 测试，模拟100并发用户
    subprocess.run([
        "locust",
        "-f", "locust_performance_test.py",
        "--host", "http://127.0.0.1:8007",  # 假设 API 服务运行在 8007 端口
        "--users", "100",
        "--spawn-rate", "10",
        "--run-time", "60s",  # 运行60秒
        "--headless",
        "--csv", "performance_results"
    ])
