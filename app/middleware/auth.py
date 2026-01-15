"""
鉴权中间件
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.user import APIKey, User
from app.models.base import get_db
from app.utils.logger import logger

security = HTTPBearer()


async def verify_api_key(request: Request, credentials: HTTPAuthorizationCredentials = None) -> tuple[User, APIKey]:
    """
    验证API Key
    
    Returns:
        (user, api_key)
    """
    if not credentials:
        # 尝试从header获取
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header"
            )
        token = auth_header[7:]  # 去掉 "Bearer " 前缀
    else:
        token = credentials.credentials
    
    # 从数据库查询
    from app.models.base import SessionLocal
    db: Session = SessionLocal()
    try:
        api_key = db.query(APIKey).filter(
            APIKey.key == token,
            APIKey.is_active == True
        ).first()
        
        if not api_key:
            logger.warning(f"Invalid API key attempted: {token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        user = db.query(User).filter(User.id == api_key.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive"
            )
        
        # 将user和api_key存储到request.state
        request.state.user = user
        request.state.api_key = api_key
        
        return user, api_key
        
    finally:
        db.close()
