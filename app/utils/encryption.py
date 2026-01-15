"""
密钥加密工具
使用 Fernet (对称加密) 加密上游 API Key
"""
from cryptography.fernet import Fernet
from app.config import settings
import base64
import hashlib


def get_encryption_key() -> bytes:
    """从配置获取或生成加密密钥"""
    key_str = settings.ENCRYPTION_KEY
    if not key_str or len(key_str) < 32:
        raise ValueError("ENCRYPTION_KEY must be at least 32 bytes. Generate with: openssl rand -hex 32")
    
    # 使用 SHA256 哈希确保是32字节
    key_hash = hashlib.sha256(key_str.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)


def encrypt_key(plain_key: str) -> str:
    """加密密钥"""
    f = Fernet(get_encryption_key())
    encrypted = f.encrypt(plain_key.encode())
    return encrypted.decode()


def decrypt_key(encrypted_key: str) -> str:
    """解密密钥"""
    f = Fernet(get_encryption_key())
    decrypted = f.decrypt(encrypted_key.encode())
    return decrypted.decode()
