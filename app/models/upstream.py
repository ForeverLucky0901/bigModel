"""
上游密钥模型
"""
from sqlalchemy import Column, String, Integer, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ENUM
import enum
from app.models.base import BaseModel


class UpstreamKeyStatus(str, enum.Enum):
    """上游密钥状态"""
    HEALTHY = "healthy"
    COOLDOWN = "cooldown"
    DISABLED = "disabled"


class UpstreamKey(BaseModel):
    """上游密钥表（OpenAI/Azure Key）"""
    __tablename__ = "upstream_keys"
    
    # 上游类型
    upstream_type = Column(String(20), nullable=False)  # openai 或 azure
    
    # 加密存储的密钥
    encrypted_key = Column(String(500), nullable=False)
    
    # Azure 特有字段
    azure_endpoint = Column(String(500), nullable=True)
    azure_deployment_name = Column(String(100), nullable=True)
    azure_api_version = Column(String(50), nullable=True)
    
    # 权重和状态
    weight = Column(Integer, default=1, nullable=False)  # 权重，用于轮询
    status = Column(String(20), default=UpstreamKeyStatus.HEALTHY.value, nullable=False)
    
    # 熔断相关
    failure_count = Column(Integer, default=0, nullable=False)
    last_failure_at = Column(String(50), nullable=True)  # ISO格式时间字符串
    cooldown_until = Column(String(50), nullable=True)  # ISO格式时间字符串
    
    # 统计
    total_requests = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    total_errors = Column(Integer, default=0, nullable=False)
    
    # 备注
    notes = Column(String(500), nullable=True)
