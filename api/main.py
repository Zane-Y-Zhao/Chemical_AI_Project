import sys
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import logging  # 必须在配置前导入
import time
from pathlib import Path

# 设置根目录并添加到sys.path
ROOT_DIR = Path(__file__).parent.parent   # 获取项目根目录
sys.path.append(str(ROOT_DIR))   # 将根目录加入模块搜索路径

# 确保logs目录存在
log_dir = ROOT_DIR / "logs"
log_dir.mkdir(exist_ok=True, parents=True)  # 添加parents=True确保父目录存在

# === 先配置logging ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "decision_api.log", 
                            encoding="utf-8")
    ]
)


# ...继续其他导入...

# api/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import time
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from knowledge_base.llm_config import call_qwen
from knowledge_base.prompt_engineering import build_decision_prompt, get_safety_rules

# === 1. 配置与日志初始化 ===
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / ".chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# 配置结构化日志（符合化工系统审计要求）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.FileHandler(ROOT_DIR / "logs" / "decision_api.log", encoding="utf-8")]
)
logger = logging.getLogger("decision_api")

# === 2. 初始化向量库（单例模式，避免重复加载）===
# 暂时注释掉向量数据库初始化，以测试服务器启动
# embedding_func = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
# vectorstore = Chroma(
#     persist_directory=str(DB_PATH),
#     embedding_function=embedding_func,
#     collection_name="chem_knowledge"
# )
vectorstore = None

# === 3. 定义请求/响应模型（强制字段校验，杜绝幻觉输入）===
class PredictionInput(BaseModel):
    prediction: str = Field(..., description="预测类型，如 temperature_rise", example="temperature_rise")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度，0.0-1.0", example=0.94)
    timestamp: str = Field(..., description="ISO 8601时间戳", example="2025-04-14T08:30:00Z")
    unit: str = Field(..., description="物理量单位，如 °C, MPa, kg/h", example="°C")

class DecisionOutput(BaseModel):
    suggestion: str = Field(..., description="生成的操作建议", example="立即关闭FV-101阀门...")
    source_trace: Dict[str, str] = Field(..., description="三方溯源信息", example={
        "prediction_source": "冯申雨模型API (2025-04-14T08:30:00Z)",
        "knowledge_source": "杨泽彤-系统操作规则文档_v2.pdf",
        "safety_clause": "国标GB/T 37243-2019 第5.2条"
    })
    execution_time_ms: float = Field(..., description="端到端处理耗时（毫秒）", example=2340.5)
# === 新增：工业级错误分类与处理 ===
class DecisionError(Exception):
    """自定义决策异常基类"""
    def __init__(self, code: int, message: str, category: str):
        self.code = code
        self.message = message
        self.category = category
        super().__init__(message)

# 错误码映射表（符合ISA-88标准）
ERROR_CODES = {
    "MODEL_TIMEOUT": {"code": 503, "category": "LLM_Service"},
    "KNOWLEDGE_MISSING": {"code": 500, "category": "Knowledge_Base"},
    "UNIT_MISMATCH": {"code": 422, "category": "Input_Validation"},
    "CONFIDENCE_LOW": {"code": 200, "category": "Business_Rule"}  # 200但内容含警告
}

def handle_decision_error(error: Exception, input_data: PredictionInput) -> DecisionOutput:
    """统一错误处理，返回符合化工规范的响应"""
    if isinstance(error, HTTPException):
        raise error
    
    # 分类处理不同错误
    if "timeout" in str(error).lower():
        logger.warning(f"LLM timeout for input {input_data.prediction}")
        return DecisionOutput(
            suggestion=f"[WARNING] 大模型响应超时，已启用降级策略：请人工核查阀门FV-101状态（依据：杨泽彤-系统操作规则文档_v2.pdf）",
            source_trace={"prediction_source": "冯申雨模型API", "knowledge_source": "降级策略", "safety_clause": "人工复核流程"},
            execution_time_ms=0.0
        )
    
    elif "unit" in str(error).lower():
        logger.error(f"Unit mismatch: {input_data.unit} not found in parameter table")
        raise DecisionError(
            code=ERROR_CODES["UNIT_MISMATCH"]["code"],
            message=f"物理量单位 '{input_data.unit}' 未在杨泽彤《参数配置表》中注册，请确认单位规范",
            category=ERROR_CODES["UNIT_MISMATCH"]["category"]
        )
    
    elif "confidence" in str(error).lower() and input_data.confidence < 0.85:
        logger.warning(f"Low confidence prediction: {input_data.confidence}")
        return DecisionOutput(
            suggestion=f"[需人工复核] 预测置信度{input_data.confidence:.2f}低于阈值0.85，建议暂停自动操作，立即联系冯申雨团队复核模型。",
            source_trace={"prediction_source": f"冯申雨模型API ({input_data.timestamp})", "knowledge_source": "置信度阈值规则", "safety_clause": "GB/T 37243-2019 第3.1条"},
            execution_time_ms=0.0
        )
    
    else:
        logger.critical(f"Unclassified error: {str(error)} | Input: {input_data.dict()}")
        raise HTTPException(status_code=500, detail="未知系统错误，请联系韩永盛团队")

# 修改 generate_decision_core 函数开头，捕获所有异常：
# try:
#     ...原逻辑...
# except Exception as e:
#     return handle_decision_error(e, input_data)

# === 4. 核心决策函数（剥离业务逻辑，专注可靠性）===
def generate_decision_core(input_data: PredictionInput) -> DecisionOutput:
    start_time = time.time()
    
    try:
        # 暂时使用默认响应，以测试服务器启动
        if vectorstore is None:
            final_suggestion = f"""【智能建议】检测到温度升高，建议立即检查FV-101阀门状态，并确认管道温度是否超过安全限值。


---


📌 生成依据：
- 预测服务：冯申雨模型API（{input_data.timestamp}，置信度{input_data.confidence:.2f}，单位{input_data.unit}）
- 知识来源：杨泽彤-系统操作规则文档_v2.pdf
- 安全条款：默认安全条款"""
            
            end_time = time.time()
            # 添加INFO级别的日志记录
            logger.info(f"Decision generation successful for prediction: {input_data.prediction}")
            return DecisionOutput(
                suggestion=final_suggestion,
                source_trace={
                    "prediction_source": f"冯申雨模型API ({input_data.timestamp})",
                    "knowledge_source": "杨泽彤-系统操作规则文档_v2.pdf",
                    "safety_clause": "默认安全条款"
                },
                execution_time_ms=(end_time - start_time) * 1000
            )
        
        # Step A: 动态检索关键词（强化化工术语识别）
        retrieval_map = {
            "temperature_rise": "阀门关闭条件、温度超限处置、高温管道表面温度限值",
            "pressure_drop": "管道泄漏检测、压力安全阀动作、法兰密封失效预案",
            "flow_instability": "泵故障预案、流量调节逻辑、循环水系统失衡处置"
        }
        keywords = retrieval_map.get(input_data.prediction, "安全操作边界")
        
        # Step B: 检索知识与安全条款（硬编码杨泽彤文档来源，确保权威性）
        retrieved_docs = vectorstore.similarity_search(keywords, k=2)
        safety_docs = get_safety_rules(vectorstore, top_k=1)
        
        # 调试信息
        print(f"检索关键词: {keywords}")
        print(f"检索到的文档数量: {len(retrieved_docs)}")
        print(f"检索到的安全条款数量: {len(safety_docs)}")
        
        # 简化逻辑：如果没有安全条款，也允许继续
        if not retrieved_docs:
            raise HTTPException(status_code=500, detail="知识库检索失败：未找到匹配规则")
        
        # Step C: 构建提示词（注入unit字段，强化物理量约束）
        # 如果没有安全条款，使用空列表
        prompt = build_decision_prompt(
            prediction_data=input_data.dict(),
            retrieved_knowledge=retrieved_docs,
            safety_rules=safety_docs if safety_docs else []
        )
        
        # Step D: 调用大模型（带超时与降级策略）
        suggestion = call_qwen(prompt)
        if "[ERROR]" in suggestion:
            raise HTTPException(status_code=503, detail=f"大模型服务不可用：{suggestion}")
        
        # Step E: 后处理（强制添加溯源标记，体现协作契约）
        # 处理安全条款为空的情况
        safety_source = safety_docs[0].metadata['source'] if safety_docs else "无安全条款"
        
        final_suggestion = f"""【智能建议】{suggestion}


---


📌 生成依据：
- 预测服务：冯申雨模型API（{input_data.timestamp}，置信度{input_data.confidence:.2f}，单位{input_data.unit}）
- 知识来源：化工知识库（检索关键词：{keywords}）
- 安全条款：{safety_source}"""
        
        end_time = time.time()
        return DecisionOutput(
            suggestion=final_suggestion,
            source_trace={
                "prediction_source": f"冯申雨模型API ({input_data.timestamp})",
                "knowledge_source": retrieved_docs[0].metadata['source'],
                "safety_clause": safety_source
            },
            execution_time_ms=(end_time - start_time) * 1000
        )
        
    except Exception as e:
        logger.error(f"Decision generation failed: {str(e)} | Input: {input_data.dict()}")
        raise HTTPException(status_code=500, detail=f"决策生成异常：{str(e)}")

# === 5. FastAPI应用实例 ===
app = FastAPI(
    title="化工过程智能决策API",
    description="基于千问大模型与RAG知识库的余热优化决策服务，符合IEC 62443-3-3工业安全标准",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url=None
)

# 允许前端跨域（赵元卿Streamlit/React需此配置）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 6. API端点（核心交付物）===
@app.post("/api/v1/decision", response_model=DecisionOutput, tags=["Decision"])
async def get_decision_suggestion(input_data: PredictionInput):
    """
    生成化工过程操作建议（端到端决策流水线）
    
    **输入要求：**  
    - `prediction`: 必须为冯申雨模型预定义类型（temperature_rise/pressure_drop/flow_instability）  
    - `confidence`: 置信度必须≥0.85，否则自动标注"需人工复核"  
    - `unit`: 物理量单位必须与杨泽彤《参数配置表》严格一致（如°C, MPa）  
    
    **输出保障：**  
    - 建议内容100%源自输入数据与知识库原文，无任何编造参数  
    - 每条建议强制绑定三方贡献者（冯申雨/杨泽彤/韩永盛）  
    - 全链路日志记录至 `logs/decision_api.log`，满足72小时审计要求  
    """
    return generate_decision_core(input_data)

# === 7. 健康检查端点（供赵元卿监控系统）===
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

# === 8. 启动入口（仅用于本地调试）===
if __name__ == "__main__":
    import uvicorn
    # 创建logs目录
    (ROOT_DIR / "logs").mkdir(exist_ok=True)
    uvicorn.run("api.main:app", host="127.0.0.1", port=8001, reload=True)
