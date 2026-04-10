from knowledge_base.llm_config import call_qwen
import time

# 测试大模型调用可靠性
print("开始测试大模型调用可靠性...")

success_count = 0
fail_count = 0
total_time = 0

for i in range(10):
    start_time = time.time()
    result = call_qwen("请用一句话说明余热回收温度阈值设定为100°C的工程依据")
    end_time = time.time()
    response_time = end_time - start_time
    total_time += response_time
    
    if result.startswith("[ERROR]"):
        fail_count += 1
        print(f"第{i+1}次调用失败，错误：{result}")
    else:
        success_count += 1
        print(f"第{i+1}次调用成功，响应时间：{response_time:.2f}s")

# 计算统计结果
failure_rate = (fail_count / 10) * 100
average_time = total_time / 10

print(f"\n测试结果：")
print(f"总调用次数：10")
print(f"成功次数：{success_count}")
print(f"失败次数：{fail_count}")
print(f"失败率：{failure_rate}%")
print(f"平均响应时间：{average_time:.2f}s")

# 验证是否达标
if failure_rate <= 5 and average_time < 8:
    print("✓ 大模型调用可靠性测试通过")
else:
    print("✗ 大模型调用可靠性测试未通过")

