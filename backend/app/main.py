from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import engine, Base
from .api import auth, users, drawings, departments, products, logs, reviews, roles, core_parts, project_groups, dashboard, workload
import re

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="图纸管理系统 API - 提供图纸全生命周期管理功能"
)

# CORS 配置 - 开发环境
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://192.168.20.136:3001",
        "http://192.168.20.136:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 注册路由
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(drawings.router, prefix="/api")
app.include_router(departments.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(roles.router, prefix="/api")
app.include_router(core_parts.router, prefix="/api")
app.include_router(project_groups.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(workload.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
