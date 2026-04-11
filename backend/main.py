﻿from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import socket
from datetime import datetime
import database

def is_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except socket.error:
            return False

def find_available_port(start_port=8000, max_attempts=10):
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    raise Exception(f"No available port found between {start_port} and {start_port + max_attempts - 1}")

app = FastAPI(title="化工余热回收系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class HeatDataCreate(BaseModel):
    temperature: float
    temp_outlet: float
    flow_rate: float
    description: Optional[str] = None

class HeatDataResponse(BaseModel):
    id: int
    timestamp: datetime
    temperature: float
    temp_outlet: float
    flow_rate: float
    heat_value: Optional[float] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/v1/data", response_model=HeatDataResponse)
def create_data_point(data: HeatDataCreate, db: Session = Depends(get_db)):
    db_data = database.HeatData(
        temperature=data.temperature,
        temp_outlet=data.temp_outlet,
        flow_rate=data.flow_rate,
        description=data.description
    )
    delta_t = data.temperature - data.temp_outlet
    calculated_heat = data.flow_rate * 4.18 * delta_t
    db_data.heat_value = calculated_heat
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

@app.get("/api/v1/data", response_model=List[HeatDataResponse])
def read_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    data = db.query(database.HeatData).order_by(database.HeatData.timestamp.desc()).offset(skip).limit(limit).all()
    return data

current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(current_dir, "..", "frontend")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    file_path = os.path.join(frontend_dir, "index.html")
    if not os.path.exists(file_path):
        return f"<h1>错误：找不到 index.html</h1><p>请检查路径: {file_path}</p>"
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/v1/kpi")
async def get_kpi_data():
    return {
        "temperature": 85.5,
        "pressure": 4.2,
        "heatRecovery": 1250.8,
        "energySaving": 320.5,
        "temperaturePrediction": 87.2,
        "pressurePrediction": 4.1,
        "heatRecoveryPrediction": 1280.5,
        "energySavingPrediction": 340.2
    }

@app.get("/api/v1/trends")
async def get_trend_data(days: int = 7):
    return {
        "labels": ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
        "temperature": [78, 82, 85, 88, 86, 84, 80],
        "pressure": [3.8, 4.0, 4.2, 4.3, 4.2, 4.1, 4.0],
        "heatRecovery": [1100, 1150, 1200, 1250, 1230, 1210, 1180]
    }

@app.get("/api/v1/equipment")
async def get_equipment_status():
    return [
        {"id": 1, "name": "换热器1", "status": "normal", "health": 95},
        {"id": 2, "name": "换热器2", "status": "warning", "health": 75},
        {"id": 3, "name": "泵1", "status": "normal", "health": 90},
        {"id": 4, "name": "阀门1", "status": "normal", "health": 85}
    ]

@app.get("/api/v1/alerts")
async def get_alerts():
    return [
        {
            "id": 1,
            "level": "warning",
            "message": "换热器2需要维护",
            "time": datetime.now().strftime("%H:%M:%S")
        },
        {
            "id": 2,
            "level": "info",
            "message": "系统运行正常",
            "time": datetime.now().strftime("%H:%M:%S")
        }
    ]

@app.post("/api/v1/decision")
async def get_decision_advice():
    return {
        "decision": {
            "reasoning": "基于当前余热温度85.5°C和压力4.2MPa的分析，建议调整换热器1的运行参数，以提高余热回收率。根据历史数据分析，当前工况下调整换热器1的进水流量可以提升约15%的热回收效率。",
            "source_trace": {
                "data_sources": ["传感器数据", "历史运行数据"],
                "model_used": "LSTM预测模型",
                "confidence": "0.92",
                "timestamp": datetime.now().isoformat()
            }
        }
    }

app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")
app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")

if __name__ == "__main__":
    database.init_db()
    port = find_available_port()
    print(f"启动服务器... 请访问 http://127.0.0.1:{port}")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=port)