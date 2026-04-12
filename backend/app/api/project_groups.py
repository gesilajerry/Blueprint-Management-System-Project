from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from typing import Optional
from ..core.database import get_db
from ..models.project_group import ProjectGroup, project_group_members
from ..models.user import User
from ..schemas import Response, PageResponse
from .deps import get_current_user, require_permission, check_user_permission
from ..core.logger import log_operation

router = APIRouter(prefix="/project-groups", tags=["项目组管理"])


@router.get("", response_model=Response)
async def get_project_groups(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目组列表"""
    # 基础查询
    query = db.query(ProjectGroup).filter(ProjectGroup.status != "deleted")

    # 根据权限过滤：有 viewAllDrawings（CTO/管理员/审定人）可以查看所有项目组
    # 其他用户只能查看自己参与的项目组
    if not check_user_permission(current_user, "viewAllDrawings", db):
        # 只能查看自己参与的项目组
        query = query.filter(
            ProjectGroup.id.in_(
                db.query(project_group_members.c.group_id)
                .filter(project_group_members.c.user_id == current_user.id)
            )
        )

    # 筛选条件
    if keyword:
        query = query.filter(
            (ProjectGroup.name.contains(keyword)) | (ProjectGroup.code.contains(keyword))
        )
    if status:
        query = query.filter(ProjectGroup.status == status)

    total = query.count()
    items = query.order_by(ProjectGroup.created_at.desc()).offset((page - 1) * size).limit(size).all()

    result_items = []
    for pg in items:
        # 获取负责人信息
        leader = db.query(User).filter(User.id == pg.leader_id).first() if pg.leader_id else None

        # 获取成员数量
        member_count = db.query(project_group_members).filter(
            project_group_members.c.group_id == pg.id
        ).count()

        # 获取产品数量
        from ..models.product import Product
        product_count = db.query(Product).filter(Product.project_group_id == pg.id).count()

        result_items.append({
            "id": pg.id,
            "name": pg.name,
            "code": pg.code,
            "leader_id": pg.leader_id,
            "leader_name": leader.name if leader else None,
            "department_id": pg.department_id,
            "member_count": member_count,
            "product_count": product_count,
            "status": pg.status,
            "created_at": pg.created_at.isoformat() if pg.created_at else None,
            "updated_at": pg.updated_at.isoformat() if pg.updated_at else None
        })

    return Response(
        data=PageResponse(
            items=result_items,
            total=total,
            page=page,
            size=size
        )
    )


@router.get("/{group_id}", response_model=Response)
async def get_project_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目组详情"""
    pg = db.query(ProjectGroup).filter(ProjectGroup.id == group_id).first()
    if not pg:
        raise HTTPException(status_code=404, detail="项目组不存在")

    # 获取负责人信息
    leader = db.query(User).filter(User.id == pg.leader_id).first() if pg.leader_id else None

    # 获取成员列表
    members = db.query(User, project_group_members.c.role_type).join(
        project_group_members, User.id == project_group_members.c.user_id
    ).filter(project_group_members.c.group_id == group_id).all()

    members_list = [{
        "id": m[0].id,
        "name": m[0].name,
        "username": m[0].username,
        "role_type": m[1],
        "email": m[0].email,
        "phone": m[0].phone
    } for m in members]

    # 获取产品列表
    from ..models.product import Product
    products = db.query(Product).filter(Product.project_group_id == group_id).all()
    products_list = [{
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "status": p.status,
        "manager": p.manager
    } for p in products]

    return Response(data={
        "id": pg.id,
        "name": pg.name,
        "code": pg.code,
        "leader_id": pg.leader_id,
        "leader_name": leader.name if leader else None,
        "department_id": pg.department_id,
        "status": pg.status,
        "members": members_list,
        "products": products_list,
        "created_at": pg.created_at.isoformat() if pg.created_at else None,
        "updated_at": pg.updated_at.isoformat() if pg.updated_at else None
    })


@router.post("", response_model=Response)
async def create_project_group(
    name: str = Form(...),
    code: str = Form(...),
    leader_id: str = Form(...),
    member_ids: str = Form(None),  # 逗号分隔的用户 ID 列表
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageProjectGroups"))
):
    """创建项目组"""
    # 检查组编号是否已存在
    existing = db.query(ProjectGroup).filter(ProjectGroup.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目组编号已存在")

    # 验证负责人是否存在
    leader = db.query(User).filter(User.id == leader_id).first()
    if not leader:
        raise HTTPException(status_code=404, detail="指定的负责人不存在")

    pg = ProjectGroup(
        name=name,
        code=code,
        leader_id=leader_id
    )

    db.add(pg)
    db.commit()
    db.refresh(pg)

    # 将负责人添加为项目经理
    from sqlalchemy import insert
    db.execute(insert(project_group_members).values(
        group_id=pg.id,
        user_id=leader_id,
        role_type='manager'
    ))

    # 添加其他成员（工程师）
    if member_ids:
        member_id_list = [m.strip() for m in member_ids.split(',') if m.strip()]
        for member_id in member_id_list:
            if member_id != leader_id:  # 避免重复添加负责人
                db.execute(insert(project_group_members).values(
                    group_id=pg.id,
                    user_id=member_id,
                    role_type='engineer'
                ))

    db.commit()

    log_operation(
        user_id=current_user.id,
        action="CREATE_PROJECT_GROUP",
        resource_type="project_group",
        resource_id=pg.id,
        description=f"创建项目组：{pg.name}",
        ip_address="unknown"
    )

    return Response(message="项目组创建成功", data={"id": pg.id})


@router.post("/{group_id}", response_model=Response)
async def update_project_group(
    group_id: str,
    name: Optional[str] = Form(None),
    leader_id: Optional[str] = Form(None),
    member_ids: Optional[str] = Form(None),  # 逗号分隔的用户 ID 列表
    status: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageProjectGroups"))
):
    """更新项目组"""
    pg = db.query(ProjectGroup).filter(ProjectGroup.id == group_id).first()
    if not pg:
        raise HTTPException(status_code=404, detail="项目组不存在")

    update_data = {k: v for k, v in {
        "name": name,
        "leader_id": leader_id,
        "status": status
    }.items() if v is not None}

    for field, value in update_data.items():
        setattr(pg, field, value)

    # 更新成员
    if member_ids is not None:
        from sqlalchemy import delete
        # 清除现有成员
        db.execute(delete(project_group_members).where(project_group_members.c.group_id == group_id))
        db.commit()

        # 添加负责人为项目经理
        if leader_id:
            from sqlalchemy import insert
            db.execute(insert(project_group_members).values(
                group_id=group_id,
                user_id=leader_id,
                role_type='manager'
            ))

        # 添加其他成员（工程师）
        if member_ids:
            member_id_list = [m.strip() for m in member_ids.split(',') if m.strip()]
            for member_id in member_id_list:
                if member_id != leader_id:  # 避免重复添加负责人
                    db.execute(insert(project_group_members).values(
                        group_id=group_id,
                        user_id=member_id,
                        role_type='engineer'
                    ))

    db.commit()

    log_operation(
        user_id=current_user.id,
        action="UPDATE_PROJECT_GROUP",
        resource_type="project_group",
        resource_id=group_id,
        description=f"更新项目组：{pg.name}",
        ip_address="unknown"
    )

    return Response(message="项目组更新成功")


@router.delete("/{group_id}", response_model=Response)
async def delete_project_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageProjectGroups"))
):
    """删除项目组（软删除）"""
    pg = db.query(ProjectGroup).filter(ProjectGroup.id == group_id).first()
    if not pg:
        raise HTTPException(status_code=404, detail="项目组不存在")

    pg.status = "deleted"
    db.commit()

    log_operation(
        user_id=current_user.id,
        action="DELETE_PROJECT_GROUP",
        resource_type="project_group",
        resource_id=group_id,
        description=f"删除项目组：{pg.name}",
        ip_address="unknown"
    )

    return Response(message="项目组已删除")


@router.post("/{group_id}/members", response_model=Response)
async def add_member(
    group_id: str,
    user_id: str,
    role_type: str,  # manager 或 engineer
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageProjectGroups"))
):
    """添加项目组成员"""
    if role_type not in ['manager', 'engineer']:
        raise HTTPException(status_code=400, detail="成员角色必须是 manager 或 engineer")

    pg = db.query(ProjectGroup).filter(ProjectGroup.id == group_id).first()
    if not pg:
        raise HTTPException(status_code=404, detail="项目组不存在")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已是成员
    existing = db.query(project_group_members).filter(
        project_group_members.c.group_id == group_id,
        project_group_members.c.user_id == user_id
    ).first()

    if existing:
        # 更新角色
        from sqlalchemy import update
        db.execute(update(project_group_members).where(
            project_group_members.c.group_id == group_id,
            project_group_members.c.user_id == user_id
        ).values(role_type=role_type))
        db.commit()
        return Response(message="成员角色更新成功")

    # 添加新成员
    from sqlalchemy import insert
    db.execute(insert(project_group_members).values(
        group_id=group_id,
        user_id=user_id,
        role_type=role_type
    ))
    db.commit()

    return Response(message="成员添加成功")


@router.delete("/{group_id}/members/{user_id}", response_model=Response)
async def remove_member(
    group_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageProjectGroups"))
):
    """移除项目组成员"""
    from sqlalchemy import delete

    db.execute(delete(project_group_members).where(
        project_group_members.c.group_id == group_id,
        project_group_members.c.user_id == user_id
    ))
    db.commit()

    return Response(message="成员已移除")
