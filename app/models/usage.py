"""
用量统计模型
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class UsageRecord(BaseModel):
    """请求记录表（审计日志）"""
    __tablename__ = "usage_records"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True, index=True)
    upstream_key_id = Column(Integer, ForeignKey("upstream_keys.id"), nullable=True, index=True)
    
    # 请求信息
    model = Column(String(100), nullable=False, index=True)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # 请求详情（可选，根据LOG_PROMPT_BODY决定）
    request_body = Column(Text, nullable=True)  # JSON字符串
    response_status = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)  # 响应时间（毫秒）
    
    # 客户端信息
    client_ip = Column(String(50), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    
    # 错误信息
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 关联
    user = relationship("User", back_populates="usage_records")
    api_key = relationship("APIKey", back_populates="usage_records")
    
    # 索引
    __table_args__ = (
        Index('idx_usage_user_date', 'user_id', 'created_at'),
        Index('idx_usage_date', 'created_at'),
    )


class UsageDaily(BaseModel):
    """每日用量聚合表"""
    __tablename__ = "usage_daily"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    
    total_requests = Column(Integer, default=0, nullable=False)
    total_prompt_tokens = Column(Integer, default=0, nullable=False)
    total_completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    total_cost = Column(Float, default=0.0, nullable=False)  # 成本（美元）
    
    # 唯一约束
    __table_args__ = (
        Index('idx_usage_daily_user_date', 'user_id', 'date', unique=True),
    )


class UsageMonthly(BaseModel):
    """每月用量聚合表"""
    __tablename__ = "usage_monthly"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    total_requests = Column(Integer, default=0, nullable=False)
    total_prompt_tokens = Column(Integer, default=0, nullable=False)
    total_completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    total_cost = Column(Float, default=0.0, nullable=False)
    
    # 唯一约束
    __table_args__ = (
        Index('idx_usage_monthly_user_ym', 'user_id', 'year', 'month', unique=True),
    )
