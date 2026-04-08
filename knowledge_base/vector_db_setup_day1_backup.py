# knowledge_base/vector_db_setup.py
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

# 1. 配置路径
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / ".chroma_db"  # 向量数据库存储位置

# 2. 初始化数据库
client = chromadb.PersistentClient(path=str(DB_PATH))
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"  # 自动下载模型
)

# 3. 创建集合
collection = client.get_or_create_collection(
    name="chem_knowledge",
    embedding_function=embedding_func
)

# 4. 加载模拟化工文档（示例）
sample_docs = [
    {"content": "余热回收温度阈值为100°C。低于此温度，烟气余热回收效率急剧下降。", "source": "杨泽彤-参数配置表"},
    {"content": "阀门开关逻辑：A-101温度>150°C且压力>2.5MPa时关闭FV-101。", "source": "杨泽彤-操作规则文档"},
    {"content": "安全规范：高温管道外表面温度不得超过60°C。", "source": "化工安全操作规程"}
]
documents = [doc["content"] for doc in sample_docs]

# 5. 存入向量库
collection.add(
    documents=documents,
    ids=[f"doc_{i}" for i in range(len(sample_docs))],
    metadatas=sample_docs
)

# 6. 测试检索
results = collection.query(
    query_texts=["阀门关闭条件是什么？"],
    n_results=1
)
print("✅ 检索结果:", results['documents'][0][0][:50] + "...")  # 打印前50字符
print(f"🎯 数据库已存入 {len(documents)} 个文档片段")
