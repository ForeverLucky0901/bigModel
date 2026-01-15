"""
创建管理员用户和API Key（支持密码登录）
"""
import sys
import os
import secrets
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models.user import User, APIKey
from app.utils.logger import logger
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

def generate_api_key() -> str:
    """生成API Key"""
    return f"sk-proxy-{secrets.token_urlsafe(32)}"

def create_admin(username: str = "admin", email: str = "admin@example.com", password: str = "admin123"):
    """创建管理员用户（带密码）"""
    db: Session = SessionLocal()
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            # 如果用户存在但没有密码，更新密码
            if not existing_user.password_hash:
                existing_user.password_hash = get_password_hash(password)
                existing_user.is_admin = True
                db.commit()
                logger.info(f"Updated existing user {username} with password and admin privileges")
                return existing_user
            else:
                logger.warning(f"User {username} already exists with password")
                return existing_user
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            is_active=True,
            is_admin=True,
            monthly_quota_tokens=100000000,  # 管理员大额度
            monthly_quota_amount=1000.0
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建API Key
        api_key = APIKey(
            key=generate_api_key(),
            user_id=user.id,
            name="Admin API Key",
            is_active=True
        )
        db.add(api_key)
        db.commit()
        
        logger.info(f"Admin user created: {username}")
        logger.info(f"Password: {password}")
        logger.info(f"API Key: {api_key.key}")
        logger.info("Please save this information securely!")
        
        return user
        
    except Exception as e:
        logger.error(f"Failed to create admin: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--email", default="admin@example.com", help="Admin email")
    parser.add_argument("--password", default="admin123", help="Admin password")
    args = parser.parse_args()
    
    create_admin(args.username, args.email, args.password)
