import sys
import os
from pathlib import Path

# 设置根目录并添加到sys.path
ROOT_DIR = Path(__file__).parent   # 获取项目根目录
sys.path.append(str(ROOT_DIR))   # 将根目录加入模块搜索路径

# 直接使用chromadb库来测试向量数据库
import chromadb

# 初始化chromadb客户端
client = chromadb.PersistentClient(path=str(ROOT_DIR / ".chroma_db"))

# 获取集合
collection = client.get_collection(name="chem_knowledge_rag")

# 测试查询
query = "循环水系统失衡处置"
results = collection.query(
    query_texts=[query],
    n_results=3
)

# 显示结果
print("测试向量数据库基本检索功能")
print("="*60)
print(f"查询：{query}")
print(f"检索到 {len(results['documents'][0])} 个结果")
print()

for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
    source = meta.get('source', '未知来源')
    content = doc[:100]
    print(f"结果{i}：")
    print(f"  来源：{source}")
    print(f"  内容：{content}...")
    print()

# 检查是否召回杨泽彤案例集中对应片段
print("检索结果分析：")
print("="*60)
for i, meta in enumerate(results['metadatas'][0], 1):
    source = meta.get('source', '未知来源')
    if "杨泽彤" in source:
        print(f"✅ 片段{i}：成功召回杨泽彤案例集片段")
    else:
        print(f"❌ 片段{i}：未召回杨泽彤案例集片段")

print("\n测试完成")
