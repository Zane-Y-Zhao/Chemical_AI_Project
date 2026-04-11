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
logging.info(f"Python路径: {sys.path}")

# 检查必要的模块是否安装
try:
    from langchain_community.vectorstores import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    logging.info("成功导入LangChain模块")
except Exception as e:
    logging.error(f"导入LangChain模块失败: {str(e)}")
    sys.exit(1)

# 初始化向量数据库
try:
    DB_PATH = ROOT_DIR / ".chroma_db"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    logging.info(f"向量数据库路径: {DB_PATH}")
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

# HyDE（假设性文档嵌入）生成函数
def generate_hypothetical_answer(query: str) -> str:
    """生成假设性答案，用于HyDE技术"""
    logging.info(f"生成假设答案，查询: {query}")
    # 导入千问模型调用函数
    try:
        from knowledge_base.llm_config import call_qwen
        logging.info("成功导入call_qwen函数")
    except Exception as e:
        logging.error(f"导入call_qwen函数失败: {str(e)}")
        return query  # 失败时返回原始查询
    
    # 定义生成假设答案的提示词
    prompt = f"你是一位化工领域专家，基于以下问题生成一个详细的假设性答案：\n{query}"
    
    # 使用千问模型生成假设答案
    try:
        hypothetical_answer = call_qwen(prompt)
        # 检查是否调用失败
        if hypothetical_answer.startswith("[ERROR]"):
            logging.error(f"生成假设答案失败：{hypothetical_answer}")
            return query  # 失败时返回原始查询
        logging.info(f"成功生成假设答案: {hypothetical_answer[:100]}...")
        return hypothetical_answer
    except Exception as e:
        logging.error(f"生成假设答案失败：{str(e)}")
        return query  # 失败时返回原始查询

# HyDE检索函数
def hyde_retriever(query: str, top_k: int = 3):
    """使用HyDE技术进行检索"""
    logging.info(f"开始HyDE检索，查询: {query}")
    # 生成假设答案
    hypothetical_answer = generate_hypothetical_answer(query)
    logging.info(f"假设答案: {hypothetical_answer[:100]}...")
    
    # 使用假设答案进行检索
    try:
        results = vectorstore.similarity_search(hypothetical_answer, k=top_k)
        logging.info(f"成功检索到 {len(results)} 个结果")
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get('source', '未知来源')
            content = doc.page_content[:80]
            logging.info(f"结果{i}: 来源={source}, 内容={content}...")
        return results
    except Exception as e:
        logging.error(f"检索失败：{str(e)}")
        return []

# 测试HyDE检索
if __name__ == "__main__":
    logging.info("开始测试HyDE模式检索：循环水系统失衡处置")
    query = "循环水系统失衡处置"
    results = hyde_retriever(query, top_k=3)
    
    # 检查是否召回杨泽彤案例集中对应片段
    logging.info("开始分析检索结果")
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get('source', '未知来源')
        if "杨泽彤" in source:
            logging.info(f"✅ 片段{i}：成功召回杨泽彤案例集片段，来源={source}")
        else:
            logging.info(f"❌ 片段{i}：未召回杨泽彤案例集片段，来源={source}")
    
    logging.info("测试完成")
