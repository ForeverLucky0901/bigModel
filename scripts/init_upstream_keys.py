"""
初始化上游密钥（从环境变量）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models.upstream import UpstreamKey, UpstreamKeyStatus
from app.utils.encryption import encrypt_key
from app.config import settings
from app.utils.logger import logger

def init_upstream_keys():
    """从环境变量初始化上游密钥"""
    db: Session = SessionLocal()
    try:
        if settings.UPSTREAM_TYPE == "openai":
            keys = settings.OPENAI_API_KEY_LIST
            if not keys:
                logger.warning("No OpenAI API keys found in environment")
                return
            
            for i, key in enumerate(keys):
                # 检查是否已存在
                existing = db.query(UpstreamKey).filter(
                    UpstreamKey.upstream_type == "openai",
                    UpstreamKey.encrypted_key == encrypt_key(key)
                ).first()
                
                if existing:
                    logger.info(f"OpenAI key {i+1} already exists, skipping")
                    continue
                
                upstream_key = UpstreamKey(
                    upstream_type="openai",
                    encrypted_key=encrypt_key(key),
                    weight=1,
                    status=UpstreamKeyStatus.HEALTHY.value,
                    notes=f"OpenAI Key {i+1}"
                )
                db.add(upstream_key)
                logger.info(f"Added OpenAI key {i+1}")
        
        elif settings.UPSTREAM_TYPE == "azure":
            keys = settings.AZURE_API_KEY_LIST
            endpoints = [settings.AZURE_ENDPOINT] * len(keys)
            deployments = settings.AZURE_DEPLOYMENT_NAME_LIST
            
            if not keys:
                logger.warning("No Azure API keys found in environment")
                return
            
            if len(deployments) != len(keys):
                logger.warning(f"Deployment count ({len(deployments)}) doesn't match key count ({len(keys)})")
                deployments = [deployments[0] if deployments else "gpt-35-turbo"] * len(keys)
            
            for i, (key, endpoint, deployment) in enumerate(zip(keys, endpoints, deployments)):
                upstream_key = UpstreamKey(
                    upstream_type="azure",
                    encrypted_key=encrypt_key(key),
                    azure_endpoint=endpoint,
                    azure_deployment_name=deployment,
                    azure_api_version=settings.AZURE_API_VERSION,
                    weight=1,
                    status=UpstreamKeyStatus.HEALTHY.value,
                    notes=f"Azure Key {i+1} - {deployment}"
                )
                db.add(upstream_key)
                logger.info(f"Added Azure key {i+1} for deployment {deployment}")
        
        db.commit()
        logger.info("Upstream keys initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to init upstream keys: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_upstream_keys()
