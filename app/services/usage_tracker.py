"""
用量统计服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date
from typing import Optional
from app.models.usage import UsageRecord, UsageDaily, UsageMonthly
from app.models.user import User
from app.utils.logger import logger


class UsageTracker:
    """用量统计器"""
    
    @staticmethod
    def record_usage(
        db: Session,
        user_id: int,
        api_key_id: Optional[int],
        upstream_key_id: Optional[int],
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        response_status: int,
        response_time_ms: float,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_body: Optional[str] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """记录单次请求"""
        try:
            record = UsageRecord(
                user_id=user_id,
                api_key_id=api_key_id,
                upstream_key_id=upstream_key_id,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                response_status=response_status,
                response_time_ms=response_time_ms,
                client_ip=client_ip,
                user_agent=user_agent,
                request_body=request_body,
                error_type=error_type,
                error_message=error_message
            )
            db.add(record)
            db.commit()
            
            # 异步更新聚合表（可以改为后台任务）
            UsageTracker._update_aggregates(db, user_id, total_tokens)
            
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
            db.rollback()
    
    @staticmethod
    def _update_aggregates(db: Session, user_id: int, tokens: int):
        """更新聚合统计"""
        try:
            today = date.today()
            today_str = today.strftime("%Y-%m-%d")
            
            # 更新每日统计
            daily = db.query(UsageDaily).filter(
                and_(
                    UsageDaily.user_id == user_id,
                    UsageDaily.date == today_str
                )
            ).first()
            
            if daily:
                daily.total_requests += 1
                daily.total_tokens += tokens
            else:
                daily = UsageDaily(
                    user_id=user_id,
                    date=today_str,
                    total_requests=1,
                    total_tokens=tokens
                )
                db.add(daily)
            
            # 更新每月统计
            now = datetime.now()
            monthly = db.query(UsageMonthly).filter(
                and_(
                    UsageMonthly.user_id == user_id,
                    UsageMonthly.year == now.year,
                    UsageMonthly.month == now.month
                )
            ).first()
            
            if monthly:
                monthly.total_requests += 1
                monthly.total_tokens += tokens
            else:
                monthly = UsageMonthly(
                    user_id=user_id,
                    year=now.year,
                    month=now.month,
                    total_requests=1,
                    total_tokens=tokens
                )
                db.add(monthly)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update aggregates: {e}")
            db.rollback()
    
    @staticmethod
    def get_monthly_usage(db: Session, user_id: int, year: int, month: int) -> Optional[UsageMonthly]:
        """获取月度用量"""
        return db.query(UsageMonthly).filter(
            and_(
                UsageMonthly.user_id == user_id,
                UsageMonthly.year == year,
                UsageMonthly.month == month
            )
        ).first()
    
    @staticmethod
    def check_quota(db: Session, user_id: int, tokens: int) -> tuple[bool, Optional[str]]:
        """
        检查配额
        
        Returns:
            (is_allowed, error_message)
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        if not user.is_active:
            return False, "User is inactive"
        
        # 检查月度配额
        now = datetime.now()
        monthly = UsageTracker.get_monthly_usage(db, user_id, now.year, now.month)
        
        current_usage = monthly.total_tokens if monthly else 0
        if current_usage + tokens > user.monthly_quota_tokens:
            return False, f"Monthly quota exceeded. Used: {current_usage}/{user.monthly_quota_tokens}"
        
        return True, None
