# -*- coding: utf-8 -*-
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

# --- 1. 日志配置 ---
# 配置日志格式：时间 - 级别 - 消息
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),  # 写入文件
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

# --- 2. 创建应用实例 ---
app = FastAPI(title="化工余热回收系统 API", version="1.0.0")

# --- 3. 导入数据库配置 ---
# 注意：确保 database.py 和 main.py 在同一目录下
from database import engine, Base

# --- 4. 定义数据模型 (Pydantic) ---
# 用于 API 请求和响应的数据校验
class DataInput(BaseModel):
    temperature: float
    pressure: float
    flow_rate: float

class DataOutput(DataInput):
    id: int
    timestamp: str

    class Config:
        # 允许从 ORM 模式读取数据（配合 SQLAlchemy 使用）
        from_attributes = True

# --- 5. 数据库表初始化 ---
# 创建所有定义的表（如果不存在）
Base.metadata.create_all(bind=engine)
logger.info("✅ 数据库表初始化完成")

# --- 6. 全局异常处理 ---
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"❌ 未捕获的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "服务器内部错误，请稍后再试"}
    )

# --- 7. 定义 API 路由 ---

@app.get("/")
def read_root():
    logger.info("访问了根路径 /")
    return {"Message": "赵元卿的系统后端已启动", "Status": "Running"}

# 模拟数据接口 (暂时用假数据演示)
@app.get("/api/v1/data", response_model=List[DataOutput])
def get_data():
    logger.info("获取数据列表请求")
    # TODO: 这里后续替换为真实的数据库查询语句
    return [
        {"id": 1, "timestamp": "2026-04-07 14:00:00", "temperature": 350.5, "pressure": 2.3, "flow_rate": 120.0},
        {"id": 2, "timestamp": "2026-04-07 14:01:00", "temperature": 352.1, "pressure": 2.4, "flow_rate": 121.5}
    ]

@app.post("/api/v1/data", response_model=DataOutput)
def add_data(item: DataInput):
    logger.info(f"收到新数据: {item}")
    # TODO: 这里后续替换为真实的数据库插入语句
    return {"id": 99, "timestamp": "2026-04-07 14:25:00", **item.dict()}