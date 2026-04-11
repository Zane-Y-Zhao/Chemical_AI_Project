# 使用socket库直接测试API服务器的脚本
import socket

def send_http_request(host, port, path):
    """使用socket库直接发送HTTP请求"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        # 连接到服务器
        sock.connect((host, port))
        print(f"成功连接到 {host}:{port}")
        
        # 构建HTTP请求
        request = f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nConnection: close\r\n\r\n"
        
        # 发送请求
        sock.sendall(request.encode())
        print("已发送HTTP请求")
        
        # 接收响应
        response = b""
        while True:
            data = sock.recv(1024)
            if not data:
                break
            response += data
        
        # 打印响应
        print("响应状态码:", response.split(b"\r\n")[0])
        print("响应内容:", response.decode('utf-8', errors='ignore')[:500])
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
    finally:
        sock.close()

if __name__ == "__main__":
    send_http_request("127.0.0.1", 8001, "/health")
