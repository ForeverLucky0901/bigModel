"""
添加password_hash字段到users表（如果不存在）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app.models.base import engine
from app.utils.logger import logger

def add_password_field():
    """添加password_hash字段"""
    try:
        with engine.connect() as conn:
            # 检查字段是否已存在
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='password_hash'
            """))
            
            if result.fetchone():
                logger.info("password_hash field already exists")
                return
            
            # 添加字段
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN password_hash VARCHAR(255)
            """))
            conn.commit()
            logger.info("password_hash field added successfully")
    except Exception as e:
        logger.error(f"Failed to add password_hash field: {e}")
        raise

if __name__ == "__main__":
    add_password_field()
