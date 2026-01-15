"""
限流中间件
"""
from fastapi import Request, HTTPException, status
from app.services.rate_limiter import RateLimiter
from app.models.user import APIKey
from app.utils.logger import logger


async def rate_limit_middleware(request: Request, call_next):
    """限流中间件（应在鉴权中间件之后）"""
    # 跳过健康检查等端点
    if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)
    
    # 先执行请求，让鉴权中间件先运行
    response = await call_next(request)
    
    # 获取API Key和IP（在鉴权之后）
    api_key: APIKey = getattr(request.state, "api_key", None)
    client_ip = request.client.host if request.client else "unknown"
    
    if not api_key:
        # 如果没有API Key，只进行IP限流
        from app.config import settings
        is_allowed, info = RateLimiter.check_rate_limit(
            identifier=client_ip,
            limit_rpm=settings.RATE_LIMIT_IP_RPM,
            limit_tpm=settings.RATE_LIMIT_IP_TPM,
            prefix="ip"
        )
        
        if not is_allowed:
            logger.warning(f"IP rate limit exceeded: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "message": "Rate limit exceeded",
                        "type": "rate_limit_error",
                        "code": "rate_limit_exceeded",
                        **info
                    }
                }
            )
        
        return response
    
    # 使用API Key的限流配置（如果存在）或全局配置
    from app.config import settings
    limit_rpm = api_key.rate_limit_rpm or settings.RATE_LIMIT_RPM
    limit_tpm = api_key.rate_limit_tpm or settings.RATE_LIMIT_TPM
    
    # 注意：限流检查应该在请求处理前进行，但由于需要鉴权信息，这里在响应后记录
    # 实际限流应该在API路由中，在调用上游前进行
    # 这里只做基础IP限流检查
    
    return response
