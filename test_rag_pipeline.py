# 测试rag_pipeline.py的功能
import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledge_base import rag_pipeline

print("成功导入rag_pipeline模块")

# 测试加载知识片段
print("\n测试加载知识片段...")
chunks = rag_pipeline.load_cleaned_chunks()
print(f"加载了 {len(chunks)} 个知识片段")

# 测试混合检索模式
print("\n测试混合检索模式...")
test_queries = ["temperature_rise", "flow_instability"]
for query in test_queries:
    print(f"\n测试查询：{query}")
    results = rag_pipeline.test_retrieval(query)
    print(f"检索到 {len(results)} 个结果")

print("\n测试完成！")
