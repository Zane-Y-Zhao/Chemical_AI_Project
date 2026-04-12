# -*- coding: utf-8 -*-
"""
端口监控与告警工具
实时检查服务端口状态，异常时触发告警，保障系统部署安全
"""
import socket

def check_port(host, port):
    """检查指定端口是否被占用"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)  # 设置超时时间，避免卡住
    try:
        result = s.connect_ex((host, port))
        if result == 0:
            return True  # 端口被占用
        else:
            return False # 端口空闲
    finally:
        s.close()

def send_alert(message):
    """告警函数：端口异常时触发通知"""
    print(f"\n🚨 【端口告警】{message}")
    # 可扩展：钉钉/企业微信/邮件告警，示例：
    # import requests
    # requests.post("https://oapi.dingtalk.com/robot/send?access_token=xxx",
    #               json={"msgtype": "text", "text": {"content": message}})

if __name__ == "__main__":
    # 配置监控的端口（对应你的服务端口8001）
    HOST = "127.0.0.1"
    PORT = 8001

    print("=" * 50)
    print("【端口监控与告警工具】")
    print(f"正在检查 {HOST}:{PORT} 端口状态...")
    print("=" * 50)

    port_busy = check_port(HOST, PORT)
    if port_busy:
        print(f"❌ 端口 {PORT} 在 {HOST} 上是【开启/被占用】状态")
        send_alert(f"端口 {PORT} 被占用，可能导致服务部署失败，请排查占用进程！")
    else:
        print(f"✅ 端口 {PORT} 在 {HOST} 上是【关闭/空闲】状态")
        print("✅ 端口状态正常，可正常部署服务")

    print("\n" + "=" * 50)
    print("端口监控与告警检查完成")
    print("=" * 50)
