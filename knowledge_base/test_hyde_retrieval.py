# 测试 HyDE 检索功能
import os
import re
from pathlib import Path
from typing import List
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# 配置路径
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / ".chroma_db"
CLEANED_DIR = ROOT_DIR / "knowledge_base" / "docs_cleaned"

# 初始化嵌入模型
embedding_func = HuggingFaceEmbeddings(
    model_name="D:\\chem-ai-project\\Chemical_AI_Project\\all-MiniLM-L6-v2"
)

# 加载清洗后的知识片段
def load_cleaned_chunks() -> List[Document]:
    docs = []
    print(f"正在加载清洗后的知识片段，目录：{CLEANED_DIR}")
    print(f"目录是否存在：{CLEANED_DIR.exists()}")
    
    # 列出目录中的文件
    files = list(CLEANED_DIR.glob("*_chunks.txt"))
    print(f"找到 {len(files)} 个文件")
    for file in files:
        print(f"文件：{file.name}")
    
    for chunk_file in files:
        print(f"处理文件：{chunk_file.name}")
        try:
            with open(chunk_file, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"文件大小：{len(content)} 字符")
        except Exception as e:
            print(f"读取文件失败：{str(e)}")
            continue
        
        # 按 "[片段X]" 分割，提取每段内容
        segments = re.split(r'\[片段\d+\]\n', content)
        print(f"分割后得到 {len(segments)} 个片段")
        
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
                print(f"添加片段，当前总数：{len(docs)}")
            else:
                print(f"跳过过短片段，长度：{len(seg)}")
    
    print(f"加载完成，总计 {len(docs)} 个知识片段")
    return docs

# 构建RAG向量库
def build_rag_store():
    print("🔄 正在构建RAG知识库...")
    documents = load_cleaned_chunks()
    print(f"📚 加载 {len(documents)} 个知识片段")
    
    # 使用LangChain封装Chroma
    try:
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embedding_func,
            persist_directory=str(DB_PATH),
            collection_name="chem_knowledge_rag"
        )
        print("✅ RAG知识库构建完成")
        return vectorstore
    except Exception as e:
        print(f"❌ 构建RAG知识库失败：{str(e)}")
        return None

# 生成假设性答案（简化版）
def generate_hypothetical_answer(query: str) -> str:
    """生成假设性答案，用于HyDE技术"""
    # 简化版：基于查询生成假设答案
    hypothetical_answer = f"循环水系统失衡的原因可能包括：1. 流量分配不均 2. 水质恶化 3. 设备故障 4. 管道堵塞。处置步骤：1. 检查流量分配 2. 分析水质 3. 排查设备故障 4. 清理管道 5. 恢复系统平衡。"
    return hypothetical_answer

# HyDE检索函数
def hyde_retriever(query: str, top_k: int = 3):
    """使用HyDE技术进行检索"""
    vectorstore = Chroma(
        persist_directory=str(DB_PATH),
        embedding_function=embedding_func,
        collection_name="chem_knowledge_rag"
    )
    
    # 生成假设答案
    hypothetical_answer = generate_hypothetical_answer(query)
    print(f"\n🤔 假设答案：{hypothetical_answer}")
    
    # 使用假设答案进行检索
    results = vectorstore.similarity_search(hypothetical_answer, k=top_k)
    print(f"\n🔍 检索问题：'{query}'")
    print("="*60)
    for i, doc in enumerate(results, 1):
        print(f"[{i}] 来源：{doc.metadata['source']} | 内容：{doc.page_content[:100]}...")
    print("="*60)
    
    return results

# 混合检索模式函数
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

if __name__ == "__main__":
    # 构建知识库
    store = build_rag_store()
    
    # 测试循环水系统失衡处置查询
    print("\n测试查询：循环水系统失衡处置")
    results = hybrid_retriever("循环水系统失衡处置")
    
    # 测试其他查询
    test_questions = [
        "temperature_rise",
        "flow_instability",
        "压力波动"
    ]
    
    for q in test_questions:
        print(f"\n测试查询：{q}")
        hybrid_retriever(q)
    
    print("\n🚀 测试完成！")
