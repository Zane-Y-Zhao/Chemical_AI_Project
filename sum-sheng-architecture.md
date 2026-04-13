# Chemical_AI_Project 架构流总结

## 1. 端到端主链路

该项目可抽象为一条端到端数据与决策链路：

1. 数据输入层：历史案例、文档、传感器状态、用户问题
2. 知识与检索层：文档处理、向量检索、RAG 召回
3. 推理与决策层：LLM 推理、规则补充、决策管线输出
4. 服务编排层：API 路由、后端服务、数据库与监控
5. 展示与交互层：前端页面、演示案例、联调流程
6. 保障层：功能测试、健康检查、性能压测、安全熔断

## 2. 分层与目录映射

### A. 数据准备层

- 根目录脚本：`data_clean.py`、`data_processor.py`、`eda_test.py`
- 相关目录：`te-data/`、`t-pre/`

职责：清洗、预处理、结构检查，为训练和知识入库提供可用数据。

### B. 模型训练层

- 训练与监控：`train.py`、`train_monitor.py`
- 自动研究流程：`auto_research.py`、`auto_research_resume_train.py`
- 模型定义：`models.py`
- 产物：`models/`、`runs/`、`*.pth`

职责：完成模型训练、恢复训练、实验记录与权重沉淀。

### C. 知识库与 RAG 层

- 目录：`knowledge_base/`
- 核心文件：`document_processor.py`、`rag_pipeline.py`、`decision_pipeline.py`、`prompt_engineering.py`、`llm_config.py`

职责：将领域知识加工为可检索形态，并与生成模型协同形成可解释决策输出。

### D. 服务接口与后端层

- API 目录：`api/`（`main.py` + 一组 API 测试与压测脚本）
- 后端目录：`backend/`（`main.py`、`database.py`、`sensor_simulator.py`、`agent_monitor.py`）
- 根目录服务脚本：`simple_api.py`、`start_api.py`

职责：承接外部请求、组织业务流程、对接数据库和模拟设备状态。

### E. 前端与演示层

- 前端目录：`frontend/`（`index.html`、`css/`、`js/`）
- 演示目录：`demo_cases/`（多个 JSON 场景）

职责：可视化呈现系统状态与推理结果，支撑演示和联调。

### F. 质量保障层

- 功能测试：大量 `test_*.py`
- 性能测试：`performance_test*.py`、`locustfile*.py`
- 运行排障：`check_port.py`、`check_vectorstore.py`、`log_analyzer.py`
- 报告模板与文档：`*_REPORT*.md`、`VALIDATION_REPORT.md`

职责：保障功能正确性、性能稳定性与线上可运维性。

## 3. 关键数据流（简化）

1. 原始数据进入预处理脚本。
2. 训练脚本产出模型权重与实验记录。
3. 文档处理脚本构建知识库索引。
4. API/后端接收请求并调用 RAG + 决策管线。
5. 前端展示结果，测试脚本持续回归验证。
6. 日志与报告回流到分析与优化环节。

## 4. 工程特征判断

该仓库并非单纯算法实验，而是具备生产化倾向的应用工程：

- 有训练、推理、服务、前端的完整分层
- 有知识库与检索增强作为领域能力核心
- 有较全面的测试与性能验证体系
- 有可复用的报告模板和演示案例资产

整体符合“化工场景 AI 应用平台”的工程化结构。