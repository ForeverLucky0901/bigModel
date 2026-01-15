"""
限流服务（基于Redis）
"""
import redis
from typing import Optional
from app.config import settings
from app.utils.logger import logger

redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """获取Redis客户端"""
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # 测试连接
        try:
            redis_client.ping()
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    return redis_client


class RateLimiter:
    """限流器"""
    
    @staticmethod
    def _get_key(prefix: str, identifier: str, window: str = "minute") -> str:
        """生成Redis key"""
        return f"rate_limit:{prefix}:{identifier}:{window}"
    
    @staticmethod
    def check_rate_limit(
        identifier: str,
        limit_rpm: int,
        limit_tpm: int,
        current_tokens: int = 0,
        prefix: str = "key"
    ) -> tuple[bool, dict]:
        """
        检查限流
        
        Returns:
            (is_allowed, info_dict)
            info_dict包含: remaining_requests, remaining_tokens, reset_time
        """
        redis_cli = get_redis_client()
        
        key_rpm = RateLimiter._get_key(prefix, identifier, "rpm")
        key_tpm = RateLimiter._get_key(prefix, identifier, "tpm")
        
        try:
            # 使用滑动窗口计数
            pipe = redis_cli.pipeline()
            
            # RPM检查
            current_rpm = redis_cli.incr(key_rpm)
            if current_rpm == 1:
                redis_cli.expire(key_rpm, 60)  # 60秒过期
            
            # TPM检查
            if current_tokens > 0:
                current_tpm = redis_cli.incrby(key_tpm, current_tokens)
                if current_tpm == current_tokens:
                    redis_cli.expire(key_tpm, 60)
            else:
                current_tpm = redis_cli.get(key_tpm) or 0
                current_tpm = int(current_tpm)
            
            # 检查是否超限
            rpm_exceeded = current_rpm > limit_rpm
            tpm_exceeded = current_tpm > limit_tpm
            
            is_allowed = not (rpm_exceeded or tpm_exceeded)
            
            info = {
                "remaining_requests": max(0, limit_rpm - current_rpm),
                "remaining_tokens": max(0, limit_tpm - current_tpm),
                "current_requests": current_rpm,
                "current_tokens": current_tpm,
                "limit_rpm": limit_rpm,
                "limit_tpm": limit_tpm,
                "reset_time": 60  # 60秒后重置
            }
            
            return is_allowed, info
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # 失败时允许通过（fail-open策略）
            return True, {"error": str(e)}
    
    @staticmethod
    def reset_rate_limit(identifier: str, prefix: str = "key"):
        """重置限流计数（用于测试或手动重置）"""
        redis_cli = get_redis_client()
        key_rpm = RateLimiter._get_key(prefix, identifier, "rpm")
        key_tpm = RateLimiter._get_key(prefix, identifier, "tpm")
        redis_cli.delete(key_rpm, key_tpm)
