import sys
import os
from pathlib import Path

# 设置根目录并添加到sys.path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from knowledge_base.prompt_engineering import build_decision_prompt, get_safety_rules

# 初始化向量数据库
DB_PATH = ROOT_DIR / ".chroma_db"
EMBEDDING_MODEL = "D:\\chem-ai-project\\Chemical_AI_Project\\all-MiniLM-L6-v2"

embedding_func = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vectorstore = Chroma(
    persist_directory=str(DB_PATH),
    embedding_function=embedding_func,
    collection_name="chem_knowledge_rag"
)

# 模拟预测数据
prediction_data = {
    "prediction": "temperature_rise",
    "confidence": 0.94,
    "timestamp": "2026-04-11T14:30:00"
}

# 测试安全熔断机制
print("测试安全熔断机制...")
print("="*50)

# 检索知识
try:
    retrieved_docs = vectorstore.similarity_search("阀门关闭条件、温度超限处置", k=2)
    print(f"检索到 {len(retrieved_docs)} 条知识依据")
    
    # 检查是否包含安全操作规程
    safety_operation_included = any("安全操作规程" in doc.metadata.get('source', '') for doc in retrieved_docs)
    print(f"是否包含安全操作规程: {safety_operation_included}")
    
    # 检索安全条款
    safety_docs = get_safety_rules(vectorstore, top_k=1)
    print(f"加载 {len(safety_docs)} 条安全条款")
    
    # 构建提示词（这会触发安全熔断）
    prompt = build_decision_prompt(prediction_data, retrieved_docs, safety_docs)
    print(f"\n构建的提示词: {prompt}")
    
    if "[ERROR]" in prompt:
        print("\n✅ 安全熔断机制触发成功！")
        print(f"错误信息: {prompt}")
    else:
        print("\n❌ 安全熔断机制未触发")
        
except Exception as e:
    print(f"\n❌ 测试失败: {str(e)}")

print("="*50)
