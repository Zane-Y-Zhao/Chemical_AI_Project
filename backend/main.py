# -*- coding: utf-8 -*-
"""
主程序 - main.py (修正版)
功能：后端服务器，接收数据，提供API，托管前端
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os

# --- 1. 导入数据库配置 ---
import database

# --- 关键修复：必须显式导入 datetime ---
from datetime import datetime

# --- 2. 初始化 FastAPI ---
app = FastAPI(title="化工余热回收系统")

# --- 3. 配置跨域 (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（仅用于开发环境）
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. Pydantic 数据模型 ---

# 用于接收前端POST数据的模型
class HeatDataCreate(BaseModel):
    temperature: float
    temp_outlet: float
    flow_rate: float
    description: Optional[str] = None

# 用于返回给前端GET数据的模型
class HeatDataResponse(BaseModel):
    id: int
    timestamp: datetime  # 这里使用了 datetime，所以必须在上面导入
    temperature: float
    temp_outlet: float
    flow_rate: float
    heat_value: Optional[float] = None
    description: Optional[str] = None

    class Config:
        # 关键配置：允许从ORM对象（SQLAlchemy模型）直接读取数据
        from_attributes = True

# --- 5. 数据库依赖项 ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 6. API 路由：接收数据 (POST) ---
@app.post("/api/v1/data", response_model=HeatDataResponse)
def create_data_point(data: HeatDataCreate, db: Session = Depends(get_db)):
    # 创建数据库模型实例
    db_data = database.HeatData(
        temperature=data.temperature,
        temp_outlet=data.temp_outlet,
        flow_rate=data.flow_rate,
        description=data.description
    )

    # 计算热量
    delta_t = data.temperature - data.temp_outlet
    calculated_heat = data.flow_rate * 4.18 * delta_t
    db_data.heat_value = calculated_heat

    # 写入数据库
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

# --- 7. API 路由：获取所有数据 (GET) ---
@app.get("/api/v1/data", response_model=List[HeatDataResponse])
def read_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取历史数据，用于前端图表展示
    """
    # 按时间倒序排列，最新的在前面
    data = db.query(database.HeatData).order_by(database.HeatData.timestamp.desc()).offset(skip).limit(limit).all()
    return data

# --- 8. 首页路由 ---
@app.get("/", response_class=HTMLResponse)
async def read_index():
    # 动态获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 假设 frontend 文件夹在 backend 的上一级目录
    frontend_dir = os.path.join(current_dir, "..", "frontend")

    file_path = os.path.join(frontend_dir, "index.html")

    if not os.path.exists(file_path):
        return f"<h1>错误：找不到 index.html</h1><p>请检查路径: {file_path}</p>"

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# --- 9. 启动命令 ---
if __name__ == "__main__":
    print("启动服务器... 请访问 http://127.0.0.1:8000")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)