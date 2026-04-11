# 测试双路径决策机制
import os
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# 配置路径
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / ".chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# 初始化向量数据库
def init_vectorstore():
    """初始化向量数据库"""
    try:
        embedding_func = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        vectorstore = Chroma(
            persist_directory=str(DB_PATH),
            embedding_function=embedding_func,
            collection_name="chem_knowledge_rag"
        )
        return vectorstore
    except Exception as e:
        print(f"向量数据库初始化失败：{str(e)}")
        return None

# 测试双路径决策机制
def test_decision_prompt():
    """测试双路径决策机制"""
    # 初始化向量数据库
    vectorstore = init_vectorstore()
    if vectorstore is None:
        print("向量数据库初始化失败，无法测试")
        return
    
    # 导入必要的函数
    from knowledge_base.prompt_engineering import build_decision_prompt, get_safety_rules
    
    # 测试用例1：高置信度（主路径）
    print("\n=== 测试用例1：高置信度（主路径）===")
    prediction_data_high = {
        "prediction": "temperature_rise",
        "confidence": 0.90,
        "timestamp": "2026-04-11T14:30:00"
    }
    
    # 检索相关知识
    retrieved_knowledge = vectorstore.similarity_search("阀门关闭条件、温度超限处置", k=2)
    safety_rules = get_safety_rules(vectorstore, top_k=1)
    
    prompt_high = build_decision_prompt(prediction_data_high, retrieved_knowledge, safety_rules)
    print("生成的提示词（主路径）：")
    print(prompt_high)
    print("\n" + "="*60 + "\n")
    
    # 测试用例2：低置信度（降级路径）
    print("\n=== 测试用例2：低置信度（降级路径）===")
    prediction_data_low = {
        "prediction": "flow_instability",
        "confidence": 0.75,
        "timestamp": "2026-04-11T14:30:00"
    }
    
    # 检索相关知识
    retrieved_knowledge = vectorstore.similarity_search("泵故障预案、流量调节逻辑", k=2)
    safety_rules = get_safety_rules(vectorstore, top_k=1)
    
    prompt_low = build_decision_prompt(prediction_data_low, retrieved_knowledge, safety_rules)
    print("生成的提示词（降级路径）：")
    print(prompt_low)
    print("\n" + "="*60 + "\n")
    
    # 测试用例3：安全熔断
    print("\n=== 测试用例3：安全熔断===")
    # 模拟不包含安全操作规程的检索结果
    # 创建一个不包含安全操作规程的文档列表
    class MockDocument:
        def __init__(self, content, metadata):
            self.page_content = content
            self.metadata = metadata
    
    mock_retrieved_knowledge = [
        MockDocument("这是一个不包含安全操作规程的文档", {"source": "杨泽彤-化工故障案例集_v1"})
    ]
    
    prompt_error = build_decision_prompt(prediction_data_high, mock_retrieved_knowledge, safety_rules)
    print("安全熔断结果：")
    print(prompt_error)
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    test_decision_prompt()
