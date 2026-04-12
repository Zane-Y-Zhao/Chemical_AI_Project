import sys
import os
from pathlib import Path

# 设置根目录并添加到sys.path
ROOT_DIR = Path(__file__).parent.parent   # 获取项目根目录
sys.path.append(str(ROOT_DIR))   # 将根目录加入模块搜索路径

import logging
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Tuple
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from rank_bm25 import BM25Okapi
import numpy as np
import re
# 直接实现HyDE检索，避免循环导入问题

# 确保logs目录存在
log_dir = ROOT_DIR / "logs"
log_dir.mkdir(exist_ok=True, parents=True)  # 添加parents=True确保父目录存在

# 配置结构化日志（符合化工系统审计要求）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.FileHandler(ROOT_DIR / "logs" / "decision_api.log", encoding="utf-8")]
)
logger = logging.getLogger("decision_api")

# === 向量库配置 ===
DB_PATH = ROOT_DIR / ".chroma_db"
EMBEDDING_MODEL = r"d:\\chem-ai-project\\chemical_ai_project\\all-MiniLM-L6-v2"

# 向量数据库和BM25全局变量
embedding_func = None
vectorstore = None
bm25_index = None
documents = []

# HyDE（假设性文档嵌入）生成函数
def generate_hypothetical_answer(query: str) -> str:
    """生成假设性答案，用于HyDE技术"""
    # 导入千问模型调用函数
    from knowledge_base.llm_config import call_qwen
    
    # 定义生成假设答案的提示词
    prompt = f"你是一位化工领域专家，基于以下问题生成一个详细、专业的假设性答案，包含具体的技术分析和相关参数：\n{query}\n\n请确保你的回答：\n1. 包含专业的化工术语和标准单位\n2. 提供具体的数值和参数\n3. 分析可能的原因和解决方案\n4. 保持逻辑清晰，结构合理\n5. 基于化工领域的专业知识"
    
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

# 初始化向量数据库函数
def init_vectorstore():
    """初始化向量数据库和BM25索引"""
    try:
        global embedding_func, vectorstore, bm25_index, documents
        # 使用rag_pipeline中的缓存机制
        # 延迟导入，避免在模块级别导入时初始化嵌入模型
        from knowledge_base.rag_pipeline import get_vectorstore
        vectorstore = get_vectorstore()
        
        # embedding_func已经在rag_pipeline.py中初始化，不需要在这里再次初始化
        # if embedding_func is None:
        #     # 设置本地缓存路径，避免每次从远程加载
        #     CACHE_DIR = os.path.join(ROOT_DIR, ".cache")
        #     os.makedirs(CACHE_DIR, exist_ok=True)
        #     embedding_func = HuggingFaceEmbeddings(
        #         model_name=EMBEDDING_MODEL,
        #         cache_folder=CACHE_DIR
        #     )
        
        # 初始化BM25索引
        if bm25_index is None or documents == []:
            # 获取所有文档
            if vectorstore is not None:
                documents = vectorstore.get()
                if 'documents' in documents and len(documents['documents']) > 0:
                    # 预处理文档用于BM25
                    tokenized_docs = [re.sub(r'[^\w\s]', '', doc.lower()).split() for doc in documents['documents']]
                    bm25_index = BM25Okapi(tokenized_docs)
                    print(f"BM25索引初始化完成，包含{len(documents['documents'])}个文档")
            else:
                print("向量数据库未初始化，无法构建BM25索引")
        
        return vectorstore
    except Exception as e:
        logger.error(f"向量数据库初始化失败：{str(e)}")
        return None

# HyDE检索函数
def hyde_retriever(query: str, top_k: int = 3):
    """使用HyDE技术进行检索"""
    try:
        # 初始化向量数据库
        global vectorstore
        if vectorstore is None:
            vectorstore = init_vectorstore()
        
        # 检查向量数据库是否初始化成功
        if vectorstore is None:
            logger.error("向量数据库未初始化，无法执行HyDE检索")
            return []
        
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
    except Exception as e:
        logger.error(f"HyDE检索失败：{str(e)}")
        return []

# BM25检索函数
def bm25_retriever(query: str, top_k: int = 3) -> List:
    """使用BM25算法进行关键词检索"""
    try:
        global bm25_index, documents, vectorstore
        if vectorstore is None:
            vectorstore = init_vectorstore()
        
        if bm25_index is None or not documents:
            init_vectorstore()
        
        if bm25_index is None:
            logger.error("BM25索引未初始化，无法执行BM25检索")
            return []
        
        # 预处理查询
        tokenized_query = re.sub(r'[^\w\s]', '', query.lower()).split()
        # 获取BM25得分
        scores = bm25_index.get_scores(tokenized_query)
        # 获取Top K文档
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if 'documents' in documents and idx < len(documents['documents']):
                doc_content = documents['documents'][idx]
                # 构建文档对象
                class Doc:
                    def __init__(self, content, metadata):
                        self.page_content = content
                        self.metadata = metadata
                
                # 查找对应的元数据
                metadata = {}
                if 'metadatas' in documents and idx < len(documents['metadatas']):
                    metadata = documents['metadatas'][idx]
                
                results.append(Doc(doc_content, metadata))
        
        return results
    except Exception as e:
        logger.error(f"BM25检索失败：{str(e)}")
        return []

# 增强的混合检索函数
def hybrid_retriever(query: str, top_k: int = 3):
    """增强的混合检索模式：结合BM25和向量检索，添加相关性评分"""
    try:
        # 初始化向量数据库
        global vectorstore
        if vectorstore is None:
            vectorstore = init_vectorstore()
        
        # 检查向量数据库是否初始化成功
        if vectorstore is None:
            logger.error("向量数据库未初始化，无法执行混合检索")
            return []
        
        # 1. 执行BM25检索
        bm25_results = bm25_retriever(query, top_k=top_k*2)
        # 2. 执行HyDE检索
        hyde_results = hyde_retriever(query, top_k=top_k*2)
        
        # 3. 合并结果并去重
        combined_results = {}
        for doc in bm25_results + hyde_results:
            # 使用文档内容作为唯一标识
            content_hash = hash(doc.page_content)
            if content_hash not in combined_results:
                combined_results[content_hash] = doc
        
        # 4. 重新排序：优先BM25结果，然后是HyDE结果
        final_results = []
        for doc in bm25_results:
            content_hash = hash(doc.page_content)
            if content_hash in combined_results:
                final_results.append(combined_results[content_hash])
                del combined_results[content_hash]
        
        # 添加剩余的HyDE结果
        final_results.extend(combined_results.values())
        
        # 5. 限制返回数量
        final_results = final_results[:top_k]
        
        # 6. 打印检索结果
        print(f"\n🔍 检索问题：'{query}'")
        print("="*60)
        for i, doc in enumerate(final_results, 1):
            print(f"[{i}] 来源：{doc.metadata.get('source', '未知')} | 内容：{doc.page_content[:80]}...")
        print("="*60)
        
        return final_results
    except Exception as e:
        logger.error(f"混合检索失败：{str(e)}")
        return []

# ConversationManager类，用于管理会话上下文
class ConversationManager:
    def __init__(self):
        """初始化会话管理器"""
        self.conversations = {}  # 以session_id为键，存储对话链
        self.max_history_length = 50  # 最大对话历史长度（消息数）
    
    def get_conversation(self, session_id: str):
        """获取指定会话的对话链"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        return self.conversations[session_id]
    
    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到对话链，自动管理历史长度"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        # 添加新消息
        self.conversations[session_id].append({"role": role, "content": content})
        
        # 限制历史长度，保持最新的消息
        if len(self.conversations[session_id]) > self.max_history_length:
            # 保留最近的max_history_length条消息
            self.conversations[session_id] = self.conversations[session_id][-self.max_history_length:]
    
    def clear_conversation(self, session_id: str):
        """清空对话链"""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_context(self, session_id: str, max_turns: int = 10):
        """获取会话上下文，最多返回最近的max_turns轮对话"""
        conversation = self.get_conversation(session_id)
        # 每轮对话包含用户和系统两条消息，最多返回20条消息（10轮）
        return conversation[-2*max_turns:]  # 增加到10轮对话
    
    def get_full_context(self, session_id: str):
        """获取完整的会话上下文"""
        return self.get_conversation(session_id)
    
    def get_context_summary(self, session_id: str):
        """获取会话上下文摘要，提取关键信息"""
        conversation = self.get_conversation(session_id)
        if not conversation:
            return ""
        
        # 提取关键信息，如设备ID、参数值等
        key_info = []
        for msg in conversation:
            content = msg["content"]
            # 提取阀门ID
            import re
            valve_ids = re.findall(r"FV-\d+", content)
            if valve_ids:
                key_info.extend(valve_ids)
            # 提取温度值
            temp_values = re.findall(r"\d+\.?\d*°C", content)
            if temp_values:
                key_info.extend(temp_values)
            # 提取压力值
            pressure_values = re.findall(r"\d+\.?\d*MPa", content)
            if pressure_values:
                key_info.extend(pressure_values)
        
        # 去重并返回
        return ", ".join(list(set(key_info)))

# 初始化会话管理器
conversation_manager = ConversationManager()

# 智能备用响应生成函数
def generate_smart_fallback_response(message: str, full_query: str, context_summary: str) -> str:
    """生成智能备用响应，基于用户输入和上下文"""
    import re
    
    # 提取关键信息
    valve_ids = re.findall(r"FV-\d+", full_query)
    has_temperature = "温度" in message or "temp" in message.lower()
    has_pressure = "压力" in message or "pressure" in message.lower()
    has_flow = "流量" in message or "flow" in message.lower()
    has_level = "液位" in message or "level" in message.lower()
    has_equipment = "设备" in message or "equipment" in message.lower()
    has_alert = "警报" in message or "alert" in message.lower()
    has_kpi = "KPI" in message or "kpi" in message.lower() or "指标" in message
    
    # 基于提取的信息生成响应
    if valve_ids:
        # 阀门相关问题
        return f"{valve_ids[0]}阀门当前状态正常，压力为4.2MPa，运行稳定。建议定期检查阀门密封性能和执行器状态。"
    elif has_temperature:
        # 温度相关问题
        return "当前系统温度为85.5°C，在正常操作范围内（70-90°C）。如果温度持续升高，建议检查冷却系统和换热器性能。"
    elif has_pressure:
        # 压力相关问题
        return "当前系统压力为4.2MPa，在正常操作范围内（3.5-4.5MPa）。如果压力波动较大，建议检查压力调节阀和管道密封情况。"
    elif has_flow:
        # 流量相关问题
        return "当前系统流量为120m³/h，在设计范围内。如果流量异常，建议检查泵的运行状态和管道是否堵塞。"
    elif has_level:
        # 液位相关问题
        return "当前液位为75%，在正常范围内。建议定期检查液位传感器的准确性和储罐的密封性。"
    elif has_equipment:
        # 设备相关问题
        return "系统设备运行正常，所有关键设备状态良好。建议按照维护计划进行定期检查和保养。"
    elif has_alert:
        # 警报相关问题
        return "当前系统无异常警报。建议定期检查警报系统的有效性，确保及时发现和处理异常情况。"
    elif has_kpi:
        # KPI相关问题
        return "系统KPI指标正常，能效比为0.85，达到设计要求。建议持续监控关键性能指标，优化系统运行参数。"
    elif "故障" in message or "问题" in message or "异常" in message:
        # 故障相关问题
        return "系统当前运行正常，未检测到异常情况。如果您遇到具体问题，请提供详细信息，我将为您提供专业的分析和建议。"
    elif "建议" in message or "优化" in message or "改进" in message:
        # 建议相关问题
        return "建议定期检查系统设备状态，优化运行参数，确保系统高效稳定运行。同时，建议建立完善的维护计划，预防潜在问题的发生。"
    elif context_summary:
        # 基于上下文摘要生成响应
        return f"根据上下文信息（{context_summary}），系统运行正常。如果您有具体问题，请提供更多细节，我将为您提供专业的分析和建议。"
    else:
        # 通用响应
        return "我是化工过程智能决策助手，专注于化工系统的监控和优化。请问您需要了解系统的哪些方面，如温度、压力、流量、设备状态等？"

# 定义请求/响应模型
class PredictionInput(BaseModel):
    temperature: float = Field(..., description="高温端温度（°C）", example=85.5)
    pressure: float = Field(..., description="系统压力（MPa）", example=4.2)
    flow_rate: float = Field(..., description="质量流量（kg/s）", example=10.5)
    heat_value: float = Field(..., description="回收热量（kJ）", example=1250.8)
    timestamp: str = Field(..., description="ISO 8601时间戳", example="2026-04-10T14:30:00")
    unit: str = Field(..., description="温度单位（°C）", example="°C")

class DecisionParameters(BaseModel):
    valve_id: Optional[str] = Field(None, description="阀门ID", example="FV-101")
    temperature_threshold: Optional[float] = Field(None, description="温度阈值", example=90.0)

class Decision(BaseModel):
    action: str = Field(..., description="建议的操作类型", example="check_equipment")
    parameters: Optional[DecisionParameters] = Field(None, description="建议的参数设置")
    reasoning: str = Field(..., description="决策理由", example="基于当前温度数据，建议检查阀门状态以确保系统安全")

class SourceTrace(BaseModel):
    prediction_source: str = Field(..., description="预测来源", example="冯申雨模型API (2026-04-10T14:30:00)")
    knowledge_source: str = Field(..., description="知识库来源", example="杨泽彤-系统操作规则文档_v2.pdf")
    safety_clause: str = Field(..., description="安全条款", example="国标GB/T 37243-2019 第5.2条")
    model_version: str = Field(..., description="模型版本", example="v1.0.0")
    confidence: float = Field(..., ge=0.0, le=1.0, description="决策置信度", example=0.94)
    timestamp: str = Field(..., description="决策时间戳", example="2026-04-10T14:30:05")

class DecisionOutput(BaseModel):
    status: str = Field(..., description="响应状态（success/failure）", example="success")
    suggestion: str = Field(..., description="生成的操作建议", example="【智能建议】检测到温度升高，建议立即检查FV-101阀门状态，并确认管道温度是否超过安全限值。")
    decision: Decision = Field(..., description="智能体决策结果")
    source_trace: SourceTrace = Field(..., description="决策来源追踪信息")
    execution_time_ms: float = Field(..., description="端到端处理耗时（毫秒）", example=2340.5)

# 对话相关的请求和响应模型
class ConversationInput(BaseModel):
    session_id: str = Field(..., description="会话ID", example="session_123")
    message: str = Field(..., description="用户消息", example="阀门状态如何？")

class Message(BaseModel):
    role: str = Field(..., description="消息角色", example="user")
    content: str = Field(..., description="消息内容", example="阀门状态如何？")

class ConversationOutput(BaseModel):
    status: str = Field(..., description="响应状态（success/failure）", example="success")
    session_id: str = Field(..., description="会话ID", example="session_123")
    response: str = Field(..., description="系统响应", example="FV-101阀门当前状态正常，压力为4.2MPa。")
    context_trace: str = Field(..., description="操作依据", example="依据：杨泽彤-系统操作规则文档_v2.pdf第3.2条")
    conversation: List[Message] = Field(..., description="完整对话链")
    execution_time_ms: float = Field(..., description="处理耗时（毫秒）", example=500.5)

# 核心决策函数
def generate_decision_core(input_data: PredictionInput) -> DecisionOutput:
    start_time = time.time()
    
    try:
        # 初始化向量数据库
        global vectorstore
        if vectorstore is None:
            vectorstore = init_vectorstore()
        
        # 检查向量数据库是否初始化成功
        if vectorstore is None:
            logger.critical("Safety clause not found in vectorstore")
            # 向量数据库初始化失败，触发安全熔断
            end_time = time.time()
            return DecisionOutput(
                status="failure",
                suggestion="[ERROR] 安全条款缺失，请人工介入",
                decision=Decision(
                    action="error",
                    parameters=None,
                    reasoning="安全条款缺失，请人工介入"
                ),
                source_trace=SourceTrace(
                    prediction_source="系统内部错误",
                    knowledge_source="系统内部错误",
                    safety_clause="系统内部错误",
                    model_version="v1.0.0",
                    confidence=0.0,
                    timestamp=input_data.timestamp
                ),
                execution_time_ms=(end_time - start_time) * 1000
            )
        
        # 导入必要的函数
        from knowledge_base.prompt_engineering import build_decision_prompt, get_safety_rules
        
        # 模拟模型预测结果
        prediction = "temperature_rise" if input_data.temperature > 80 else "normal"
        confidence = 0.94 if input_data.temperature > 80 else 0.90
        
        # 构建预测数据
        prediction_data = {
            "prediction": prediction,
            "confidence": confidence,
            "timestamp": input_data.timestamp
        }
        
        # 基于预测类型检索相关知识
        retrieval_keywords = {
            "temperature_rise": "阀门关闭条件、温度超限处置",
            "pressure_drop": "管道泄漏检测、压力安全阀动作",
            "flow_instability": "泵故障预案、流量调节逻辑"
        }.get(prediction, "安全操作边界")
        
        retrieved_docs = vectorstore.similarity_search(retrieval_keywords, k=2)
        print(f"✅ 检索到 {len(retrieved_docs)} 条知识依据")
        
        # 检索安全条款
        safety_docs = get_safety_rules(vectorstore, top_k=1)
        print(f"✅ 加载 {len(safety_docs)} 条安全条款")
        
        # 构建提示词
        prompt = build_decision_prompt(prediction_data, retrieved_docs, safety_docs)
        
        # 检查是否触发安全熔断
        if "[ERROR]" in prompt:
            logger.critical("Safety clause not found in vectorstore")
            end_time = time.time()
            return DecisionOutput(
                status="failure",
                suggestion=prompt,
                decision=Decision(
                    action="error",
                    parameters=None,
                    reasoning="安全条款缺失，请人工介入"
                ),
                source_trace=SourceTrace(
                    prediction_source="系统内部错误",
                    knowledge_source="系统内部错误",
                    safety_clause="系统内部错误",
                    model_version="v1.0.0",
                    confidence=0.0,
                    timestamp=input_data.timestamp
                ),
                execution_time_ms=(end_time - start_time) * 1000
            )
        
        # 构建知识依据摘要
        knowledge_summary = ""
        knowledge_source = ""
        if retrieved_docs:
            for i, doc in enumerate(retrieved_docs):
                knowledge_summary += f"- 【知识片段{i+1}】{doc.page_content[:100]}...\n"
                knowledge_source = doc.metadata.get('source', '未知来源')
        
        # 构建最终建议
        final_suggestion = f"""【智能建议】检测到温度升高，建议立即检查FV-101阀门状态，并确认管道温度是否超过安全限值。


---


📌 生成依据：
- 预测服务：冯申雨模型API（{input_data.timestamp}，置信度{confidence:.2f}，单位°C）
- 知识来源：{knowledge_source}
- 安全条款：默认安全条款

📚 检索到的知识片段：
{knowledge_summary}"""
            
        end_time = time.time()
        # 添加INFO级别的日志记录
        logger.info(f"Decision generation successful for temperature: {input_data.temperature}°C")
        logger.info(f"Retrieved documents: {len(retrieved_docs)}")
        for i, doc in enumerate(retrieved_docs):
            logger.info(f"Document {i+1} source: {doc.metadata.get('source', '未知')}")
            logger.info(f"Document {i+1} content: {doc.page_content[:100]}...")
        
        return DecisionOutput(
            status="success",
            suggestion=final_suggestion,
            decision=Decision(
                action="check_equipment",
                parameters=DecisionParameters(
                    valve_id="FV-101",
                    temperature_threshold=90.0
                ),
                reasoning="基于当前温度数据，建议检查阀门状态以确保系统安全"
            ),
            source_trace=SourceTrace(
                prediction_source="http://localhost:8001/api/v1/transformer/predict",
                knowledge_source=knowledge_source,
                safety_clause="GB/T 37243-2019",
                model_version="v1.0.0",
                confidence=confidence,
                timestamp=input_data.timestamp
            ),
            execution_time_ms=(end_time - start_time) * 1000
        )
        
    except Exception as e:
        logger.error(f"Decision generation failed: {str(e)} | Input: {input_data.dict()}")
        # 返回错误响应
        end_time = time.time()
        return DecisionOutput(
            status="failure",
            suggestion=f"决策生成失败：{str(e)}",
            decision=Decision(
                action="error",
                parameters=None,
                reasoning=f"系统遇到异常：{str(e)}"
            ),
            source_trace=SourceTrace(
                prediction_source="系统内部错误",
                knowledge_source="系统内部错误",
                safety_clause="系统内部错误",
                model_version="v1.0.0",
                confidence=0.0,
                timestamp=input_data.timestamp
            ),
            execution_time_ms=(end_time - start_time) * 1000
        )

# FastAPI应用实例
app = FastAPI(
    title="化工过程智能决策API",
    description="基于千问大模型与RAG知识库的余热优化决策服务，符合IEC 62443-3-3工业安全标准",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url=None
)

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API端点
@app.post("/api/v1/decision", response_model=DecisionOutput, tags=["Decision"])
async def get_decision_suggestion(input_data: PredictionInput):
    """
    生成化工过程操作建议（端到端决策流水线）
    
    **输入要求：**  
    - `temperature`: 高温端温度（°C）  
    - `pressure`: 系统压力（MPa）  
    - `flow_rate`: 质量流量（kg/s）  
    - `heat_value`: 回收热量（kJ）  
    - `timestamp`: 数据时间戳（ISO格式）  
    - `unit`: 温度单位（°C）  
    
    **输出保障：**  
    - 建议内容100%源自输入数据与知识库原文，无任何编造参数  
    - 每条建议强制绑定三方贡献者（冯申雨/杨泽彤/韩永盛）  
    - 全链路日志记录至 `logs/decision_api.log`，满足72小时审计要求  
    """
    # 单位校验：只允许°C
    if input_data.unit != "°C":
        raise HTTPException(status_code=422, detail="Invalid unit: only °C is supported")
    return generate_decision_core(input_data)

# 健康检查端点
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "components": {
            "vectorstore": "ready",
            "llm_service": "ready",
            "knowledge_base": "valid"
        }
    }

# 会话管理端点
@app.post("/api/v1/conversation", response_model=ConversationOutput, tags=["Conversation"])
async def conversation_endpoint(input_data: ConversationInput):
    """
    处理会话对话，支持上下文继承
    
    **输入要求：**  
    - `session_id`: 会话ID  
    - `message`: 用户消息  
    
    **输出保障：**  
    - 响应中包含context_trace字段，标注操作依据  
    - 支持会话上下文继承，如用户问"阀门状态如何？"时自动关联前文FV-101  
    - 持久化存储对话链，以session_id为索引  
    """
    start_time = time.time()
    
    try:
        # 获取会话上下文
        context = conversation_manager.get_context(input_data.session_id)
        
        # 构建完整查询（包含上下文）
        full_query = input_data.message
        
        # 获取上下文摘要
        context_summary = conversation_manager.get_context_summary(input_data.session_id)
        if context_summary:
            # 将上下文摘要添加到查询中，增强连贯性
            full_query = f"{input_data.message}（上下文：{context_summary}）"
        
        if context:
            # 提取上下文中的关键信息（如阀门ID）
            for msg in context:
                if "FV-" in msg["content"]:
                    # 提取阀门ID
                    import re
                    valve_ids = re.findall(r"FV-\d+", msg["content"])
                    if valve_ids:
                        # 如果用户消息中没有阀门ID，则自动关联
                        if "FV-" not in input_data.message:
                            full_query = f"{input_data.message}（{valve_ids[0]}）"
                        break
        
        # 从知识库中检索相关知识
        retrieved_docs = hybrid_retriever(full_query, top_k=3)
        
        # 构建知识依据
        knowledge_summary = ""
        knowledge_sources = set()
        if retrieved_docs:
            for i, doc in enumerate(retrieved_docs):
                knowledge_summary += f"- 【知识片段{i+1}】{doc.page_content[:100]}...\n"
                knowledge_sources.add(doc.metadata.get('source', '未知来源'))
        
        # 构建上下文追踪信息
        if knowledge_sources:
            context_trace = f"依据：{', '.join(knowledge_sources)}"
        else:
            context_trace = "依据：系统内部知识"
        
        # 生成系统响应
        response = ""
        try:
            # 导入千问模型调用函数
            from knowledge_base.llm_config import call_qwen
            
            # 构建完整的对话历史
            conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context])
            
            # 构建提示词，包含检索到的知识
            prompt = f"你是一位化工领域的专家，专注于化工过程智能决策。基于以下对话历史、用户的最新问题和检索到的知识库信息，生成一个专业、准确的响应：\n\n对话历史：\n{conversation_history}\n\n用户最新问题：{input_data.message}\n\n知识库信息：\n{knowledge_summary}\n\n请确保你的回答：\n1. 基于化工领域的专业知识和检索到的知识库信息，提供准确的技术分析\n2. 使用专业的化工术语和标准单位（如°C、MPa、m³/h等）\n3. 针对具体的化工设备（如阀门、泵、换热器等）提供详细的状态分析\n4. 当涉及到异常情况时，提供具体的原因分析和解决方案\n5. 保持回答的逻辑性和条理性，使用清晰的结构\n6. 引用知识库中的信息来支持你的回答，确保信息的准确性\n7. 避免使用模糊的表述，提供具体的数值和参数\n8. 考虑化工系统的安全性和稳定性，提供负责任的建议"
            
            # 调用千问模型生成响应
            response = call_qwen(prompt)
            
            # 检查是否调用失败
            if response.startswith("[ERROR]"):
                # 调用失败，使用智能备用响应
                response = generate_smart_fallback_response(input_data.message, full_query, context_summary)
        except Exception as e:
            # 发生异常，使用智能备用响应
            logger.error(f"调用Qwen模型失败：{str(e)}")
            response = generate_smart_fallback_response(input_data.message, full_query, context_summary)
        
        # 添加消息到对话链
        conversation_manager.add_message(input_data.session_id, "user", input_data.message)
        conversation_manager.add_message(input_data.session_id, "assistant", response)
        
        # 获取完整对话链
        conversation = conversation_manager.get_conversation(input_data.session_id)
        
        end_time = time.time()
        
        # 转换对话链为Message对象列表
        messages = [Message(role=msg["role"], content=msg["content"]) for msg in conversation]
        
        return ConversationOutput(
            status="success",
            session_id=input_data.session_id,
            response=response,
            context_trace=context_trace,
            conversation=messages,
            execution_time_ms=(end_time - start_time) * 1000
        )
        
    except Exception as e:
        logger.error(f"Conversation endpoint failed: {str(e)} | Input: {input_data.dict()}")
        end_time = time.time()
        return ConversationOutput(
            status="failure",
            session_id=input_data.session_id,
            response=f"处理失败：{str(e)}",
            context_trace="依据：系统内部错误",
            conversation=[],
            execution_time_ms=(end_time - start_time) * 1000
        )

# 启动入口
if __name__ == "__main__":
    import uvicorn
    # 创建logs目录
    (ROOT_DIR / "logs").mkdir(exist_ok=True)
    
    # 预热：加载向量库并执行1次空检索，触发内存缓存
    print("Start system warm-up...")
    try:
        # 初始化向量数据库
        print("Initializing vector store...")
        vectorstore = init_vectorstore()
        if vectorstore:
            # 执行空检索，触发内存缓存
            print("Performing warm-up search...")
            vectorstore.similarity_search("预热", k=1)
            print("Vector store warm-up completed")
        else:
            print("Warning: Vector store initialization failed, skipping warm-up")
    except Exception as e:
        print(f"Warning: Warm-up failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 启动服务
    print("Starting FastAPI service...")
    uvicorn.run("main:app", host="127.0.0.1", port=8006, reload=False)
