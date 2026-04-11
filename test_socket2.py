# 使用socket库直接测试API服务器的脚本
import socket

def send_http_request(host, port, path, method="GET", headers={}, body=""):
    """使用socket库直接发送HTTP请求"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        # 连接到服务器
        sock.connect((host, port))
        print(f"成功连接到 {host}:{port}")
        
        # 构建HTTP请求
        request_lines = [f"{method} {path} HTTP/1.1"]
        request_lines.append(f"Host: {host}:{port}")
        request_lines.append("Connection: close")
        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")
        if body:
            request_lines.append(f"Content-Length: {len(body)}")
        request_lines.append("")
        if body:
            request_lines.append(body)
        request = "\r\n".join(request_lines)
        
        # 发送请求
        sock.sendall(request.encode())
        print("已发送HTTP请求")
        print("请求内容:")
        print(request)
        
        # 接收响应
        response = b""
        while True:
            data = sock.recv(1024)
            if not data:
                break
            response += data
        
        # 打印响应
        print("\n响应状态码:", response.split(b"\r\n")[0])
        print("响应内容:", response.decode('utf-8', errors='ignore')[:1000])
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
    finally:
        sock.close()

if __name__ == "__main__":
    # 测试健康检查端点
    print("测试健康检查端点:")
    send_http_request("127.0.0.1", 8001, "/health")
    
    print("\n" + "="*80 + "\n")
    
    # 测试会话管理端点
    print("测试会话管理端点:")
    headers = {"Content-Type": "application/json"}
    body = '{"session_id": "session_123", "message": "FV-101阀门状态如何？"}'
    send_http_request("127.0.0.1", 8001, "/api/v1/conversation", "POST", headers, body)
