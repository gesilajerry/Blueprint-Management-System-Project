from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional
from ..core.database import get_db
from ..core.security import decode_access_token
from ..core.config import settings
from ..core.permissions import DEFAULT_ROLE_PERMISSIONS, PERMISSION_KEYS
from ..models.user import User
from ..models.role import Role
from ..schemas import TokenData

security = HTTPBearer(auto_error=False)


# 角色码映射（role_id -> role_code）
ROLE_CODE_MAP = {
    "role_admin": "admin",
    "role_cto": "cto",
    "role_designer": "designer",
    "role_reviewer": "reviewer",
    "role_guest": "guest",
    "role_project_manager": "project_manager",
    "role_engineer": "engineer",
    "role_archive_manager": "archive_manager",
    "role_observer": "observer"
}


def get_user_role_code(user: User) -> str:
    """获取用户角色码"""
    if not user.role_id:
        return "guest"
    return ROLE_CODE_MAP.get(user.role_id, "guest")


def check_user_permission(user: User, permission: str, db: Session = None) -> bool:
    """检查用户是否有指定权限（优先使用数据库中的自定义权限）"""
    # 如果用户有角色，尝试从数据库获取自定义权限
    if user.role_id and db:
        role = db.query(Role).filter(Role.id == user.role_id, Role.status == "active").first()
        if role and role.permissions:
            # 使用数据库中存储的自定义权限
            return role.permissions.get(permission, False)

    # 否则使用硬编码的权限矩阵
    role_code = get_user_role_code(user)
    role_permissions = DEFAULT_ROLE_PERMISSIONS.get(role_code, DEFAULT_ROLE_PERMISSIONS["guest"])
    return role_permissions.get(permission, False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败，请先登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception

    if user.status != "active":
        raise HTTPException(status_code=403, detail="用户已被禁用")

    return user


def require_permission(permission: str):
    """权限检查装饰器"""
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if not check_user_permission(current_user, permission, db):
            role_code = get_user_role_code(current_user)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 '{permission}' 权限，当前角色 '{role_code}' 无此权限"
            )
        return current_user

    return permission_checker


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """可选的当前用户（不强制登录）"""
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

