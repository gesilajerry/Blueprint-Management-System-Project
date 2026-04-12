from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from typing import Optional
from ..core.database import get_db
from ..models.user import User
from ..models.department import Department
from ..schemas import Response, PageResponse
from .deps import get_current_user, require_permission
from ..core.logger import log_operation

router = APIRouter(prefix="/departments", tags=["部门管理"])


@router.get("", response_model=Response)
async def get_departments(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取部门列表（任何登录用户都可查看）"""
    query = db.query(Department)

    if keyword:
        query = query.filter((Department.name.contains(keyword)) | (Department.code.contains(keyword)))
    if status:
        query = query.filter(Department.status == status)

    total = query.count()
    items = query.order_by(Department.sort).offset((page - 1) * size).limit(size).all()

    return Response(
        data=PageResponse(
            items=[{
                "id": d.id,
                "name": d.name,
                "code": d.code,
                "manager": d.manager,
                "sort": d.sort,
                "status": d.status,
                "created_at": d.created_at
            } for d in items],
            total=total,
            page=page,
            size=size
        )
    )


@router.post("", response_model=Response)
async def create_department(
    name: str = Form(...),
    code: str = Form(...),
    manager: Optional[str] = Form(None),
    sort: int = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageDepartments"))
):
    """创建部门"""
    existing = db.query(Department).filter(Department.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="部门编码已存在")

    dept = Department(name=name, code=code, manager=manager, sort=sort)
    db.add(dept)
    db.commit()
    db.refresh(dept)

    log_operation(
        user_id=current_user.id,
        action="CREATE_DEPARTMENT",
        resource_type="department",
        resource_id=dept.id,
        description=f"创建部门：{dept.name}",
        ip_address="unknown"
    )

    return Response(message="部门创建成功", data={"id": dept.id})


@router.post("/{dept_id}", response_model=Response)
async def update_department(
    dept_id: str,
    name: Optional[str] = Form(None),
    manager: Optional[str] = Form(None),
    sort: Optional[int] = Form(None),
    status: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageDepartments"))
):
    """更新部门"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    if name:
        dept.name = name
    if manager:
        dept.manager = manager
    if sort is not None:
        dept.sort = sort
    if status:
        dept.status = status

    db.commit()

    log_operation(
        user_id=current_user.id,
        action="UPDATE_DEPARTMENT",
        resource_type="department",
        resource_id=dept_id,
        description=f"更新部门：{dept.name}",
        ip_address="unknown"
    )

    return Response(message="部门更新成功")


@router.delete("/{dept_id}", response_model=Response)
async def delete_department(
    dept_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageDepartments"))
):
    """删除部门"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    dept.status = "disabled"
    db.commit()

    log_operation(
        user_id=current_user.id,
        action="DELETE_DEPARTMENT",
        resource_type="department",
        resource_id=dept_id,
        description=f"禁用部门：{dept.name}",
        ip_address="unknown"
    )

    return Response(message="部门已禁用")
