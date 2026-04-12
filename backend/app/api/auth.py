from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from ..core.database import get_db
from ..core.security import verify_password, get_password_hash, create_access_token
from ..core.config import settings
from ..core.permissions import PERMISSION_KEYS
from ..models.user import User
from ..schemas import UserLogin, Token, UserResponse, Response
from ..core.logger import log_operation
from .deps import get_current_user, check_user_permission, get_user_role_code

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=Response)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.password_hash):
        log_operation(
            user_id="anonymous",
            action="LOGIN_FAILED",
            resource_type="user",
            description=f"登录失败：用户名或密码错误 - {login_data.username}",
            ip_address="unknown"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(status_code=403, detail="用户已被禁用")

    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    db.commit()

    # 生成 Token
    access_token = create_access_token(data={"sub": user.id, "username": user.username})

    log_operation(
        user_id=user.id,
        action="LOGIN_SUCCESS",
        resource_type="user",
        resource_id=user.id,
        description=f"用户登录成功：{user.username}",
        ip_address="unknown"
    )

    return Response(
        message="登录成功",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "email": user.email,
                "department_id": user.department_id,
                "role_id": user.role_id
            }
        }
    )


@router.get("/me", response_model=Response)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户信息（包含完整权限）"""
    # 获取用户所有权限
    user_permissions = {}
    for perm_key in PERMISSION_KEYS.keys():
        user_permissions[perm_key] = check_user_permission(current_user, perm_key, db)

    role_code = get_user_role_code(current_user)

    return Response(
        data={
            "id": current_user.id,
            "username": current_user.username,
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "department_id": current_user.department_id,
            "role_id": current_user.role_id,
            "role_code": role_code,
            "status": current_user.status,
            "last_login_at": current_user.last_login_at,
            "permissions": user_permissions
        }
    )


@router.post("/logout", response_model=Response)
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    log_operation(
        user_id=current_user.id,
        action="LOGOUT",
        resource_type="user",
        resource_id=current_user.id,
        description=f"用户登出：{current_user.username}",
        ip_address="unknown"
    )

    return Response(message="登出成功")
