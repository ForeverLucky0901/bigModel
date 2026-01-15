"""
管理后台API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime
from app.models.base import get_db
from app.models.user import User, APIKey
from app.models.usage import UsageDaily
from app.api.auth import get_current_user
from app.utils.logger import logger
import secrets

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_user)):
    """要求管理员权限"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ==================== 用户管理 ====================

@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """获取用户列表"""
    users = db.query(User).all()
    return [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "is_active": u.is_active,
        "is_admin": u.is_admin,
        "monthly_quota_tokens": u.monthly_quota_tokens,
        "monthly_quota_amount": u.monthly_quota_amount,
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in users]


class CreateUserRequest(BaseModel):
    username: str
    email: Optional[str] = None
    monthly_quota_tokens: int = 1000000
    monthly_quota_amount: float = 10.0


@router.post("/users")
async def create_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """创建用户"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    user = User(
        username=request.username,
        email=request.email,
        is_active=True,
        is_admin=False,
        monthly_quota_tokens=request.monthly_quota_tokens,
        monthly_quota_amount=request.monthly_quota_amount
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "monthly_quota_tokens": user.monthly_quota_tokens
    }


class UpdateUserRequest(BaseModel):
    is_active: Optional[bool] = None
    monthly_quota_tokens: Optional[int] = None
    monthly_quota_amount: Optional[float] = None


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if request.is_active is not None:
        user.is_active = request.is_active
    if request.monthly_quota_tokens is not None:
        user.monthly_quota_tokens = request.monthly_quota_tokens
    if request.monthly_quota_amount is not None:
        user.monthly_quota_amount = request.monthly_quota_amount
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "is_active": user.is_active,
        "monthly_quota_tokens": user.monthly_quota_tokens
    }


# ==================== API Key管理 ====================

def generate_api_key() -> str:
    """生成API Key"""
    return f"sk-proxy-{secrets.token_urlsafe(32)}"


@router.get("/api-keys")
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取API Key列表（管理员看全部，普通用户看自己的）"""
    if current_user.is_admin:
        keys = db.query(APIKey).all()
    else:
        keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    
    return [{
        "id": k.id,
        "key": k.key,
        "user_id": k.user_id,
        "user": {
            "id": k.user.id,
            "username": k.user.username
        } if k.user else None,
        "name": k.name,
        "is_active": k.is_active,
        "created_at": k.created_at.isoformat() if k.created_at else None
    } for k in keys]


class CreateKeyRequest(BaseModel):
    user_id: int
    name: Optional[str] = None


@router.post("/api-keys")
async def create_api_key(
    request: CreateKeyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建API Key"""
    # 普通用户只能为自己创建
    if not current_user.is_admin and request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only create keys for yourself"
        )
    
    # 检查用户是否存在
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    api_key = APIKey(
        key=generate_api_key(),
        user_id=request.user_id,
        name=request.name or f"API Key for {user.username}",
        is_active=True
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return {
        "id": api_key.id,
        "key": api_key.key,
        "user_id": api_key.user_id,
        "name": api_key.name,
        "is_active": api_key.is_active
    }


class UpdateKeyRequest(BaseModel):
    is_active: Optional[bool] = None
    name: Optional[str] = None


@router.patch("/api-keys/{key_id}")
async def update_api_key(
    key_id: int,
    request: UpdateKeyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新API Key"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found"
        )
    
    # 普通用户只能修改自己的Key
    if not current_user.is_admin and api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own keys"
        )
    
    if request.is_active is not None:
        api_key.is_active = request.is_active
    if request.name is not None:
        api_key.name = request.name
    
    db.commit()
    db.refresh(api_key)
    
    return {
        "id": api_key.id,
        "is_active": api_key.is_active,
        "name": api_key.name
    }


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除API Key"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found"
        )
    
    # 普通用户只能删除自己的Key
    if not current_user.is_admin and api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own keys"
        )
    
    db.delete(api_key)
    db.commit()
    
    return {"message": "API Key deleted"}


# ==================== 用量统计 ====================

@router.get("/usage")
async def get_usage_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """获取用量统计"""
    # 总请求数和总Token数
    from app.models.usage import UsageRecord
    stats = db.query(
        func.count(UsageRecord.id).label('total_requests'),
        func.sum(UsageRecord.total_tokens).label('total_tokens')
    ).first()
    
    # 活跃用户数（最近30天有请求的用户）
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = db.query(func.count(func.distinct(UsageRecord.user_id))).filter(
        UsageRecord.created_at >= thirty_days_ago
    ).scalar()
    
    # 每日用量记录（最近30天）
    daily_usage = db.query(UsageDaily).order_by(UsageDaily.date.desc()).limit(30).all()
    
    return {
        "total_requests": stats.total_requests or 0,
        "total_tokens": stats.total_tokens or 0,
        "active_users": active_users or 0,
        "records": [{
            "id": d.id,
            "user_id": d.user_id,
            "user": {
                "id": d.user.id,
                "username": d.user.username
            } if d.user else None,
            "date": d.date,
            "total_requests": d.total_requests,
            "total_tokens": d.total_tokens
        } for d in daily_usage]
    }
