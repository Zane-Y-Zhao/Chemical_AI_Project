import os
# 1. 设置镜像
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 2. 尝试加载模型
from sentence_transformers import SentenceTransformer

print("开始下载模型...")
# 直接下载，不走 LangChain 的封装，更纯粹
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print("模型下载并加载成功！")