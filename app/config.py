"""
配置管理模块
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # 基础配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ADMIN_PORT: int = 8001
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # 域名
    DOMAIN: str = "your-domain.com"
    ADMIN_DOMAIN: Optional[str] = None
    
    # 数据库
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "gpt_proxy"
    POSTGRES_USER: str = "gpt_proxy"
    POSTGRES_PASSWORD: str = ""
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # 上游配置
    UPSTREAM_TYPE: str = "openai"  # openai 或 azure
    
    # OpenAI
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_API_KEYS: str = ""
    
    @property
    def OPENAI_API_KEY_LIST(self) -> List[str]:
        return [k.strip() for k in self.OPENAI_API_KEYS.split(",") if k.strip()]
    
    # Azure OpenAI
    AZURE_ENDPOINT: str = ""
    AZURE_API_KEYS: str = ""
    AZURE_DEPLOYMENT_NAMES: str = ""
    AZURE_API_VERSION: str = "2023-12-01-preview"
    
    @property
    def AZURE_API_KEY_LIST(self) -> List[str]:
        return [k.strip() for k in self.AZURE_API_KEYS.split(",") if k.strip()]
    
    @property
    def AZURE_DEPLOYMENT_NAME_LIST(self) -> List[str]:
        return [d.strip() for d in self.AZURE_DEPLOYMENT_NAMES.split(",") if d.strip()]
    
    # 限流
    RATE_LIMIT_RPM: int = 60
    RATE_LIMIT_TPM: int = 90000
    RATE_LIMIT_IP_RPM: int = 30
    RATE_LIMIT_IP_TPM: int = 45000
    
    # 熔断
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_COOLDOWN_SECONDS: int = 300
    CIRCUIT_BREAKER_RECOVERY_THRESHOLD: int = 2
    
    # 安全
    ENCRYPTION_KEY: str = ""
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"
    
    # 日志
    LOG_LEVEL: str = "INFO"
    LOG_PROMPT_BODY: bool = False
    LOG_FILE_PATH: str = "/var/log/gpt_proxy/app.log"
    
    # 配额
    DEFAULT_MONTHLY_QUOTA_TOKENS: int = 1000000
    DEFAULT_MONTHLY_QUOTA_AMOUNT: float = 10.0
    
    # 超时
    UPSTREAM_TIMEOUT: int = 300
    UPSTREAM_CONNECT_TIMEOUT: int = 30
    
    # Nginx（仅用于 docker-compose，API 不使用）
    NGINX_WORKER_PROCESSES: str = "auto"
    NGINX_WORKER_CONNECTIONS: int = 1024
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量


settings = Settings()
