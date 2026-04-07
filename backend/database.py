class my_class(object):
    pass
# database.py
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 1. 数据库文件路径 (SQLite)
# 这会在你的项目根目录下创建一个 heat_recovery.db 文件
SQLALCHEMY_DATABASE_URL = "sqlite:///./heat_recovery.db"

# 2. 创建引擎
# connect_args 是 SQLite 特有的参数，用于处理线程检查
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. 创建会话（用来操作数据库）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 声明基类（用来创建表结构）
Base = declarative_base()

# 5. 定义数据表模型 (对应你的余热回收系统)
class HeatData(Base):
    __tablename__ = "heat_data"  # 数据库里的表名

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)  # 时间戳
    temperature = Column(Float, nullable=False)         # 烟气温度
    flow_rate = Column(Float, nullable=False)           # 流量
    heat_value = Column(Float, nullable=True)           # 计算出的热值
    description = Column(String, nullable=True)         # 备注



