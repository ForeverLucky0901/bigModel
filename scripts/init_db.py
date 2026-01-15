"""
数据库初始化脚本
创建所有表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models.base import Base, engine
from app.utils.logger import logger

def init_db():
    """初始化数据库"""
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

if __name__ == "__main__":
    init_db()
