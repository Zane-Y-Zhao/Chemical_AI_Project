# 全项目文件改动清单（严格执行版）

## 目标
- 打通 te_transformer 真实推理链路
- 消除前端 mock，改为真实接口调用
- 保留现有知识检索与决策生成框架

## 文件改动清单

1. [x] `api/main.py`
- 新增 Transformer 在线推理组件（模型加载、特征构造、窗口缓存、推理接口）
- 新增 `/api/v1/transformer/predict` 端点
- 将 `generate_decision_core` 从阈值模拟预测改为真实模型推理结果

2. [x] `frontend/js/api/decisionClient.js`
- 移除“永远返回 mock”的逻辑
- 改为调用 `/api/v1/decision`，失败时再回退 mock

3. [x] `frontend/js/api/conversationClient.js`
- 移除“永远返回 mock”的逻辑
- 改为调用 `/api/v1/conversation`，失败时再回退 mock

4. [x] `EXECUTION_FILE_CHANGE_CHECKLIST.md`
- 固化本次执行范围、变更项、后续待办

## 本轮未纳入（下一轮）

## 第二轮已完成
- [x] `t-pre/te_cross_validate_transformer.py`：新增交叉验证脚本
- [x] `api/test_functional_suite.py`：增加 transformer 端点专项用例并改为稳健断言
- [x] `model_api_spec.md`：补充真实推理字段、错误码与运行配置
- [x] `INTEGRATION_TEST_REPORT_TEMPLATE.md`：新增集成测试报告模板
- [x] `PERFORMANCE_VALIDATION_REPORT_TEMPLATE.md`：新增性能验证报告模板

## 待执行（第三轮）
- [x] 运行交叉验证冒烟并落盘 `runs/te_transformer/cv_metrics_smoke.json`
- 运行全量交叉验证并落盘 `runs/te_transformer/cv_metrics.json`
- 实测压测并回填正式报告（非模板）
- 执行前端联调截图与Case-5演示资产补齐
