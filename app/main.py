"""
FastAPI 应用主入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, health
from app.middleware.rate_limit import rate_limit_middleware
from app.utils.logger import logger

app = FastAPI(
    title="GPT Proxy Service",
    description="OpenAI-compatible API proxy with authentication, rate limiting, and usage tracking",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册中间件
@app.middleware("http")
async def middleware_stack(request: Request, call_next):
    """中间件栈"""
    # 基础IP限流（在鉴权之前）
    if request.url.path not in ["/health", "/docs", "/openapi.json", "/redoc"]:
        from app.services.rate_limiter import RateLimiter
        from app.config import settings
        client_ip = request.client.host if request.client else "unknown"
        is_allowed, _ = RateLimiter.check_rate_limit(
            identifier=client_ip,
            limit_rpm=settings.RATE_LIMIT_IP_RPM,
            limit_tpm=settings.RATE_LIMIT_IP_TPM,
            prefix="ip"
        )
        if not is_allowed:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="IP rate limit exceeded"
            )
    return await call_next(request)


# 注册路由
app.include_router(health.router)
app.include_router(chat.router)

# 认证和管理路由
from app.api import auth, admin
app.include_router(auth.router)
app.include_router(admin.router)


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("GPT Proxy Service starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("GPT Proxy Service shutting down...")


if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
