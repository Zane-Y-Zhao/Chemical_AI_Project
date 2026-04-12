import sys
import os
from pathlib import Path

# 设置根目录并添加到sys.path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# 初始化向量数据库
DB_PATH = ROOT_DIR / ".chroma_db"
EMBEDDING_MODEL = "D:\\chem-ai-project\\Chemical_AI_Project\\all-MiniLM-L6-v2"

embedding_func = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vectorstore = Chroma(
    persist_directory=str(DB_PATH),
    embedding_function=embedding_func,
    collection_name="chem_knowledge_rag"
)

# 查看向量数据库中的文档
print("向量数据库中的文档:")
print("="*50)

# 检索所有文档
all_docs = vectorstore.similarity_search("安全操作规程", k=10)
print(f"检索到 {len(all_docs)} 条包含安全操作规程的文档")

for i, doc in enumerate(all_docs, 1):
    print(f"\n[{i}] 来源: {doc.metadata.get('source', '未知')}")
    print(f"内容: {doc.page_content[:100]}...")

print("="*50)
