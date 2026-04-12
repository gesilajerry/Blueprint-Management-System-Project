from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from ..core.database import get_db
from ..models.user import User
from ..models.product import Product
from ..schemas import Response, PageResponse
from .deps import get_current_user, require_permission
from ..core.logger import log_operation

router = APIRouter(prefix="/products", tags=["产品/项目管理"])


@router.get("", response_model=Response)
async def get_products(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取产品列表"""
    query = db.query(Product)

    if keyword:
        query = query.filter((Product.name.contains(keyword)) | (Product.code.contains(keyword)))
    if status:
        query = query.filter(Product.status == status)

    total = query.count()
    items = query.order_by(Product.created_at.desc()).offset((page - 1) * size).limit(size).all()

    # 获取负责人信息
    result_items = []
    for p in items:
        manager_name = p.manager
        if p.manager_id:
            manager_user = db.query(User).filter(User.id == p.manager_id).first()
            if manager_user:
                manager_name = manager_user.name
        result_items.append({
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "status": p.status,
            "project_group_id": p.project_group_id,
            "department_id": p.department_id,
            "manager": manager_name,
            "manager_id": p.manager_id,
            "start_date": str(p.start_date) if p.start_date else None,
            "created_at": p.created_at
        })

    return Response(
        data=PageResponse(
            items=result_items,
            total=total,
            page=page,
            size=size
        )
    )


@router.post("", response_model=Response)
async def create_product(
    name: str = Form(...),
    code: str = Form(...),
    project_group_id: Optional[str] = Form(None),
    department_id: Optional[str] = Form(None),
    manager: Optional[str] = Form(None),
    manager_id: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageProducts"))
):
    """创建产品"""
    existing = db.query(Product).filter(Product.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="立项编号已存在")

    # 如果提供了 manager_id，获取负责人姓名
    manager_name = manager
    if manager_id and not manager:
        manager_user = db.query(User).filter(User.id == manager_id).first()
        if manager_user:
            manager_name = manager_user.name

    product = Product(
        name=name,
        code=code,
        project_group_id=project_group_id,
        department_id=department_id,
        manager=manager_name,
        manager_id=manager_id,
        start_date=date.fromisoformat(start_date) if start_date else None
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    log_operation(
        user_id=current_user.id,
        action="CREATE_PRODUCT",
        resource_type="product",
        resource_id=product.id,
        description=f"创建产品：{product.name}",
        ip_address="unknown"
    )

    return Response(message="产品创建成功", data={"id": product.id})


@router.put("/{product_id}", response_model=Response)
async def update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    project_group_id: Optional[str] = Form(None),
    department_id: Optional[str] = Form(None),
    manager: Optional[str] = Form(None),
    manager_id: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageProducts"))
):
    """更新产品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    if name:
        product.name = name
    if project_group_id:
        product.project_group_id = project_group_id
    if department_id:
        product.department_id = department_id
    if manager is not None:
        product.manager = manager
    if manager_id is not None:
        product.manager_id = manager_id
        # 如果只提供了 manager_id 而没有 manager，自动获取姓名
        if manager is None:
            manager_user = db.query(User).filter(User.id == manager_id).first()
            if manager_user:
                product.manager = manager_user.name
    if start_date:
        product.start_date = date.fromisoformat(start_date)
    if status:
        product.status = status

    db.commit()

    log_operation(
        user_id=current_user.id,
        action="UPDATE_PRODUCT",
        resource_type="product",
        resource_id=product_id,
        description=f"更新产品：{product.name}",
        ip_address="unknown"
    )

    return Response(message="产品更新成功")


@router.delete("/{product_id}", response_model=Response)
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageProducts"))
):
    """删除产品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    product.status = "archived"
    db.commit()

    log_operation(
        user_id=current_user.id,
        action="DELETE_PRODUCT",
        resource_type="product",
        resource_id=product_id,
        description=f"归档产品：{product.name}",
        ip_address="unknown"
    )

    return Response(message="产品已归档")
