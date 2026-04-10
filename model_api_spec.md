Transformer 模型 API 接口规范文档
1. 接口概述
本接口用于调用基于 PyTorch 实现的 Transformer 时序分类模型。该模型专为处理多变量时序数据（如 TE 化工过程数据）设计，利用自注意力机制捕捉序列中的长距离依赖关系。
•接口路径: `/api/v1/transformer/predict`
•请求方法: `POST`
•Content-Type: `application/json`
•模型版本: `v1.0 (d_model=128, nhead=4)`

2. 智能决策API接口
本接口是基于Transformer模型的智能决策接口，用于生成化工过程操作建议。
•接口路径: `/api/v1/decision`
•请求方法: `POST`
•Content-Type: `application/json`
•版本: `v1.0.0`

3. 请求参数
输入数据约束
请求体中的参数必须包含温度、压力、流量和热量等关键传感器数据。

请求体示例
{
  "temperature": 85.5,
  "pressure": 4.2,
  "flow_rate": 10.5,
  "heat_value": 1250.8,
  "timestamp": "2026-04-10T14:30:00"
}

字段说明
字段名	类型	说明
`temperature`	`Number`	高温端温度（°C）
`pressure`	`Number`	系统压力（MPa）
`flow_rate`	`Number`	质量流量（kg/s）
`heat_value`	`Number`	回收热量（kJ）
`timestamp`	`String`	数据时间戳（ISO格式）

4. 响应参数
成功响应示例
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

字段说明
字段名	类型	说明
`status`	`String`	响应状态（success/failure/warning）
`suggestion`	`String`	生成的操作建议
`decision`	`Object`	智能体决策结果
`decision.action`	`String`	建议的操作类型
`decision.parameters`	`Object`	建议的参数设置
`decision.reasoning`	`String`	决策理由
`source_trace`	`Object`	决策来源追踪信息
`source_trace.prediction_source`	`String`	预测来源
`source_trace.knowledge_source`	`String`	知识库来源
`source_trace.safety_clause`	`String`	安全条款
`source_trace.model_version`	`String`	模型版本
`source_trace.confidence`	`Number`	决策置信度
`source_trace.timestamp`	`String`	决策时间戳
`execution_time_ms`	`Number`	端到端处理耗时（毫秒）

5. 错误码定义
状态码	错误信息	描述与解决方案
`200`	`OK`	请求成功，返回预测结果。
`400`	`Bad Request`	参数错误。请检查输入数据的格式和值。
`500`	`Internal Error`
服务器内部错误。可能是模型加载失败、推理过程中出现异常。
`503`	`Unavailable`	服务不可用。服务正在重启或过载。

6. 模型配置说明
本 API 后端加载的模型配置如下（参考代码）：
•输入维度: `input_size` (例如 52，对应 TE_processed.csv 特征数)
•序列长度: `seq_len` (例如 5，需与数据预处理窗口一致)
•隐藏层维度: `d_model = 128`
•注意力头数: `nhead = 4`
•编码器层数: `num_layers = 2`
•输出类别: `output_size` (取决于具体分类任务，二分类通常为 1)