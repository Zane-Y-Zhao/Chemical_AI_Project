# 化工余热回收系统 (Chemical Heat Recovery System)

## 1. 项目简介
本项目旨在开发一套化工过程余热回收系统的仿真与优化平台。

## 2. 环境配置
### 后端启动
1. 安装依赖：`pip install -r requirements.txt`
2. 启动服务：`uvicorn main:app --reload`

## 3. 数据库设计 (Database Design)
当前使用 SQLite 数据库 (`heat_recovery.db`)。
主要数据表规划如下：

### 表名：ProcessUnits (工艺单元)
存储换热器、塔器等设备的基础参数。
- `id`: 整数, 主键
- `name`: 字符串, 设备名称
- `type`: 字符串, 设备类型

### 表名：SensorData (传感器数据)
存储实时的温度、压力、流量数据。
- `id`: 整数, 主键
- `timestamp`: 日期时间, 采集时间
- `unit_id`: 整数, 外键(关联 ProcessUnits)
- `temperature`: 浮点数, 温度值
- `pressure`: 浮点数, 压力值
- `flow_rate`: 浮点数, 流量值