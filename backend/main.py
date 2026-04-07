# -*- coding: utf-8 -*-
from fastapi import FastAPI

# 1. 创建应用实例
app = FastAPI(title="化工余热回收系统 API")

# 2. 定义一个根路径接口
@app.get("/")
def read_root():
    return {"Message": "赵元卿的系统后端已启动", "Status": "Running"}
# 导入刚才写的数据库配置
from database import engine, Base

# 创建数据库表（如果表不存在的话）
Base.metadata.create_all(bind=engine)