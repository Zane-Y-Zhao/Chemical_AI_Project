# 性能验证报告（模板）

## 1. 基本信息
- 日期: YYYY-MM-DD
- 执行人: 
- 分支: main
- API地址: `http://127.0.0.1:8001/api/v1/decision`

## 2. 环境信息
- OS: Windows
- CPU/GPU: 
- Python: 
- 并发工具: `performance_test_comprehensive.py` / `locust`

## 3. 执行步骤（可复现）
1. 激活环境: `c:/Users/Sheng/Desktop/Chemical_AI_Project/.venv/Scripts/Activate.ps1`
2. 启动API: `python start_api.py`
3. 运行综合压测: `python performance_test_comprehensive.py`
4. 如需locust: `locust -f locustfile_performance.py --host=http://127.0.0.1:8001`
5. 导出结果并填表

## 4. 指标定义
- 平均延迟: Avg Latency (ms)
- 95分位延迟: P95 Latency (ms)
- 吞吐量: Requests/sec
- 成功率: 2xx / Total
- 错误请求平均响应时间: 对422/4xx的平均响应耗时

## 5. 场景结果
| 场景 | 配置 | Avg(ms) | P95(ms) | 吞吐(req/s) | 成功率(%) | 结论 |
|---|---|---:|---:|---:|---:|---|
| 单用户连续请求 | duration=60s |  |  |  |  |  |
| 100并发请求 | users=100,total=1000 |  |  |  |  |  |
| 混合负载 | 80%正常+20%错误 |  |  |  |  |  |

## 6. 验收阈值
- Avg <= 600ms
- P95 <= 800ms
- 主流程成功率 >= 99.9%
- 错误请求响应时间 <= 200ms

## 7. 结论与优化建议
- 是否通过验收: 是/否
- 主要瓶颈: 
- 优化项: 
