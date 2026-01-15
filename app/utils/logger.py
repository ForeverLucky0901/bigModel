"""
日志配置
"""
import logging
import sys
from pathlib import Path
from app.config import settings


def setup_logger():
    """配置日志"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # 创建日志目录
    if settings.LOG_FILE_PATH:
        log_file = Path(settings.LOG_FILE_PATH)
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 配置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # 文件处理器
    handlers = [console_handler]
    if settings.LOG_FILE_PATH:
        file_handler = logging.FileHandler(settings.LOG_FILE_PATH)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # 配置根日志
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 第三方库日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


logger = setup_logger()
