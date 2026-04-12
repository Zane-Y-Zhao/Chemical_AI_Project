from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 创建一个简单的 FastAPI 应用
app = FastAPI(
    title="测试 API",
    description="一个简单的测试 API",
    version="1.0.0"
)

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "API 服务运行正常"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_simple_api:app", host="127.0.0.1", port=8008, reload=True)
