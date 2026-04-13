# 系统集成测试报告（模板）

## 1. 基本信息
- 日期: YYYY-MM-DD
- 执行人: 
- 分支: main
- 后端版本: 
- 前端版本: 
- 模型版本: te_transformer_v1

## 2. 环境信息
- OS: Windows
- Python: 
- FastAPI: 
- 启动方式: `python start_api.py`
- 服务地址: `http://127.0.0.1:8001`

## 3. 执行步骤（可复现）
1. 激活环境: `c:/Users/Sheng/Desktop/Chemical_AI_Project/.venv/Scripts/Activate.ps1`
2. 启动服务: `python start_api.py`
3. 健康检查: 访问 `GET /health`
4. 预测测试: 调用 `POST /api/v1/transformer/predict`
5. 决策测试: 调用 `POST /api/v1/decision`
6. 会话测试: 调用 `POST /api/v1/conversation`
7. 前端联调: 打开 `frontend/index.html` 并验证决策与会话请求走真实接口

## 4. 接口联调结果
| 用例 | 输入 | 预期 | 实际 | 结论 |
|---|---|---|---|---|
| health_check | 无 | 200 + status=healthy |  |  |
| transformer_predict_valid | unit=°C | 200 + schema完整 |  |  |
| transformer_predict_invalid_unit | unit=K | 422 |  |  |
| decision_valid | 标准输入 | 200 + source_trace完整 |  |  |
| conversation_context | 两轮对话 | 第二轮继承上下文 |  |  |
| frontend_decision | 仪表盘触发 | 返回真实决策响应 |  |  |

## 5. 问题清单
| 编号 | 现象 | 影响 | 定位 | 状态 |
|---|---|---|---|---|
| I-001 |  |  |  |  |

## 6. 结论
- 集成通过率: %
- 阻塞项: 
- 是否满足上线联调要求: 是/否
