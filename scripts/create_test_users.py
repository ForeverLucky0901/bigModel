"""
快速创建测试用户（用于开发测试）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.create_admin import create_admin
from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models.user import User, APIKey
from app.utils.logger import logger
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def generate_api_key() -> str:
    import secrets
    return f"sk-proxy-{secrets.token_urlsafe(32)}"

def create_test_users():
    """创建测试用户"""
    db: Session = SessionLocal()
    try:
        # 创建管理员账号
        logger.info("Creating admin user...")
        create_admin("admin", "admin@example.com", "admin123")
        
        # 创建普通测试用户
        logger.info("Creating test user...")
        test_user = db.query(User).filter(User.username == "test").first()
        if not test_user:
            test_user = User(
                username="test",
                email="test@example.com",
                password_hash=get_password_hash("test123"),
                is_active=True,
                is_admin=False,
                monthly_quota_tokens=1000000,
                monthly_quota_amount=10.0
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            
            # 创建API Key
            api_key = APIKey(
                key=generate_api_key(),
                user_id=test_user.id,
                name="Test API Key",
                is_active=True
            )
            db.add(api_key)
            db.commit()
            logger.info(f"Test user created: test / test123")
        
        logger.info("\n" + "="*50)
        logger.info("测试账号信息：")
        logger.info("="*50)
        logger.info("管理员账号：")
        logger.info("  用户名: admin")
        logger.info("  密码: admin123")
        logger.info("")
        logger.info("普通用户：")
        logger.info("  用户名: test")
        logger.info("  密码: test123")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"Failed to create test users: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()
