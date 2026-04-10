import sys
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from knowledge_base.rag_pipeline import Chroma, SentenceTransformerEmbeddings
from knowledge_base.prompt_engineering import build_decision_prompt, get_safety_rules

# 加载RAG库
embedding_func = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(
    persist_directory=".chroma_db",
    embedding_function=embedding_func,
    collection_name="chem_knowledge_rag"
)

# 模拟冯申雨预测数据（真实场景将由API获取）
mock_prediction = {
    "prediction": "temperature_rise",
    "confidence": 0.94,
    "timestamp": "2025-04-13T10:22:30Z"
}

# 检索相关知识与安全条款
retrieved = vectorstore.similarity_search("FV-101关闭条件", k=2)
safety_rules = get_safety_rules(vectorstore)

# 生成最终提示词
final_prompt = build_decision_prompt(mock_prediction, retrieved, safety_rules)
print("🔍 生成的提示词：\n" + "="*80)
print(final_prompt[:500] + "...")
