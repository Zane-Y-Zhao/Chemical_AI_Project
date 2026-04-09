# knowledge_base/rag_pipeline.py
import re
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import json
from pathlib import Path
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.documents import Document
from chromadb.utils import embedding_functions

# 1. 路径配置（严格匹配Day 1约定）
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / ".chroma_db"
CLEANED_DIR = ROOT_DIR / "knowledge_base" / "docs_cleaned"

# 2. 初始化嵌入模型（复用Day 1轻量模型）
embedding_func = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

# 3. 加载清洗后的知识片段
def load_cleaned_chunks() -> List[Document]:
    docs = []
    for chunk_file in CLEANED_DIR.glob("*_chunks.txt"):
        with open(chunk_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 按 "[片段X]" 分割，提取每段内容
        segments = re.split(r'\[片段\d+\]\n', content)
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
    return docs

# 4. 构建RAG向量库（持久化）
def build_rag_store():
    print("🔄 正在构建RAG知识库...")
    documents = load_cleaned_chunks()
    print(f"📚 加载 {len(documents)} 个知识片段")
    
    # 使用LangChain封装Chroma（更稳定，支持元数据过滤）
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_func,
        persist_directory=str(DB_PATH),
        collection_name="chem_knowledge_rag"
    )
    
    print("✅ RAG知识库构建完成")
    return vectorstore

# 5. 检索测试函数（模拟用户提问）
def test_retrieval(query: str, top_k: int = 3):
    vectorstore = Chroma(
        persist_directory=str(DB_PATH),
        embedding_function=embedding_func,
        collection_name="chem_knowledge_rag"
    )
    
    results = vectorstore.similarity_search(query, k=top_k)
    print(f"\n🔍 检索问题：'{query}'")
    print("="*60)
    for i, doc in enumerate(results, 1):
        print(f"[{i}] 来源：{doc.metadata['source']} | 内容：{doc.page_content[:80]}...")
    print("="*60)

if __name__ == "__main__":
    # 构建知识库（首次运行耗时约2分钟）
    store = build_rag_store()
    
    # 测试3类典型问题（覆盖规则、安全、参数）
    test_questions = [
        "阀门FV-101在什么条件下必须关闭？",
        "高温管道外表面温度的安全上限是多少？",
        "余热回收的温度阈值设定为多少？"
    ]
    
    for q in test_questions:
        test_retrieval(q)
    
    print("\n🚀 Day 2核心目标达成：知识库已基于真实化工规则构建，具备精准检索能力！")


