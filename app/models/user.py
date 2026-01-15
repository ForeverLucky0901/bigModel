"""
用户模型
"""
from sqlalchemy import Column, String, Boolean, Text, Integer, Float
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    """用户表"""
    __tablename__ = "users"
    
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)  # 密码哈希（用于Web登录）
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    
    # 配额
    monthly_quota_tokens = Column(Integer, default=1000000, nullable=False)
    monthly_quota_amount = Column(Float, default=10.0, nullable=False)
    
    # 关联
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user")


class APIKey(BaseModel):
    """API密钥表（代理Key）"""
    __tablename__ = "api_keys"
    
    key = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=True)  # Key名称/备注
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 允许的模型列表（JSON字符串，如 ["gpt-3.5-turbo", "gpt-4"]）
    allowed_models = Column(Text, nullable=True)
    
    # 速率限制（覆盖全局设置）
    rate_limit_rpm = Column(Integer, nullable=True)
    rate_limit_tpm = Column(Integer, nullable=True)
    
    # 关联
    user = relationship("User", back_populates="api_keys")
    usage_records = relationship("UsageRecord", back_populates="api_key")
