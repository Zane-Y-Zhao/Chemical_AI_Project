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
  "decision": {
    "action": "adjust_parameters",
    "parameters": {
      "temperature_setpoint": 82.0,
      "pressure_setpoint": 4.0,
      "flow_rate_setpoint": 11.0
    },
    "reasoning": "基于当前温度和压力数据，建议调整参数以提高系统效率"
  },
  "source_trace": {
    "model_version": "v1.0.0",
    "knowledge_base": "化工安全操作规程_2025版",
    "confidence": 0.92,
    "timestamp": "2026-04-10T14:30:05"
  }
}
```

**字段说明：**

| 字段名 | 类型 | 说明 |
|-------|------|------|
| status | string | 响应状态（success/failure） |
| decision | object | 智能体决策结果 |
| decision.action | string | 建议的操作类型 |
| decision.parameters | object | 建议的参数设置 |
| decision.reasoning | string | 决策理由 |
| source_trace | object | 决策来源追踪信息（**必须在前端界面展示**） |
| source_trace.model_version | string | 模型版本 |
| source_trace.knowledge_base | string | 知识库来源 |
| source_trace.confidence | number | 决策置信度 |
| source_trace.timestamp | string | 决策时间戳 |

### 2.6 错误响应

**示例错误响应：**

```json
{
  "status": "failure",
  "error": "Invalid input parameters",
  "message": "Temperature must be greater than 0"
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
   - 解析 `decision` 字段，根据 `action` 和 `parameters` 执行相应操作
   - 解析 `source_trace` 字段，在界面上展示决策来源信息

2. **错误响应**：
   - 捕获并处理错误，在界面上显示错误信息

### 3.3 界面展示

前端应在界面上专门设置一个区域，展示智能体决策的溯源信息，包括：
- 模型版本
- 知识库来源
- 决策置信度
- 决策时间

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

## 6. 版本控制

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0 | 2026-04-10 | 初始版本 |

## 7. 联系方式

如有任何问题，请联系：
- 后端开发：[您的姓名]
- 智能体开发：赵元卿
