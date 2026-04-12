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
logger = logging.getLogger("test_optimization")

# 测试本地缓存和超时机制
def test_local_cache():
    logger.info("测试本地缓存机制...")
    start_time = time.time()
    
    try:
        # 测试加载嵌入模型
        from langchain_huggingface import HuggingFaceEmbeddings
        
        # 设置本地缓存路径
        CACHE_DIR = os.path.join(ROOT_DIR, ".cache")
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        logger.info(f"本地缓存路径: {CACHE_DIR}")
        
        # 加载模型
        logger.info("开始加载模型...")
        embedding_func = HuggingFaceEmbeddings(
            model_name="D:\\chem-ai-project\\Chemical_AI_Project\\all-MiniLM-L6-v2",
            cache_folder=CACHE_DIR
        )
        
        # 测试模型是否加载成功
        logger.info("测试模型嵌入功能...")
        test_embedding = embedding_func.embed_query("测试嵌入")
        logger.info(f"模型加载成功，嵌入向量长度: {len(test_embedding)}")
        
        load_time = time.time() - start_time
        logger.info(f"模型加载时间: {load_time:.2f}秒")
        
        return True
    except Exception as e:
        logger.error(f"测试本地缓存失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_vectorstore():
    logger.info("测试向量数据库初始化...")
    start_time = time.time()
    
    try:
        from knowledge_base.rag_pipeline import get_vectorstore
        
        # 测试获取向量库实例
        logger.info("开始获取向量库实例...")
        vectorstore = get_vectorstore()
        
        if vectorstore is not None:
            logger.info("向量数据库初始化成功")
            
            # 测试简单检索
            logger.info("测试简单检索...")
            test_results = vectorstore.similarity_search("温度", k=2)
            logger.info(f"检索测试成功，返回 {len(test_results)} 个结果")
        else:
            logger.warning("向量数据库初始化失败")
        
        load_time = time.time() - start_time
        logger.info(f"向量数据库加载时间: {load_time:.2f}秒")
        
        return vectorstore is not None
    except Exception as e:
        logger.error(f"测试向量数据库失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("开始测试优化效果...")
    
    # 测试本地缓存
    cache_test = test_local_cache()
    
    # 测试向量数据库
    vectorstore_test = test_vectorstore()
    
    logger.info("测试完成")
    logger.info(f"本地缓存测试: {'成功' if cache_test else '失败'}")
    logger.info(f"向量数据库测试: {'成功' if vectorstore_test else '失败'}")
