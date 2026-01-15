"""
创建普通用户和API Key
"""
import sys
import os
import secrets
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models.user import User, APIKey
from app.config import settings
from app.utils.logger import logger

def generate_api_key() -> str:
    """生成API Key"""
    return f"sk-proxy-{secrets.token_urlsafe(32)}"

def create_user(
    username: str,
    email: str = None,
    monthly_quota_tokens: int = None,
    monthly_quota_amount: float = None,
    allowed_models: list = None,
    rate_limit_rpm: int = None,
    rate_limit_tpm: int = None
):
    """创建用户和API Key"""
    db: Session = SessionLocal()
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            logger.warning(f"User {username} already exists")
            return existing_user
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            is_active=True,
            is_admin=False,
            monthly_quota_tokens=monthly_quota_tokens or settings.DEFAULT_MONTHLY_QUOTA_TOKENS,
            monthly_quota_amount=monthly_quota_amount or settings.DEFAULT_MONTHLY_QUOTA_AMOUNT
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建API Key
        api_key = APIKey(
            key=generate_api_key(),
            user_id=user.id,
            name=f"API Key for {username}",
            is_active=True,
            allowed_models=json.dumps(allowed_models) if allowed_models else None,
            rate_limit_rpm=rate_limit_rpm,
            rate_limit_tpm=rate_limit_tpm
        )
        db.add(api_key)
        db.commit()
        
        logger.info(f"User created: {username}")
        logger.info(f"API Key: {api_key.key}")
        logger.info("Please save this API key securely!")
        
        return user, api_key
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create user and API key")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--email", help="Email")
    parser.add_argument("--quota-tokens", type=int, help="Monthly token quota")
    parser.add_argument("--quota-amount", type=float, help="Monthly amount quota")
    parser.add_argument("--allowed-models", help="Comma-separated list of allowed models")
    parser.add_argument("--rate-limit-rpm", type=int, help="Rate limit RPM")
    parser.add_argument("--rate-limit-tpm", type=int, help="Rate limit TPM")
    args = parser.parse_args()
    
    allowed_models = args.allowed_models.split(",") if args.allowed_models else None
    
    create_user(
        username=args.username,
        email=args.email,
        monthly_quota_tokens=args.quota_tokens,
        monthly_quota_amount=args.quota_amount,
        allowed_models=allowed_models,
        rate_limit_rpm=args.rate_limit_rpm,
        rate_limit_tpm=args.rate_limit_tpm
    )
