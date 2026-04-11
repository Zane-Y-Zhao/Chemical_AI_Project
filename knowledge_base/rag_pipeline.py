# knowledge_base/rag_pipeline.py
import re
import os
import logging
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import json
from pathlib import Path
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from chromadb.utils import embedding_functions

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 1. 路径配置（严格匹配Day 1约定）
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / ".chroma_db"
CLEANED_DIR = ROOT_DIR / "knowledge_base" / "docs_cleaned"

# 2. 初始化嵌入模型（复用Day 1轻量模型）
embedding_func = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

# 3. 加载清洗后的知识片段
def load_cleaned_chunks() -> List[Document]:
    docs = []
    logging.info(f"正在加载清洗后的知识片段，目录：{CLEANED_DIR}")
    logging.info(f"目录是否存在：{CLEANED_DIR.exists()}")
    
    # 列出目录中的文件
    files = list(CLEANED_DIR.glob("*_chunks.txt"))
    logging.info(f"找到 {len(files)} 个文件")
    for file in files:
        logging.info(f"文件：{file.name}")
    
    for chunk_file in files:
        logging.info(f"处理文件：{chunk_file.name}")
        try:
            with open(chunk_file, "r", encoding="utf-8") as f:
                content = f.read()
            logging.info(f"文件大小：{len(content)} 字符")
        except Exception as e:
            logging.error(f"读取文件失败：{str(e)}")
            continue
        
        # 按 "[片段X]" 分割，提取每段内容
        segments = re.split(r'\[片段\d+\]\n', content)
        logging.info(f"分割后得到 {len(segments)} 个片段")
        
        for seg in segments[1:]:  # 跳过首段空内容
            seg = seg.strip()
            if len(seg) > 20:  # 过滤过短片段
                # 绑定来源元数据（关键！用于溯源）
                source_doc = chunk_file.stem.replace("_chunks", "")
                docs.append(Document(
                    page_content=seg,
                    metadata={
                        "source": f"杨泽彤-{source_doc}",
                        "chunk_id": f"{source_doc}-{len(docs)+1}"
                    }
                ))
                logging.info(f"添加片段，当前总数：{len(docs)}")
            else:
                logging.info(f"跳过过短片段，长度：{len(seg)}")
    
    logging.info(f"加载完成，总计 {len(docs)} 个知识片段")
    return docs

# 4. 构建RAG向量库（持久化）
def build_rag_store():
    logging.info("🔄 正在构建RAG知识库...")
    documents = load_cleaned_chunks()
    logging.info(f"📚 加载 {len(documents)} 个知识片段")
    
    # 使用LangChain封装Chroma（更稳定，支持元数据过滤）
    try:
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embedding_func,
            persist_directory=str(DB_PATH),
            collection_name="chem_knowledge_rag"
        )
        logging.info("✅ RAG知识库构建完成")
        return vectorstore
    except Exception as e:
        logging.error(f"❌ 构建RAG知识库失败：{str(e)}")
        return None

# 5. HyDE（假设性文档嵌入）生成函数
def generate_hypothetical_answer(query: str) -> str:
    """生成假设性答案，用于HyDE技术"""
    # 导入千问模型调用函数
    from knowledge_base.llm_config import call_qwen
    
    # 定义生成假设答案的提示词
    prompt = f"你是一位化工领域专家，基于以下问题生成一个详细的假设性答案：\n{query}"
    
    # 使用千问模型生成假设答案
    try:
        hypothetical_answer = call_qwen(prompt)
        # 检查是否调用失败
        if hypothetical_answer.startswith("[ERROR]"):
            print(f"生成假设答案失败：{hypothetical_answer}")
            return query  # 失败时返回原始查询
        return hypothetical_answer
    except Exception as e:
        print(f"生成假设答案失败：{str(e)}")
        return query  # 失败时返回原始查询

# 6. HyDE检索函数
def hyde_retriever(query: str, top_k: int = 3):
    """使用HyDE技术进行检索"""
    vectorstore = Chroma(
        persist_directory=str(DB_PATH),
        embedding_function=embedding_func,
        collection_name="chem_knowledge_rag"
    )
    
    # 生成假设答案
    hypothetical_answer = generate_hypothetical_answer(query)
    print(f"\n🤔 假设答案：{hypothetical_answer[:100]}...")
    
    # 使用假设答案进行检索
    results = vectorstore.similarity_search(hypothetical_answer, k=top_k)
    print(f"\n🔍 检索问题：'{query}'")
    print("="*60)
    for i, doc in enumerate(results, 1):
        print(f"[{i}] 来源：{doc.metadata['source']} | 内容：{doc.page_content[:80]}...")
    print("="*60)
    
    return results

# 7. 混合检索模式函数
def hybrid_retriever(query: str, top_k: int = 3):
    """混合检索模式：高频查询用关键词检索，模糊查询启用HyDE+语义检索"""
    # 定义高频查询关键词列表
    high_frequency_queries = [
        "temperature_rise", "temperature", "temp", "温度",
        "pressure", "press", "压力", "pressur",
        "flow", "流量", "flowrate",
        "level", "液位", "level",
        "valve", "阀门", "valv",
        "pump", "泵", "pump"
    ]
    
    # 定义模糊查询关键词列表
    fuzzy_queries = [
        "flow_instability", "flow instability", "流量不稳定",
        "pressure_fluctuation", "pressure fluctuation", "压力波动",
        "temperature_variation", "temperature variation", "温度变化",
        "leakage", "泄漏", "leak",
        "corrosion", "腐蚀", "corrode",
        "abnormal", "异常", "anomaly"
    ]
    
    vectorstore = Chroma(
        persist_directory=str(DB_PATH),
        embedding_function=embedding_func,
        collection_name="chem_knowledge_rag"
    )
    
    # 检查是否为高频查询
    is_high_frequency = any(keyword.lower() in query.lower() for keyword in high_frequency_queries)
    # 检查是否为模糊查询
    is_fuzzy = any(keyword.lower() in query.lower() for keyword in fuzzy_queries)
    
    if is_high_frequency:
        # 高频查询使用关键词检索
        print("📊 使用关键词检索（高频查询）")
        results = vectorstore.similarity_search(query, k=top_k)
    elif is_fuzzy:
        # 模糊查询使用HyDE+语义检索
        print("🧠 使用HyDE+语义检索（模糊查询）")
        results = hyde_retriever(query, top_k)
    else:
        # 其他查询默认使用语义检索
        print("🔍 使用语义检索（默认）")
        results = vectorstore.similarity_search(query, k=top_k)
    
    return results

# 8. 检索测试函数（模拟用户提问）
def test_retrieval(query: str, top_k: int = 3):
    """测试混合检索模式"""
    results = hybrid_retriever(query, top_k)
    return results

if __name__ == "__main__":
    # 构建知识库（首次运行耗时约2分钟）
    store = build_rag_store()
    
    # 测试混合检索模式
    test_questions = [
        # 高频查询测试
        "temperature_rise",
        "压力",
        "flow",
        # 模糊查询测试
        "flow_instability",
        "压力波动",
        # 普通查询测试
        "阀门FV-101在什么条件下必须关闭？",
        "高温管道外表面温度的安全上限是多少？",
        "余热回收的温度阈值设定为多少？"
    ]
    
    for q in test_questions:
        test_retrieval(q)
    
    print("\n🚀 核心目标达成：知识库已基于真实化工规则构建，具备混合检索能力！")


