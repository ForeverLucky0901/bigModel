"""
上游Key池管理服务
支持轮询、权重、熔断
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import Optional, List
import random
from app.models.upstream import UpstreamKey, UpstreamKeyStatus
from app.utils.encryption import decrypt_key
from app.config import settings
from app.utils.logger import logger


class KeyPoolService:
    """Key池服务"""
    
    @staticmethod
    def get_healthy_keys(db: Session, upstream_type: str) -> List[UpstreamKey]:
        """获取健康的上游密钥"""
        now = datetime.utcnow()
        
        # 查询健康或需要检查恢复的密钥
        keys = db.query(UpstreamKey).filter(
            and_(
                UpstreamKey.upstream_type == upstream_type,
                UpstreamKey.status.in_([UpstreamKeyStatus.HEALTHY.value, UpstreamKeyStatus.COOLDOWN.value])
            )
        ).all()
        
        healthy_keys = []
        for key in keys:
            # 检查cooldown是否到期
            if key.status == UpstreamKeyStatus.COOLDOWN.value:
                if key.cooldown_until:
                    cooldown_time = datetime.fromisoformat(key.cooldown_until.replace('Z', '+00:00'))
                    if now < cooldown_time.replace(tzinfo=None):
                        continue  # 仍在冷却期
                    else:
                        # 冷却期结束，尝试恢复
                        key.status = UpstreamKeyStatus.HEALTHY.value
                        key.failure_count = 0
                        key.cooldown_until = None
                        db.commit()
                        logger.info(f"Upstream key {key.id} recovered from cooldown")
            
            if key.status == UpstreamKeyStatus.HEALTHY.value:
                healthy_keys.append(key)
        
        return healthy_keys
    
    @staticmethod
    def select_key(db: Session, upstream_type: str, strategy: str = "weighted") -> Optional[UpstreamKey]:
        """
        选择上游密钥
        
        Args:
            strategy: "weighted" (权重轮询) 或 "round_robin" (轮询)
        """
        healthy_keys = KeyPoolService.get_healthy_keys(db, upstream_type)
        
        if not healthy_keys:
            logger.warning(f"No healthy upstream keys available for {upstream_type}")
            return None
        
        if strategy == "weighted":
            # 权重选择
            total_weight = sum(k.weight for k in healthy_keys)
            if total_weight == 0:
                return random.choice(healthy_keys)
            
            rand = random.uniform(0, total_weight)
            current = 0
            for key in healthy_keys:
                current += key.weight
                if rand <= current:
                    return key
            return healthy_keys[0]
        else:
            # 简单轮询（可以改进为基于使用次数）
            return random.choice(healthy_keys)
    
    @staticmethod
    def record_success(db: Session, key_id: int, tokens: int = 0):
        """记录成功请求"""
        key = db.query(UpstreamKey).filter(UpstreamKey.id == key_id).first()
        if key:
            key.total_requests += 1
            key.total_tokens += tokens
            key.failure_count = 0  # 重置失败计数
            db.commit()
    
    @staticmethod
    def record_failure(db: Session, key_id: int, error_type: str = "unknown"):
        """记录失败请求，触发熔断"""
        key = db.query(UpstreamKey).filter(UpstreamKey.id == key_id).first()
        if not key:
            return
        
        key.total_errors += 1
        key.failure_count += 1
        key.last_failure_at = datetime.utcnow().isoformat()
        
        # 检查是否需要熔断
        if key.failure_count >= settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD:
            if key.status == UpstreamKeyStatus.HEALTHY.value:
                cooldown_until = datetime.utcnow() + timedelta(seconds=settings.CIRCUIT_BREAKER_COOLDOWN_SECONDS)
                key.status = UpstreamKeyStatus.COOLDOWN.value
                key.cooldown_until = cooldown_until.isoformat()
                logger.warning(f"Upstream key {key_id} entered cooldown after {key.failure_count} failures")
        
        db.commit()
    
    @staticmethod
    def get_decrypted_key(upstream_key: UpstreamKey) -> str:
        """获取解密后的密钥"""
        try:
            return decrypt_key(upstream_key.encrypted_key)
        except Exception as e:
            logger.error(f"Failed to decrypt key {upstream_key.id}: {e}")
            raise
