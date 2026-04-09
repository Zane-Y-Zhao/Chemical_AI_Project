# backend/database.py

import os
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# --- 1. 数据库配置与WAL模式优化 ---
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "heat_recovery.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# 创建引擎：启用WAL模式以支持高并发读写
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # connect_args 中的设置会直接传递给 DBAPI
    connect_args={
        "check_same_thread": False,  # 允许多线程访问（FastAPI默认多线程）
    },
    # --- 连接池优化 (基于2026最佳实践) ---
    pool_size=10,          # 基础连接池大小
    max_overflow=20,       # 爆发时最多创建的额外连接数
    pool_timeout=60,       # 获取连接的超时时间(秒)
    pool_pre_ping=True,    # 每次获取连接前进行有效性检测，防止断连
    echo=False             # 生产环境建议关闭SQL日志
)

# --- 2. 会话工厂 ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 3. 数据模型定义 (包含关键索引) ---
class HeatData(Base):
    __tablename__ = "heat_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now, index=True) # 增加索引
    temperature = Column(Float, nullable=False)
    temp_outlet = Column(Float, nullable=False)
    flow_rate = Column(Float, nullable=False)
    heat_value = Column(Float, nullable=True)
    description = Column(String, nullable=True)

    # 定义复合索引，优化基于温度和时间的联合查询
    __table_args__ = (
        Index("ix_temp_outlet", "temp_outlet"),
        Index("ix_temperature_timestamp", "temperature", "timestamp"), # 常见查询模式
    )

# --- 4. 初始化函数 (用于main.py) ---
def init_db():
    # 启用WAL模式 (在连接建立后执行)
    # 注意：SQLAlchemy 的 connect_args 不直接支持 PRAGMA，需通过事件监听或初始化时执行
    # 这里我们提供一个初始化函数供 main.py 调用
    with engine.connect() as con:
        con.execute("PRAGMA journal_mode=WAL;") # 核心：开启WAL模式
        con.execute("PRAGMA busy_timeout=5000;") # 设置忙碌超时
        con.commit()
    Base.metadata.create_all(bind=engine)