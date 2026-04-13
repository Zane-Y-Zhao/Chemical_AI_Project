# Chemical_AI_Project 项目结构总结

## 1. 项目总体定位

该项目是一个面向化工场景的 AI 系统，整体覆盖了：

- 数据处理与清洗
- 模型训练与监控
- 知识库与 RAG 检索决策
- API 服务与后端联动
- 前端展示与联调
- 功能、性能与稳定性测试

从目录结构看，项目已经形成了“研发 + 验证 + 部署”一体化工程形态。

## 2. 根目录（主要是脚本与文档）

根目录包含大量可直接运行的 Python 脚本，按职责大致分为：

- 训练与模型相关：`train.py`、`train_monitor.py`、`auto_research.py`、`auto_research_resume_train.py`、`models.py`
- 数据与分析：`data_clean.py`、`data_processor.py`、`eda_test.py`、`log_analyzer.py`
- 服务与启动：`simple_api.py`、`start_api.py`、`deploy_verify.py`
- 评测与测试：`test_*.py`、`performance_test*.py`、`locustfile*.py`
- 排查与工具：`check_port.py`、`check_vectorstore.py`、`count_transformer_params.py`
- 文档与报告：`README.md`、`model_api_spec.md`、`TEST_REPORT.md`、`VALIDATION_REPORT.md`、`技术白皮书.md`

此外，根目录有模型权重与检查点文件，如：`final_model.pth`、`best_model_autoresearch.pth`、`last_checkpoint_autoresearch.pth`。

## 3. 核心子目录说明

### api/

API 侧独立目录，含：

- 服务入口与模块：`main.py`、`__init__.py`
- API 相关测试：`test_api_startup.py`、`test_simple_api.py`、`test_functional_suite.py`
- API 性能压测脚本：`performance_test.py`、`simple_performance_test.py`、`locustfile.py`

用途偏向“接口层快速验证 + 性能回归”。

### backend/

后端业务模块，含：

- 主入口：`main.py`
- 数据库：`database.py`
- 传感器模拟：`sensor_simulator.py`
- 监控：`agent_monitor.py`
- 依赖：`requirements.txt`
- 联调文档：`frontend_integration_guide.md`

体现出与前端、设备模拟和监控联动的后端工程能力。

### frontend/

前端资源目录，含：

- 页面入口：`index.html`
- 样式目录：`css/`
- 脚本目录：`js/`

结构清晰，适合与后端 API 做可视化联调。

### knowledge_base/

知识库与检索增强核心目录，含：

- 文档处理：`document_processor.py`
- 决策与流程：`decision_pipeline.py`
- RAG 主链路：`rag_pipeline.py`
- 提示词工程：`prompt_engineering.py`
- LLM 配置：`llm_config.py`
- 相关测试与性能脚本：`test_*.py`、`locust_performance_test.py`

这是项目智能决策能力的重要中枢。

### demo_cases/

示例用例目录，包含多个 JSON 场景文件（如 `case_1.json` 到 `case_4_round2.json`）和说明文档 `demo_cases.md`，用于演示与回归对比。

## 4. 数据、产物与运行目录

- `models/`：模型文件目录
- `logs/`：运行日志目录
- `runs/`：训练或实验运行记录目录
- `te-data/`、`t-pre/`：项目数据相关目录（命名显示可能与原始数据/预处理流程有关）

这些目录说明项目具备完整实验闭环：输入数据 -> 训练/推理 -> 结果记录 -> 分析复盘。

## 5. 测试与质量保障特点

项目存在大量测试脚本，覆盖面较广：

- API 可用性与健康检查（如 `test_api_health.py`、`test_health.py`）
- 对话与决策链路（如 `test_conversation.py`、`test_decision*.py`）
- RAG 与检索能力（如 `test_rag_pipeline.py`、`test_vectorstore.py`）
- 安全熔断相关测试（如 `test_safety_fuse*.py`）
- 性能压测（`locustfile.py`、`performance_test_comprehensive.py`）

说明项目不仅关注功能实现，也重视稳定性、性能与安全性验证。

## 6. 结构结论

当前项目结构已经具备中大型 AI 应用工程的典型特征：

- 模型训练与推理链路完整
- 知识库与 RAG 决策模块独立
- API、后端、前端分层明确
- 测试体系较完善，文档与报告沉淀充分

整体可判断为一个“面向真实业务场景”的化工 AI 系统工程，而不仅是单一模型实验仓库。