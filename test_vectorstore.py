import sys
import os
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 设置根目录并添加到sys.path
ROOT_DIR = Path(__file__).parent   # 获取项目根目录
sys.path.append(str(ROOT_DIR))   # 将根目录加入模块搜索路径

logging.info(f"项目根目录: {ROOT_DIR}")

# 检查向量数据库目录
DB_PATH = ROOT_DIR / ".chroma_db"
logging.info(f"向量数据库目录: {DB_PATH}")
logging.info(f"向量数据库目录是否存在: {DB_PATH.exists()}")

# 列出向量数据库目录中的文件
if DB_PATH.exists():
    files = list(DB_PATH.iterdir())
    logging.info(f"向量数据库目录中的文件: {[f.name for f in files]}")

# 导入必要的模块
try:
    from langchain_community.vectorstores import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    logging.info("成功导入LangChain模块")
except Exception as e:
    logging.error(f"导入LangChain模块失败: {str(e)}")
    sys.exit(1)

# 初始化向量数据库
try:
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    logging.info(f"嵌入模型: {EMBEDDING_MODEL}")
    
    embedding_func = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    logging.info("成功初始化嵌入模型")
    
    vectorstore = Chroma(
        persist_directory=str(DB_PATH),
        embedding_function=embedding_func,
        collection_name="chem_knowledge_rag"
    )
    logging.info("成功初始化向量数据库")
    
except Exception as e:
    logging.error(f"初始化向量数据库失败: {str(e)}")
    sys.exit(1)

# 测试基本检索功能
try:
    logging.info("开始测试向量数据库基本检索功能")
    
    # 测试查询
    query = "循环水系统失衡处置"
    logging.info(f"查询：{query}")
    
    # 执行检索
    results = vectorstore.similarity_search(query, k=3)
    logging.info(f"检索到 {len(results)} 个结果")
    
    # 显示检索结果
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get('source', '未知来源')
        content = doc.page_content[:100]
        logging.info(f"结果{i}：")
        logging.info(f"  来源：{source}")
        logging.info(f"  内容：{content}...")
    
    # 检查是否召回杨泽彤案例集中对应片段
    logging.info("开始分析检索结果")
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get('source', '未知来源')
        if "杨泽彤" in source:
            logging.info(f"✅ 片段{i}：成功召回杨泽彤案例集片段")
        else:
            logging.info(f"❌ 片段{i}：未召回杨泽彤案例集片段")
    
    logging.info("测试完成")
    
except Exception as e:
    logging.error(f"测试失败: {str(e)}")
    sys.exit(1)
