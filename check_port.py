# 检查端口8001是否在监听的脚本
import socket

def check_port(host, port):
    """检查指定端口是否在监听"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"端口 {port} 在 {host} 上是开放的")
        else:
            print(f"端口 {port} 在 {host} 上是关闭的")
    except Exception as e:
        print(f"检查端口时出错: {str(e)}")
    finally:
        sock.close()

if __name__ == "__main__":
    check_port("127.0.0.1", 8001)
