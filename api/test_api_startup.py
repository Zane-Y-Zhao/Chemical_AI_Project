import sys
import os
from pathlib import Path

# 设置根目录并添加到sys.path
ROOT_DIR = Path(__file__).parent.parent   # 获取项目根目录
sys.path.append(str(ROOT_DIR))   # 将根目录加入模块搜索路径

import logging
import time

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_api_startup")

# 测试 API 服务启动
def test_api_startup():
    logger.info("测试 API 服务启动...")
    
    try:
        # 导入 main.py 中的必要组件
        from main import app, init_vectorstore
        
        # 测试初始化向量数据库
        logger.info("测试初始化向量数据库...")
        vectorstore = init_vectorstore()
        
        if vectorstore is not None:
            logger.info("向量数据库初始化成功")
        else:
            logger.warning("向量数据库初始化失败")
        
        logger.info("API 服务启动测试完成")
        return True
    except Exception as e:
        logger.error(f"API 服务启动测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("开始测试 API 服务启动...")
    
    # 测试 API 服务启动
    startup_test = test_api_startup()
    
    logger.info("测试完成")
    logger.info(f"API 服务启动测试: {'成功' if startup_test else '失败'}")
