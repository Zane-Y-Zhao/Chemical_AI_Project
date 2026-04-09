import requests
import time
import random

url = "http://127.0.0.1:8000/api/v1/data"

print("🚀 传感器模拟器启动，正在向后端发送数据...")

while True:
    # 模拟波动的数据
    temp_in = round(random.uniform(85, 95), 2)
    temp_out = round(random.uniform(60, 70), 2)
    flow = round(random.uniform(4.5, 5.5), 2)
    
    data = {
        "temperature": temp_in,
        "temp_outlet": temp_out,
        "flow_rate": flow,
        "description": "自动模拟数据"
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ 发送成功: {data}")
        else:
            print(f"❌ 发送失败: {response.text}")
    except Exception as e:
        print(f"⚠️ 连接错误，请确保后端 main.py 正在运行: {e}")
        
    time.sleep(2) # 每2秒发一次