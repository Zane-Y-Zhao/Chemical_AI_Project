# -*- coding: utf-8 -*-
"""
数据库配置文件 - database.py
对应参数表：质量流量(m)、高温温度(t1)、低温温度(t2)、回收热量(Q)
"""

from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# --- 1. 数据库连接配置 ---
# SQLite 数据库文件名为 heat_recovery.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./heat_recovery.db"

# 创建数据库引擎
# connect_args 仅在 SQLite 下需要，用于处理线程问题
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# --- 2. 创建会话工厂 ---
# SessionLocal 类用于在代码中创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 3. 声明基类 ---
# 所有的数据库模型类都需要继承这个 Base
Base = declarative_base()


# --- 4. 定义数据模型 (对应参数表) ---
class HeatData(Base):
    # 指定数据库中的表名
    __tablename__ = "heat_data"

    # --- 字段定义 ---

    # 1. 主键 ID
    id = Column(Integer, primary_key=True, index=True)

    # 2. 时间戳 (记录数据产生的时间)
    # default=datetime.now 表示插入数据时自动填入当前时间
    timestamp = Column(DateTime, default=datetime.now)

    # 3. 高温端温度 t1 (入口温度)
    # 对应参数表：t1 | 现场热电偶测量
    temperature = Column(Float, nullable=False)

    # 4. 低温端温度 t2 (出口温度)  <-- 新增字段
    # 对应参数表：t2 | 现场热电偶测量
    # 这是计算温差 (t1-t2) 必须的参数，之前缺失，现在补上
    temp_outlet = Column(Float, nullable=False, default=0.0)

    # 5. 质量流量 m
    # 对应参数表：m | 工艺流量计
    flow_rate = Column(Float, nullable=False)

    # 6. 余热回收热量 Q
    # 对应参数表：Q | 计算值
    # 这个字段存储智能体计算出来的结果
    heat_value = Column(Float, nullable=True)

    # 7. 备注/描述
    description = Column(String, nullable=True)