# 前端集成指南

## 1. 概述

本文档旨在规范化工余热智能管理系统的前后端接口集成，特别是与智能体服务的对接。前端开发人员应严格按照本指南实现接口调用，确保系统功能正常运行。

## 2. 智能体决策API集成

### 2.1 API地址

```
http://localhost:8001/api/v1/decision
```

### 2.2 请求方法

- POST

### 2.3 请求头

| 字段名 | 值 | 必填 | 说明 |
|-------|-----|------|------|
| Content-Type | application/json | 是 | 固定值，确保请求体为JSON格式 |

### 2.4 请求体

**示例请求体：**

```json
{
  "temperature": 85.5,
  "pressure": 4.2,
  "flow_rate": 10.5,
  "heat_value": 1250.8,
  "timestamp": "2026-04-10T14:30:00"
}
```

**参数说明：**

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| temperature | number | 是 | 高温端温度（°C） |
| pressure | number | 是 | 系统压力（MPa） |
| flow_rate | number | 是 | 质量流量（kg/s） |
| heat_value | number | 是 | 回收热量（kJ） |
| timestamp | string | 是 | 数据时间戳（ISO格式） |

### 2.5 响应体

**示例响应体：**

```json
{
  "status": "success",
  "suggestion": "【智能建议】检测到温度升高，建议立即检查FV-101阀门状态，并确认管道温度是否超过安全限值。",
  "decision": {
    "action": "check_equipment",
    "parameters": {
      "valve_id": "FV-101",
      "temperature_threshold": 90.0
    },
    "reasoning": "基于当前温度数据，建议检查阀门状态以确保系统安全"
  },
  "source_trace": {
    "prediction_source": "冯申雨模型API (2026-04-10T14:30:00)",
    "knowledge_source": "杨泽彤-系统操作规则文档_v2.pdf",
    "safety_clause": "默认安全条款",
    "model_version": "v1.0.0",
    "confidence": 0.94,
    "timestamp": "2026-04-10T14:30:05"
  },
  "execution_time_ms": 2340.5
}
```

**字段说明：**

| 字段名 | 类型 | 说明 |
|-------|------|------|
| status | string | 响应状态（success/failure/warning） |
| suggestion | string | 生成的操作建议 |
| decision | object | 智能体决策结果 |
| decision.action | string | 建议的操作类型 |
| decision.parameters | object | 建议的参数设置 |
| decision.reasoning | string | 决策理由 |
| source_trace | object | 决策来源追踪信息（**必须在前端界面展示**） |
| source_trace.prediction_source | string | 预测来源 |
| source_trace.knowledge_source | string | 知识库来源 |
| source_trace.safety_clause | string | 安全条款 |
| source_trace.model_version | string | 模型版本 |
| source_trace.confidence | number | 决策置信度 |
| source_trace.timestamp | string | 决策时间戳 |
| execution_time_ms | number | 端到端处理耗时（毫秒） |

### 2.6 错误响应

**示例错误响应：**

```json
{
  "status": "failure",
  "suggestion": "决策生成失败：参数错误",
  "decision": {
    "action": "error",
    "parameters": null,
    "reasoning": "系统遇到异常：参数错误"
  },
  "source_trace": {
    "prediction_source": "系统内部错误",
    "knowledge_source": "系统内部错误",
    "safety_clause": "系统内部错误",
    "model_version": "v1.0.0",
    "confidence": 0.0,
    "timestamp": "2026-04-10T14:30:00"
  },
  "execution_time_ms": 0.0
}
```

## 3. 前端实现要求

### 3.1 调用方式

前端应使用Axios或其他HTTP客户端库调用API，确保设置正确的请求头。

**示例代码：**

```javascript
async function getDecision(data) {
  try {
    const response = await axios.post('http://localhost:8001/api/v1/decision', data, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error calling decision API:', error);
    throw error;
  }
}
```

### 3.2 响应处理

1. **成功响应**：
   - 解析 `suggestion` 字段，在界面上展示操作建议
   - 解析 `decision` 字段，根据 `action` 和 `parameters` 执行相应操作
   - 解析 `source_trace` 字段，在界面上展示决策来源信息

2. **错误响应**：
   - 捕获并处理错误，在界面上显示错误信息
   - 解析 `status` 字段，根据不同状态显示不同的错误提示

### 3.3 界面展示

前端应在界面上专门设置一个区域，展示智能体决策的溯源信息，包括：
- 预测来源（prediction_source）
- 知识库来源（knowledge_source）
- 安全条款（safety_clause）
- 模型版本（model_version）
- 决策置信度（confidence）
- 决策时间（timestamp）

## 4. 本地开发环境

### 4.1 服务启动顺序

1. 启动智能体服务（端口8001）
2. 启动后端服务（端口8000）
3. 启动前端应用

### 4.2 测试建议

- 使用Postman或类似工具测试API接口
- 确保前端能够正确处理各种响应情况
- 验证 `source_trace` 字段的展示效果

## 5. 部署环境

在生产环境中，API地址可能会有所不同，应根据实际部署情况进行调整。

## 5. 其他数据接口

### 5.1 KPI数据接口
- **API地址**: `http://localhost:8000/api/v1/kpi`
- **请求方法**: GET
- **响应体格式**:
```json
{
  "temperature": 85.5,
  "pressure": 4.2,
  "heatRecovery": 1250.8,
  "energyConsumption": 15.6,
  "efficiency": 85.2,
  "predictions": {
    "temperature": 86.2,
    "pressure": 4.3,
    "heatRecovery": 1280.5,
    "energyConsumption": 15.8,
    "efficiency": 84.5
  }
}
```

### 5.2 趋势数据接口
- **API地址**: `http://localhost:8000/api/v1/trends`
- **请求方法**: GET
- **响应体格式**:
```json
{
  "labels": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
  "datasets": {
    "temperature": [78, 82, 85, 88, 86, 85],
    "pressure": [3.8, 4.0, 4.2, 4.5, 4.3, 4.2],
    "heatRecovery": [1100, 1150, 1200, 1280, 1260, 1250]
  }
}
```

### 5.3 设备状态接口
- **API地址**: `http://localhost:8000/api/v1/equipment`
- **请求方法**: GET
- **响应体格式**:
```json
[
  {
    "id": 1,
    "name": "换热器1",
    "status": "normal",
    "statusText": "正常",
    "health": 95
  },
  {
    "id": 2,
    "name": "换热器2",
    "status": "warning",
    "statusText": "需要维护",
    "health": 75
  }
]
```

### 5.4 预警信息接口
- **API地址**: `http://localhost:8000/api/v1/alerts`
- **请求方法**: GET
- **响应体格式**:
```json
[
  {
    "id": 1,
    "title": "温度预警",
    "message": "高温端温度即将超过阈值",
    "time": "2026-04-10 14:30:22",
    "level": "warning"
  }
]
```

## 6. 版本控制

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0 | 2026-04-10 | 初始版本 |
| 1.1 | 2026-04-10 | 统一接口规范，添加suggestion字段和扩展source_trace字段 |

## 7. 联系方式

如有任何问题，请联系：
- 后端开发：[您的姓名]
- 智能体开发：赵元卿
