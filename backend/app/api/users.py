from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
import csv
import io
from fastapi.responses import StreamingResponse
from ..core.database import get_db
from ..models.user import User
from ..schemas import UserResponse, UserCreate, UserUpdate, Response, PageResponse
from .deps import get_current_user, require_permission, check_user_permission
from ..core.security import get_password_hash
from ..core.logger import log_operation

# 导入用户默认密码
DEFAULT_IMPORT_PASSWORD = "123456"

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=Response)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    department_id: Optional[str] = None,
    role_id: Optional[str] = None,
    status: Optional[str] = None,
    is_project_leader: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户列表（分页、筛选，任何登录用户都可查看）"""
    from ..models.product import Product

    query = db.query(User)

    if keyword:
        query = query.filter((User.username.contains(keyword)) | (User.name.contains(keyword)))
    if department_id:
        query = query.filter(User.department_id == department_id)
    if role_id:
        query = query.filter(User.role_id == role_id)
    if status:
        query = query.filter(User.status == status)

    # 过滤项目负责人（来自产品/项目的负责人）
    if is_project_leader:
        from ..models.product import Product
        manager_ids = db.query(Product.manager_id).filter(
            Product.manager_id.isnot(None)
        ).distinct().all()
        if manager_ids:
            query = query.filter(User.id.in_([mid[0] for mid in manager_ids]))
        else:
            query = query.filter(User.id == None)

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()

    return Response(
        data=PageResponse(
            items=[{
                "id": u.id,
                "username": u.username,
                "name": u.name,
                "email": u.email,
                "phone": u.phone,
                "department_id": u.department_id,
                "role_id": u.role_id,
                "status": u.status,
                "created_at": u.created_at,
                "last_login_at": u.last_login_at
            } for u in items],
            total=total,
            page=page,
            size=size
        )
    )


@router.post("", response_model=Response)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageUsers"))
):
    """创建用户"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=user_data.username,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        department_id=user_data.department_id,
        role_id=user_data.role_id,
        email=user_data.email,
        phone=user_data.phone
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    log_operation(
        user_id=current_user.id,
        action="CREATE_USER",
        resource_type="user",
        resource_id=user.id,
        description=f"创建用户：{user.username}",
        ip_address="unknown"
    )

    return Response(message="用户创建成功", data={"id": user.id})


@router.get("/me/project-groups", response_model=Response)
async def get_my_project_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户所属的项目组及角色"""
    from ..models.project_group import ProjectGroup, project_group_members
    from ..models.product import Product

    # 获取用户参与的所有项目组及其角色
    memberships = db.query(
        ProjectGroup,
        project_group_members.c.role_type
    ).join(
        project_group_members,
        ProjectGroup.id == project_group_members.c.group_id
    ).filter(
        project_group_members.c.user_id == current_user.id,
        ProjectGroup.status != "deleted"
    ).all()

    result = []
    for pg, role_type in memberships:
        # 获取负责人信息
        leader = db.query(User).filter(User.id == pg.leader_id).first() if pg.leader_id else None

        # 获取该组的产品列表
        products = db.query(Product).filter(
            Product.project_group_id == pg.id,
            Product.status == "active"
        ).all()

        products_list = [{
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "manager": p.manager,
            "status": p.status
        } for p in products]

        result.append({
            "id": pg.id,
            "name": pg.name,
            "code": pg.code,
            "leader_id": pg.leader_id,
            "leader_name": leader.name if leader else None,
            "role_type": role_type,  # manager 或 engineer
            "role_label": "项目经理" if role_type == "manager" else "工程师",
            "products": products_list,
            "product_count": len(products_list),
            "status": pg.status
        })

    return Response(data=result)


@router.get("/export")
async def export_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageUsers"))
):
    """导出用户数据为 CSV"""
    users = db.query(User).order_by(User.created_at.desc()).all()

    output = io.StringIO()
    output.write('\ufeff')  # UTF-8 BOM
    fieldnames = ['username', 'name', 'email', 'phone', 'department_id', 'role_id', 'status', 'created_at']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for u in users:
        writer.writerow({
            'username': u.username,
            'name': u.name or '',
            'email': u.email or '',
            'phone': u.phone or '',
            'department_id': u.department_id or '',
            'role_id': u.role_id or '',
            'status': u.status or 'active',
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S') if u.created_at else ''
        })

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"}
    )


@router.post("/import")
async def import_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageUsers"))
):
    """批量导入用户（合并模式，密码统一为 123456）"""
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="仅支持 CSV 格式文件")

    content = await file.read()
    try:
        try:
            decoded = content.decode('utf-8-sig')
        except:
            decoded = content.decode('gbk')
    except:
        raise HTTPException(status_code=400, detail="文件编码不支持，请使用 UTF-8 或 GBK 编码的 CSV")

    reader = csv.DictReader(io.StringIO(decoded))
    success_count = 0
    skipped_count = 0
    errors = []

    # 验证表头
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV 文件为空或格式错误")
    required_fields = ['username', 'name']
    for field in required_fields:
        if field not in reader.fieldnames:
            raise HTTPException(status_code=400, detail=f"CSV 表头缺少必需字段：{field}")

    for row_num, row in enumerate(reader, start=2):
        username = row.get('username', '').strip()
        name = row.get('name', '').strip()

        if not username or not name:
            errors.append(f"第 {row_num} 行：用户名和姓名不能为空")
            skipped_count += 1
            continue

        # 检查用户名是否已存在
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            errors.append(f"第 {row_num} 行：用户名 {username} 已存在，跳过")
            skipped_count += 1
            continue

        # 获取可选字段
        email = row.get('email', '').strip() or None
        phone = row.get('phone', '').strip() or None
        department_id = row.get('department_id', '').strip() or None
        role_id = row.get('role_id', '').strip() or 'role_guest'  # 默认为访客
        status = row.get('status', '').strip() or 'active'

        # 验证 status
        if status not in ('active', 'disabled'):
            status = 'active'

        try:
            user = User(
                username=username,
                name=name,
                email=email,
                phone=phone,
                department_id=department_id,
                role_id=role_id,
                status=status,
                password_hash=get_password_hash(DEFAULT_IMPORT_PASSWORD)
            )
            db.add(user)
            db.commit()
            success_count += 1
        except Exception as e:
            db.rollback()
            errors.append(f"第 {row_num} 行：创建用户 {username} 失败 - {str(e)}")
            skipped_count += 1

    log_operation(
        user_id=current_user.id,
        action="IMPORT_USERS",
        resource_type="user",
        resource_id="bulk",
        description=f"批量导入用户：成功{success_count}条，跳过{skipped_count}条",
        ip_address="unknown"
    )

    return Response(message="导入完成", data={
        "success_count": success_count,
        "skipped_count": skipped_count,
        "errors": errors[:10] if errors else []  # 最多返回10条错误信息
    })


@router.get("/{user_id}", response_model=Response)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户详情（本人或管理员可查看）"""
    # 权限检查：非本人且无管理权限不能查看
    if user_id != current_user.id and not check_user_permission(current_user, "manageUsers", db):
        raise HTTPException(status_code=403, detail="您没有权限查看此用户详情")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return Response(data={
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "department_id": user.department_id,
        "role_id": user.role_id,
        "status": user.status,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at
    })


@router.put("/{user_id}", response_model=Response)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageUsers"))
):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    log_operation(
        user_id=current_user.id,
        action="UPDATE_USER",
        resource_type="user",
        resource_id=user_id,
        description=f"更新用户：{user.username}",
        ip_address="unknown"
    )

    return Response(message="用户更新成功")


@router.delete("/{user_id}", response_model=Response)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageUsers"))
):
    """删除用户（软删除）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.status = "disabled"
    db.commit()

    log_operation(
        user_id=current_user.id,
        action="DELETE_USER",
        resource_type="user",
        resource_id=user_id,
        description=f"禁用用户：{user.username}",
        ip_address="unknown"
    )

    return Response(message="用户已禁用")
