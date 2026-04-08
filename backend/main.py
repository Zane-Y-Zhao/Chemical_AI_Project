# -*- coding: utf-8 -*-
"""
后端主程序 - main.py
注意：这段代码必须放在 backend 文件夹下
"""

# 1. 导入必要的库
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import List
from datetime import datetime
import uvicorn  # 👈 这是让 FastAPI 跑起来的引擎

# --- 👇 新增：导入跨域支持 (Day 2 新增代码) ---
from fastapi.middleware.cors import CORSMiddleware

# 2. 导入数据库配置 (确保 database.py 在同一文件夹)
from database import engine, Base, HeatData, SessionLocal

# --- 数据库初始化 (关键) ---
# 这行代码会检查数据库，如果表不存在就创建
Base.metadata.create_all(bind=engine)

# --- 创建 FastAPI 应用 ---
app = FastAPI(title="化工余热回收系统 API")

# --- 👇 第二步：配置跨域 (Day 2 新增代码) ---
# 这段代码要放在 app = FastAPI() 之后，路由定义之前
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，开发阶段用。生产环境建议改成 ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法 (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # 允许所有请求头
)

# --- 配置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 依赖项：数据库会话 ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic 模型 (数据校验) ---
# ⚠️ 重点：这里的字段名必须和 database.py 里的字段名一模一样！
# 根据你之前的 database.py，字段应该是 temperature, temp_outlet, flow_rate
from pydantic import BaseModel

class HeatDataCreate(BaseModel):
    temperature: float      # 对应 database.py 的 t1 (高温端温度)
    temp_outlet: float      # 对应 database.py 的 t2 (低温端温度)
    flow_rate: float        # 对应 database.py 的 m (质量流量)

    class Config:
        from_attributes = True

# --- 👇 Day 2 新增：用于响应查询的模型 (包含 ID 和时间) ---
class HeatDataResponse(HeatDataCreate):
    id: int
    timestamp: datetime
    heat_value: float = None  # 对应计算出的热量 Q
    description: str = None

    class Config:
        from_attributes = True

# --- API 路由 ---

@app.post("/api/v1/data", response_model=HeatDataResponse)
def create_data_point(item: HeatDataCreate, db: Session = Depends(get_db)):
    """
    接收数据并存入数据库
    """
    try:
        # 1. 创建数据库对象
        # 注意：这里直接使用传入的数据，不需要计算，直接存
        db_item = HeatData(
            temperature=item.temperature,
            temp_outlet=item.temp_outlet,
            flow_rate=item.flow_rate,
            # timestamp=datetime.now() # 数据库模型里有默认值，这里可以不填
        )

        # 2. 提交到数据库
        db.add(db_item)
        db.commit()
        db.refresh(db_item)

        logger.info(f"✅ 成功写入数据: t1={item.temperature}, t2={item.temp_outlet}")
        return db_item

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 数据库写入失败: {e}")
        raise HTTPException(status_code=500, detail="数据库写入错误")

# --- 👇 Day 2 新增：获取所有数据的接口 ---
@app.get("/api/v1/data", response_model=List[HeatDataResponse])
def get_all_data(db: Session = Depends(get_db)):
    """
    查询数据库中的所有历史数据
    前端图表需要用到这个接口
    """
    try:
        # 查询所有数据，按时间倒序排列
        data = db.query(HeatData).order_by(HeatData.timestamp.desc()).all()
        return data
    except Exception as e:
        logger.error(f"❌ 数据读取失败: {e}")
        raise HTTPException(status_code=500, detail="数据读取失败")

@app.get("/")
def read_root():
    return {"message": "化工余热回收系统已启动", "status": "running"}

# --- 主函数：程序的入口 (这就是之前缺失的点火钥匙) ---
# 当你直接运行这个文件时，执行下面的代码
if __name__ == "__main__":
    # 使用 uvicorn 启动应用
    # host="0.0.0.0" 表示允许任何网络访问
    # port=8000 表示在 8000 端口监听
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)