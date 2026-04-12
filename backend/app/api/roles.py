from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
from ..core.database import get_db
from ..models.user import User
from ..models.role import Role
from ..schemas import Response, PageResponse
from .deps import get_current_user, require_permission
from ..core.logger import log_operation

router = APIRouter(prefix="/roles", tags=["角色权限管理"])


@router.get("", response_model=Response)
async def get_roles(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageRoles"))
):
    """获取角色列表"""
    query = db.query(Role)

    if keyword:
        query = query.filter((Role.name.contains(keyword)) | (Role.code.contains(keyword)))
    if status:
        query = query.filter(Role.status == status)

    total = query.count()
    items = query.order_by(Role.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return Response(
        data=PageResponse(
            items=[{
                "id": r.id,
                "name": r.name,
                "code": r.code,
                "permissions": r.permissions,
                "status": r.status,
                "created_at": r.created_at
            } for r in items],
            total=total,
            page=page,
            size=size
        )
    )


@router.post("", response_model=Response)
async def create_role(
    name: str = Body(...),
    code: str = Body(...),
    permissions: dict = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageRoles"))
):
    """创建角色"""
    existing = db.query(Role).filter(Role.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="角色编码已存在")

    role = Role(name=name, code=code, permissions=permissions or {})
    db.add(role)
    db.commit()
    db.refresh(role)

    log_operation(
        user_id=current_user.id,
        action="CREATE_ROLE",
        resource_type="role",
        resource_id=role.id,
        description=f"创建角色：{role.name}",
        ip_address="unknown"
    )

    return Response(message="角色创建成功", data={"id": role.id})


@router.put("/{role_id}", response_model=Response)
async def update_role(
    role_id: str,
    name: Optional[str] = Body(None),
    permissions: Optional[dict] = Body(None),
    status: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageRoles"))
):
    """更新角色"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if name:
        role.name = name
    if permissions is not None:
        role.permissions = permissions
    if status:
        role.status = status

    db.commit()

    log_operation(
        user_id=current_user.id,
        action="UPDATE_ROLE",
        resource_type="role",
        resource_id=role_id,
        description=f"更新角色：{role.name}",
        ip_address="unknown"
    )

    return Response(message="角色更新成功")


@router.delete("/{role_id}", response_model=Response)
async def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageRoles"))
):
    """删除角色"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    role.status = "disabled"
    db.commit()

    log_operation(
        user_id=current_user.id,
        action="DELETE_ROLE",
        resource_type="role",
        resource_id=role_id,
        description=f"禁用角色：{role.name}",
        ip_address="unknown"
    )

    return Response(message="角色已禁用")
