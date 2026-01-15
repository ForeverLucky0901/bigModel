"""
健康检查端点
"""
from fastapi import APIRouter
from app.services.rate_limiter import get_redis_client
from app.models.base import engine
from sqlalchemy import text
from app.utils.logger import logger

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查"""
    status = {
        "status": "healthy",
        "services": {}
    }
    
    # 检查数据库
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["services"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status["services"]["database"] = "unhealthy"
        status["status"] = "degraded"
    
    # 检查Redis
    try:
        redis_cli = get_redis_client()
        redis_cli.ping()
        status["services"]["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        status["services"]["redis"] = "unhealthy"
        status["status"] = "degraded"
    
    return status
