import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# knowledge_base/decision_pipeline.py
import json
import requests
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from knowledge_base.llm_config import call_qwen
from knowledge_base.prompt_engineering import build_decision_prompt, get_safety_rules

# 1. 配置（复用Day 1–2约定）
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / ".chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
PREDICTION_API_URL = "http://localhost:8000/docs"  # 赵元卿提供的模型服务地址

# 2. 初始化组件
embedding_func = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vectorstore = Chroma(
    persist_directory=str(DB_PATH),
    embedding_function=embedding_func,
    collection_name="chem_knowledge_rag"
)

# 3. 主函数：端到端决策生成
def generate_decision_suggestion():
    print("🔄 启动端到端决策流水线...")
    
    # Step A: 调用冯申雨预测模型（模拟真实API调用）
    try:
        # 实际部署时替换为真实请求
        # response = requests.post(PREDICTION_API_URL, json={"sensor_data": [...]})
        # prediction_data = response.json()
        
        # 当前测试：使用Day 2验证过的典型预测
        prediction_data = {
            "prediction": "temperature_rise",
            "confidence": 0.94,
            "timestamp": "2025-04-13T10:22:30Z"
        }
        print(f"✅ 获取预测数据：{prediction_data}")
    except Exception as e:
        print(f"❌ 预测API调用失败：{e}")
        return "[ERROR] 预测服务不可用"

    # Step B: 基于预测类型检索相关知识（动态关键词生成）
    prediction_type = prediction_data["prediction"]
    retrieval_keywords = {
        "temperature_rise": "阀门关闭条件、温度超限处置",
        "pressure_drop": "管道泄漏检测、压力安全阀动作",
        "flow_instability": "泵故障预案、流量调节逻辑"
    }.get(prediction_type, "安全操作边界")

    retrieved_docs = vectorstore.similarity_search(retrieval_keywords, k=2)
    print(f"✅ 检索到 {len(retrieved_docs)} 条知识依据")

    # Step C: 检索安全条款
    safety_docs = get_safety_rules(vectorstore, top_k=1)
    print(f"✅ 加载 {len(safety_docs)} 条安全条款")

    # Step D: 构建提示词并调用大模型
    prompt = build_decision_prompt(prediction_data, retrieved_docs, safety_docs)
    print("⏳ 正在调用千问大模型生成建议...")
    suggestion = call_qwen(prompt)

    # Step E: 后处理与合规校验
    if "[ERROR]" in suggestion:
        return suggestion
    
    # 强制添加溯源标记（体现协作责任）
  # Step E: 后处理与合规校验（补全部分开始）
    if "[ERROR]" in suggestion:
        return suggestion
    
    # 强制添加溯源标记（体现协作责任）
    final_output = f"""【智能建议】{suggestion}



---


📌 生成依据：
- 预测服务：冯申雨（{prediction_data['timestamp']}）
- 知识来源：韩永盛（检索关键词：{retrieval_keywords}）
- 安全条款：杨泽彤"""
    
    return final_output  # 返回完整决策建议

# 4. 主执行入口（必须补充！）
if __name__ == "__main__":
    print("="*50)
    print("🚀 化工过程智能决策系统 v1.0")
    print("="*50)
    
    # 执行流水线
    decision = generate_decision_suggestion()
    
    print("\n" + "="*50)
    print("💡 最终决策建议：")
    print(decision)
    print("="*50)