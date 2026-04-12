from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import os
import uuid
import io
import csv
import zipfile
from ..core.database import get_db
from ..core.config import settings
from ..models.user import User
from ..models.drawing import Drawing, DrawingVersion, DrawingStatus, ConfidentialityLevel, ReviewStatus
from ..schemas import Response, PageResponse, DrawingCreate, DrawingUpdate, DrawingVersionCreate
from .deps import get_current_user, require_permission, check_user_permission
from ..core.logger import log_operation

router = APIRouter(prefix="/drawings", tags=["图纸管理"])


def generate_drawing_no(product_code: str, db: Session) -> str:
    """生成图号：{产品代码}-{序号:4 位}"""
    # 获取该产品下最大的序号
    max_drawing = db.query(Drawing).filter(
        Drawing.drawing_no.like(f"{product_code}-%")
    ).order_by(Drawing.drawing_no.desc()).first()

    if max_drawing:
        # 提取序号部分（从最后一个连字符后面提取）
        parts = max_drawing.drawing_no.rsplit("-", 1)
        if len(parts) >= 2:
            try:
                seq = int(parts[1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
    else:
        seq = 1

    return f"{product_code}-{seq:04d}"


@router.get("", response_model=Response)
async def get_drawings(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    product_id: Optional[str] = None,
    project_group_id: Optional[str] = None,
    manager_id: Optional[str] = None,
    uploader_id: Optional[str] = None,
    creator_id: Optional[str] = None,
    confidentiality_level: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取图纸列表（分页、筛选）- 根据角色权限过滤

    权限层级：
    - CTO/管理员：查看所有图纸（viewAllDrawings）
    - 项目负责人：查看负责项目内的所有图纸（viewProjectDrawings）
    - 工程师/设计师：仅查看自己创建的图纸（viewOwnDrawings）
    - 审定人：查看所有图纸以便进行审定（viewAllDrawings）
    - 访客：无法查看图纸
    """
    from ..models.product import Product
    from ..models.project_group import project_group_members, ProjectGroup

    # 基础查询
    # 如果筛选"全部"，则包含所有状态的图纸；否则默认排除已删除的
    if status == 'all':
        query = db.query(Drawing)
    else:
        query = db.query(Drawing).filter(Drawing.status != DrawingStatus.DELETED)
    # 排除关联已归档产品的图纸
    query = query.join(Product).filter(Product.status == 'active')

    # 根据动态权限过滤图纸
    if check_user_permission(current_user, "viewAllDrawings", db):
        # CTO/管理员/审定人等可以查看所有图纸，不过滤
        pass
    elif check_user_permission(current_user, "viewProjectDrawings", db):
        # 项目负责人查看其负责项目内的所有图纸（通过 Product.manager_id 关联）
        product_ids = db.query(Product.id).filter(
            Product.manager_id == current_user.id
        ).all()

        if product_ids:
            query = query.filter(Drawing.product_id.in_([p.id for p in product_ids]))
        else:
            query = query.filter(Drawing.id == None)
    elif check_user_permission(current_user, "viewOwnDrawings", db):
        # 工程师/设计师只能查看自己创建的图纸
        query = query.filter(Drawing.creator_id == current_user.id)
    else:
        # 访客等无相关权限，无法查看任何图纸
        query = query.filter(Drawing.id == None)

    # 筛选条件
    if keyword:
        query = query.filter(
            (Drawing.drawing_no.contains(keyword)) | (Drawing.name.contains(keyword))
        )
    if product_id:
        query = query.filter(Drawing.product_id == product_id)
    if project_group_id:
        # 通过产品关联到项目组 - 使用条件避免重复 join
        from sqlalchemy.orm import aliased
        ProductAlias = aliased(Product)
        query = query.join(ProductAlias, Drawing.product_id == ProductAlias.id).filter(ProductAlias.project_group_id == project_group_id)
    if manager_id:
        # 通过产品关联到项目负责人
        from sqlalchemy.orm import aliased
        ProductAlias = aliased(Product)
        query = query.join(ProductAlias, Drawing.product_id == ProductAlias.id).filter(ProductAlias.manager_id == manager_id)
    if uploader_id:
        # 通过最新版本关联到上传人
        query = query.join(DrawingVersion).filter(
            DrawingVersion.is_latest == True,
            DrawingVersion.uploader_id == uploader_id
        )
    if creator_id:
        query = query.filter(Drawing.creator_id == creator_id)
    if confidentiality_level:
        query = query.filter(Drawing.confidentiality_level == confidentiality_level)
    if status and status != 'all':
        query = query.filter(Drawing.status == status)

    total = query.count()
    items = query.order_by(Drawing.created_at.desc()).offset((page - 1) * size).limit(size).all()

    # 获取最新版本和上传人信息
    from ..models.product import Product
    from ..models.project_group import ProjectGroup

    result_items = []
    for d in items:
        # 获取最新版本
        latest_version = db.query(DrawingVersion).filter(
            DrawingVersion.drawing_id == d.id,
            DrawingVersion.is_latest == True
        ).first()

        # 获取产品信息
        product = db.query(Product).filter(Product.id == d.product_id).first()

        # 获取项目组信息
        project_group = None
        if product and product.project_group_id:
            project_group = db.query(ProjectGroup).filter(ProjectGroup.id == product.project_group_id).first()

        # 获取上传人信息
        uploader_name = None
        if latest_version and latest_version.uploader_id:
            uploader = db.query(User).filter(User.id == latest_version.uploader_id).first()
            uploader_name = uploader.name if uploader else None

        # 获取创建人信息
        creator_name = None
        if d.creator_id:
            creator = db.query(User).filter(User.id == d.creator_id).first()
            creator_name = creator.name if creator else None

        result_items.append({
            "id": d.id,
            "drawing_no": d.drawing_no,
            "name": d.name,
            "product_id": d.product_id,
            "product_name": product.name if product else None,
            "project_group_id": product.project_group_id if product else None,
            "project_group_name": project_group.name if project_group else None,
            "project_manager": product.manager if product else None,
            "department_id": d.department_id,
            "confidentiality_level": d.confidentiality_level.value,
            "is_core_part": d.is_core_part,
            "status": d.status.value,
            "review_status": d.review_status.value if d.review_status else "pending",
            "creator_id": d.creator_id,
            "creator_name": creator_name,
            "version_no": latest_version.version_no if latest_version else None,
            "uploader_name": uploader_name,
            "uploaded_at": latest_version.uploaded_at.isoformat() if latest_version and latest_version.uploaded_at else None,
            "purpose": d.purpose,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None
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
async def create_drawing(
    drawing_no: Optional[str] = Form(None),
    name: str = Form(...),
    product_id: str = Form(...),
    department_id: Optional[str] = Form(None),  # 可选，自动从产品获取
    confidentiality_level: str = Form(...),
    is_core_part: bool = Form(False),
    core_part_keywords: str = Form(None),  # 逗号分隔的关键词 ID 列表
    purpose: str = Form(None),
    material: str = Form(None),
    dimensions: str = Form(None),
    secret_points: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("createDrawing"))
):
    """创建图纸"""
    # 获取产品代码以生成图号
    from ..models.product import Product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    # 如果未提供图号，则自动生成
    if not drawing_no:
        drawing_no = generate_drawing_no(product.code, db)

    # 如果未提供 department_id，自动从产品获取
    if not department_id and product.department_id:
        department_id = product.department_id

    drawing = Drawing(
        drawing_no=drawing_no,
        name=name,
        product_id=product_id,
        department_id=department_id,
        confidentiality_level=ConfidentialityLevel(confidentiality_level),
        is_core_part=is_core_part,
        creator_id=current_user.id,
        purpose=purpose,
        material=material,
        dimensions=dimensions,
        secret_points=secret_points
    )

    db.add(drawing)
    db.commit()

    # 关联核心部件关键词
    if core_part_keywords and is_core_part:
        from ..models.core_part import CorePartKeyword
        keyword_ids = [k.strip() for k in core_part_keywords.split(',') if k.strip()]
        keywords = db.query(CorePartKeyword).filter(CorePartKeyword.id.in_(keyword_ids)).all()
        drawing.core_part_keywords.extend(keywords)
        db.commit()

    db.refresh(drawing)

    log_operation(
        user_id=current_user.id,
        action="CREATE_DRAWING",
        resource_type="drawing",
        resource_id=drawing.id,
        description=f"创建图纸：{drawing.drawing_no} - {drawing.name}",
        ip_address="unknown"
    )

    return Response(message="图纸创建成功", data={"id": drawing.id, "drawing_no": drawing_no})


@router.get("/{drawing_id}", response_model=Response)
async def get_drawing(
    drawing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取图纸详情"""
    from ..models.product import Product
    from ..models.project_group import ProjectGroup, project_group_members

    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing or drawing.status == DrawingStatus.DELETED:
        raise HTTPException(status_code=404, detail="图纸不存在")

    # 检查关联产品是否已归档
    if drawing.product_id:
        product = db.query(Product).filter(Product.id == drawing.product_id).first()
        if product and product.status == 'archived':
            raise HTTPException(status_code=404, detail="图纸不存在")

    # 检查用户是否有权限查看该图纸
    has_access = False

    if check_user_permission(current_user, "viewAllDrawings", db):
        # CTO/管理员/审定人可以查看所有图纸
        has_access = True
    elif check_user_permission(current_user, "viewProjectDrawings", db):
        # 项目负责人：检查是否是负责的项目的图纸（通过 Product.manager_id）
        if drawing.product_id:
            product = db.query(Product).filter(Product.id == drawing.product_id).first()
            if product and product.manager_id == current_user.id:
                has_access = True
    elif check_user_permission(current_user, "viewOwnDrawings", db):
        # 工程师/设计师：只能查看自己创建的图纸
        if drawing.creator_id == current_user.id:
            has_access = True

    if not has_access:
        raise HTTPException(status_code=403, detail="您没有权限查看此图纸")

    # 获取产品信息
    from ..models.product import Product
    product = db.query(Product).filter(Product.id == drawing.product_id).first()

    # 获取项目组信息
    project_group = None
    if product and product.project_group_id:
        from ..models.project_group import ProjectGroup
        project_group = db.query(ProjectGroup).filter(ProjectGroup.id == product.project_group_id).first()

    # 获取创建人信息
    creator = db.query(User).filter(User.id == drawing.creator_id).first() if drawing.creator_id else None

    # 获取最新版本信息
    latest_version = db.query(DrawingVersion).filter(
        DrawingVersion.drawing_id == drawing_id,
        DrawingVersion.is_latest == True
    ).first()

    # 获取上传人信息
    uploader = None
    if latest_version and latest_version.uploader_id:
        uploader = db.query(User).filter(User.id == latest_version.uploader_id).first()

    return Response(data={
        "id": drawing.id,
        "drawing_no": drawing.drawing_no,
        "name": drawing.name,
        "product_id": drawing.product_id,
        "product_name": product.name if product else None,
        "project_group_id": product.project_group_id if product else None,
        "project_group_name": project_group.name if project_group else None,
        "project_manager": product.manager if product else None,
        "department_id": drawing.department_id,
        "confidentiality_level": drawing.confidentiality_level.value,
        "is_core_part": drawing.is_core_part,
        "core_part_keywords": [{"id": k.id, "keyword": k.keyword} for k in drawing.core_part_keywords],
        "purpose": drawing.purpose,
        "material": drawing.material,
        "dimensions": drawing.dimensions,
        "secret_points": drawing.secret_points,
        "creator_id": drawing.creator_id,
        "creator_name": creator.name if creator else None,
        "review_status": drawing.review_status.value if drawing.review_status else None,
        "status": drawing.status.value,
        "created_at": drawing.created_at.isoformat() if drawing.created_at else None,
        "updated_at": drawing.updated_at.isoformat() if drawing.updated_at else None,
        "latest_version": {
            "id": latest_version.id if latest_version else None,
            "version_no": latest_version.version_no if latest_version else None,
            "file_name": latest_version.file_name if latest_version else None,
            "file_size": latest_version.file_size if latest_version else None,
            "file_format": latest_version.file_format if latest_version else None,
            "uploader_id": latest_version.uploader_id if latest_version else None,
            "uploader_name": uploader.name if uploader else None,
            "uploaded_at": latest_version.uploaded_at.isoformat() if latest_version and latest_version.uploaded_at else None
        } if latest_version else None
    })


@router.post("/{drawing_id}", response_model=Response)
async def update_drawing(
    drawing_id: str,
    name: Optional[str] = Form(None),
    product_id: Optional[str] = Form(None),
    department_id: Optional[str] = Form(None),
    is_core_part: Optional[bool] = Form(None),
    core_part_keywords: Optional[str] = Form(None),
    purpose: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    dimensions: Optional[str] = Form(None),
    secret_points: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("createDrawing"))
):
    """更新图纸"""
    from ..models.product import Product

    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    # 检查用户是否有权限访问该图纸
    has_access = False
    if check_user_permission(current_user, "viewAllDrawings", db):
        has_access = True
    elif check_user_permission(current_user, "viewProjectDrawings", db):
        if drawing.product_id:
            product = db.query(Product).filter(Product.id == drawing.product_id).first()
            if product and product.manager_id == current_user.id:
                has_access = True
    elif check_user_permission(current_user, "viewOwnDrawings", db):
        if drawing.creator_id == current_user.id:
            has_access = True

    if not has_access:
        raise HTTPException(status_code=403, detail="您没有权限修改此图纸")

    update_data = {
        k: v for k, v in {
            "name": name,
            "product_id": product_id,
            "department_id": department_id,
            "is_core_part": is_core_part,
            "purpose": purpose,
            "material": material,
            "dimensions": dimensions,
            "secret_points": secret_points
        }.items() if v is not None
    }

    for field, value in update_data.items():
        setattr(drawing, field, value)

    # 更新核心部件关键词
    if core_part_keywords is not None:
        from ..models.core_part import CorePartKeyword
        # 清除现有关系
        drawing.core_part_keywords.clear()
        # 添加新的关键词
        keyword_ids = [k.strip() for k in core_part_keywords.split(',') if k.strip()]
        if keyword_ids:
            keywords = db.query(CorePartKeyword).filter(CorePartKeyword.id.in_(keyword_ids)).all()
            drawing.core_part_keywords.extend(keywords)

    db.commit()
    db.refresh(drawing)

    log_operation(
        user_id=current_user.id,
        action="UPDATE_DRAWING",
        resource_type="drawing",
        resource_id=drawing_id,
        description=f"更新图纸：{drawing.drawing_no}",
        ip_address="unknown"
    )

    return Response(message="图纸更新成功")


@router.delete("/{drawing_id}", response_model=Response)
async def delete_drawing(
    drawing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("createDrawing"))
):
    """删除/作废图纸（软删除）"""
    from ..models.product import Product

    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    # 检查用户是否有权限访问该图纸
    has_access = False
    if check_user_permission(current_user, "viewAllDrawings", db):
        has_access = True
    elif check_user_permission(current_user, "viewProjectDrawings", db):
        if drawing.product_id:
            product = db.query(Product).filter(Product.id == drawing.product_id).first()
            if product and product.manager_id == current_user.id:
                has_access = True
    elif check_user_permission(current_user, "viewOwnDrawings", db):
        if drawing.creator_id == current_user.id:
            has_access = True

    if not has_access:
        raise HTTPException(status_code=403, detail="您没有权限作废此图纸")

    drawing.status = DrawingStatus.ARCHIVED
    db.commit()

    log_operation(
        user_id=current_user.id,
        action="DELETE_DRAWING",
        resource_type="drawing",
        resource_id=drawing_id,
        description=f"作废图纸：{drawing.drawing_no}",
        ip_address="unknown"
    )

    return Response(message="图纸已作废")


@router.post("/{drawing_id}/reactivate", response_model=Response)
async def reactivate_drawing(
    drawing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("createDrawing"))
):
    """重新激活已作废的图纸"""
    from ..models.product import Product

    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    # 检查用户是否有权限访问该图纸
    has_access = False
    if check_user_permission(current_user, "viewAllDrawings", db):
        has_access = True
    elif check_user_permission(current_user, "viewProjectDrawings", db):
        if drawing.product_id:
            product = db.query(Product).filter(Product.id == drawing.product_id).first()
            if product and product.manager_id == current_user.id:
                has_access = True
    elif check_user_permission(current_user, "viewOwnDrawings", db):
        if drawing.creator_id == current_user.id:
            has_access = True

    if not has_access:
        raise HTTPException(status_code=403, detail="您没有权限重新激活此图纸")

    drawing.status = DrawingStatus.ACTIVE
    db.commit()

    log_operation(
        user_id=current_user.id,
        action="REACTIVATE_DRAWING",
        resource_type="drawing",
        resource_id=drawing_id,
        description=f"重新激活图纸：{drawing.drawing_no}",
        ip_address="unknown"
    )

    return Response(message="图纸已重新激活")



@router.post("/{drawing_id}/versions", response_model=Response)
async def upload_version(
    drawing_id: str,
    change_types: Optional[str] = Form(None),
    change_reason: Optional[str] = Form(None),
    related_issue: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("uploadVersion"))
):
    """上传新版本"""
    from ..models.product import Product

    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    # 检查用户是否有权限访问该图纸
    has_access = False
    if check_user_permission(current_user, "viewAllDrawings", db):
        has_access = True
    elif check_user_permission(current_user, "viewProjectDrawings", db):
        if drawing.product_id:
            product = db.query(Product).filter(Product.id == drawing.product_id).first()
            if product and product.manager_id == current_user.id:
                has_access = True
    elif check_user_permission(current_user, "viewOwnDrawings", db):
        if drawing.creator_id == current_user.id:
            has_access = True

    if not has_access:
        raise HTTPException(status_code=403, detail="您没有权限上传此图纸的版本")

    # 作废的图纸不能上传新版本
    if drawing.status == DrawingStatus.ARCHIVED:
        raise HTTPException(status_code=400, detail="作废的图纸不能上传新版本，请先重新激活")

    # 检查文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置指针

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 500MB 限制")

    # 生成新版本号
    latest_version = db.query(DrawingVersion).filter(
        DrawingVersion.drawing_id == drawing_id,
        DrawingVersion.is_latest == True
    ).first()

    if latest_version:
        # 解析版本号
        version_str = latest_version.version_no.replace("V", "")
        parts = version_str.split(".")
        try:
            parts[1] = str(int(parts[1]) + 1)
        except (IndexError, ValueError):
            parts = ["1", "1"]
        new_version_no = f"V{'.'.join(parts)}"
    else:
        new_version_no = "V1.0"

    # 将旧版本设为非最新
    if latest_version:
        latest_version.is_latest = False

    # 保存文件
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".dwg"
    storage_path = os.path.join(settings.FILE_STORAGE_PATH, drawing_id, new_version_no)
    os.makedirs(storage_path, exist_ok=True)

    file_path = os.path.join(storage_path, f"drawing{file_ext}")
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # 创建版本记录
    version = DrawingVersion(
        drawing_id=drawing_id,
        version_no=new_version_no,
        file_path=file_path,
        file_name=file.filename or "drawing",
        file_size=file_size,
        file_format=file_ext.lstrip(".").upper(),
        change_types=change_types,
        change_reason=change_reason,
        related_issue=related_issue,
        uploader_id=current_user.id,
        is_latest=True
    )

    db.add(version)
    db.flush()  # 确保 version.id 已生成

    # 将之前的最新版本标记为非最新
    db.query(DrawingVersion).filter(
        DrawingVersion.drawing_id == drawing_id,
        DrawingVersion.is_latest == True,
        DrawingVersion.id != version.id
    ).update({"is_latest": False})

    # 上传新版本后，图纸需要重新审核（将 review_status 重置为 PENDING）
    drawing.review_status = ReviewStatus.PENDING

    db.commit()
    db.refresh(version)

    log_operation(
        user_id=current_user.id,
        action="UPLOAD_VERSION",
        resource_type="drawing_version",
        resource_id=version.id,
        description=f"上传版本：{drawing.drawing_no} - {new_version_no}",
        ip_address="unknown"
    )

    return Response(message="版本上传成功", data={"id": version.id, "version_no": new_version_no})


@router.get("/{drawing_id}/versions", response_model=Response)
async def get_versions(
    drawing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取版本历史"""
    from ..models.product import Product

    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    # 检查用户是否有权限访问该图纸
    has_access = False
    if check_user_permission(current_user, "viewAllDrawings", db):
        has_access = True
    elif check_user_permission(current_user, "viewProjectDrawings", db):
        if drawing.product_id:
            product = db.query(Product).filter(Product.id == drawing.product_id).first()
            if product and product.manager_id == current_user.id:
                has_access = True
    elif check_user_permission(current_user, "viewOwnDrawings", db):
        if drawing.creator_id == current_user.id:
            has_access = True

    if not has_access:
        raise HTTPException(status_code=403, detail="您没有权限查看此图纸版本")

    # 修正 is_latest 标志：确保每个图纸只有一个最新版本
    latest_version = db.query(DrawingVersion).filter(
        DrawingVersion.drawing_id == drawing_id
    ).order_by(DrawingVersion.uploaded_at.desc()).first()

    if latest_version:
        # 将所有版本设为非最新，然后只把最新的设为最新
        db.query(DrawingVersion).filter(
            DrawingVersion.drawing_id == drawing_id
        ).update({"is_latest": False})
        latest_version.is_latest = True
        db.commit()

    versions = db.query(DrawingVersion).filter(
        DrawingVersion.drawing_id == drawing_id
    ).order_by(DrawingVersion.uploaded_at.desc()).all()

    # 获取上传人名字
    uploader_ids = set(v.uploader_id for v in versions if v.uploader_id)
    uploaders = {u.id: u.name for u in db.query(User).filter(User.id.in_(uploader_ids)).all()} if uploader_ids else {}

    return Response(data=[{
        "id": v.id,
        "version_no": v.version_no,
        "file_name": v.file_name,
        "file_size": v.file_size,
        "file_format": v.file_format,
        "change_types": v.change_types,
        "change_reason": v.change_reason,
        "related_issue": v.related_issue,
        "uploader_id": v.uploader_id,
        "uploader_name": uploaders.get(v.uploader_id) if v.uploader_id else None,
        "uploaded_at": v.uploaded_at,
        "is_latest": v.is_latest
    } for v in versions])


@router.get("/{drawing_id}/download", response_model=Response)
async def download_drawing(
    drawing_id: str,
    version_id: Optional[str] = Query(None, description="指定版本ID，不指定则下载最新版本"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载图纸文件（有权限的用户可下载）"""
    from ..models.product import Product
    from ..models.project_group import ProjectGroup, project_group_members

    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing or drawing.status == DrawingStatus.DELETED:
        raise HTTPException(status_code=404, detail="图纸不存在")

    # 检查关联产品是否已归档
    if drawing.product_id:
        product = db.query(Product).filter(Product.id == drawing.product_id).first()
        if product and product.status == 'archived':
            raise HTTPException(status_code=404, detail="图纸不存在")

    # 检查用户是否有权限访问该图纸
    has_access = False

    if check_user_permission(current_user, "viewAllDrawings", db):
        # CTO/管理员/审定人可以下载所有图纸
        has_access = True
    elif check_user_permission(current_user, "viewProjectDrawings", db):
        # 项目负责人：检查是否是负责的项目的图纸（通过 Product.manager_id）
        if drawing.product_id:
            product = db.query(Product).filter(Product.id == drawing.product_id).first()
            if product and product.manager_id == current_user.id:
                has_access = True
    elif check_user_permission(current_user, "viewOwnDrawings", db):
        # 工程师/设计师：只能下载自己创建的图纸
        if drawing.creator_id == current_user.id:
            has_access = True

    if not has_access:
        raise HTTPException(status_code=403, detail="您没有权限下载此图纸")

    # 获取指定版本或最新版本
    if version_id:
        version = db.query(DrawingVersion).filter(
            DrawingVersion.id == version_id,
            DrawingVersion.drawing_id == drawing_id
        ).first()
        if not version:
            raise HTTPException(status_code=404, detail="指定版本不存在")
    else:
        version = db.query(DrawingVersion).filter(
            DrawingVersion.drawing_id == drawing_id,
            DrawingVersion.is_latest == True
        ).first()

    if not version:
        raise HTTPException(status_code=404, detail="图纸文件不存在")

    # 解析文件真实路径
    file_path = version.file_path
    if file_path.startswith('./'):
        file_path = file_path[2:]

    # 计算可能的路径：1) 相对于 backend 目录 2) 相对于项目根目录
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    possible_paths = [
        os.path.join(backend_dir, file_path),  # backend/data/drawings/...
        os.path.join(backend_dir, 'data', 'drawings', file_path.lstrip('data/drawings/') if file_path.startswith('data/drawings/') else file_path),  # 项目根目录
    ]

    # 如果路径已经是绝对路径
    if os.path.isabs(version.file_path):
        possible_paths = [version.file_path]

    # 查找实际存在的文件
    actual_path = None
    for p in possible_paths:
        if os.path.exists(p):
            actual_path = p
            break

    if not actual_path:
        raise HTTPException(status_code=404, detail="图纸文件已丢失")

    # 记录下载日志
    log_operation(
        user_id=current_user.id,
        action="DOWNLOAD_DRAWING",
        resource_type="drawing",
        resource_id=drawing_id,
        description=f"下载图纸：{drawing.drawing_no}",
        ip_address="unknown"
    )

    # 返回文件
    from fastapi.responses import FileResponse
    return FileResponse(
        actual_path,
        filename=f"{drawing.drawing_no}_{version.version_no}.{version.file_format.lower()}",
        media_type='application/octet-stream'
    )


@router.get("/export/csv", response_model=Response)
async def export_drawings_csv(
    keyword: Optional[str] = None,
    product_id: Optional[str] = None,
    project_group_id: Optional[str] = None,
    manager_id: Optional[str] = None,
    uploader_id: Optional[str] = None,
    department_id: Optional[str] = None,
    confidentiality_level: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("viewAllDrawings"))
):
    """导出图纸数据为 CSV（需要 viewAllDrawings 权限）"""
    from ..models.product import Product
    from ..models.project_group import ProjectGroup, project_group_members

    # 基础查询
    query = db.query(Drawing).filter(Drawing.status != DrawingStatus.DELETED)

    # 根据动态权限过滤
    if check_user_permission(current_user, "viewAllDrawings", db):
        # CTO/管理员/审定人可以导出所有图纸
        pass
    elif check_user_permission(current_user, "viewProjectDrawings", db):
        # 项目负责人导出其负责项目内的所有图纸（通过 Product.manager_id）
        product_ids = db.query(Product.id).filter(
            Product.manager_id == current_user.id
        ).all()

        if product_ids:
            query = query.filter(Drawing.product_id.in_([p.id for p in product_ids]))
        else:
            query = query.filter(Drawing.id == None)
    elif check_user_permission(current_user, "viewOwnDrawings", db):
        # 工程师/设计师只能导出自己创建的图纸
        query = query.filter(Drawing.creator_id == current_user.id)
    else:
        # 访客等无权限，无法导出任何图纸
        query = query.filter(Drawing.id == None)

    # 筛选条件
    if keyword:
        query = query.filter(
            (Drawing.drawing_no.contains(keyword)) | (Drawing.name.contains(keyword))
        )
    if product_id:
        query = query.filter(Drawing.product_id == product_id)
    if project_group_id:
        query = query.join(Product).filter(Product.project_group_id == project_group_id)
    if manager_id:
        query = query.join(Product).filter(Product.manager_id == manager_id)
    if uploader_id:
        query = query.join(DrawingVersion).filter(
            DrawingVersion.is_latest == True,
            DrawingVersion.uploader_id == uploader_id
        )
    if department_id:
        query = query.filter(Drawing.department_id == department_id)
    if confidentiality_level:
        query = query.filter(Drawing.confidentiality_level == confidentiality_level)
    if status:
        query = query.filter(Drawing.status == status)

    drawings = query.order_by(Drawing.created_at.desc()).all()

    # 生成 CSV
    output = io.StringIO()
    fieldnames = ['图号', '名称', '所属产品', '所属项目组', '项目负责人', '保密等级', '是否核心部件',
                  '用途', '材料', '尺寸', '审定状态', '上传人', '上传日期', '创建人', '创建日期']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for d in drawings:
        # 获取最新版本
        latest_version = db.query(DrawingVersion).filter(
            DrawingVersion.drawing_id == d.id,
            DrawingVersion.is_latest == True
        ).first()

        # 获取产品信息
        product = db.query(Product).filter(Product.id == d.product_id).first()

        # 获取项目组信息
        project_group = None
        if product and product.project_group_id:
            project_group = db.query(ProjectGroup).filter(ProjectGroup.id == product.project_group_id).first()

        # 获取上传人信息
        uploader_name = None
        if latest_version and latest_version.uploader_id:
            uploader = db.query(User).filter(User.id == latest_version.uploader_id).first()
            uploader_name = uploader.name if uploader else None

        # 获取创建人信息
        creator = db.query(User).filter(User.id == d.creator_id).first()

        writer.writerow({
            '图号': d.drawing_no,
            '名称': d.name,
            '所属产品': product.name if product else '',
            '所属项目组': project_group.name if project_group else '',
            '项目负责人': product.manager if product else '',
            '保密等级': d.confidentiality_level.value,
            '是否核心部件': '是' if d.is_core_part else '否',
            '用途': d.purpose or '',
            '材料': d.material or '',
            '尺寸': d.dimensions or '',
            '审定状态': d.review_status.value if d.review_status else 'pending',
            '上传人': uploader_name or '',
            '上传日期': latest_version.uploaded_at.strftime('%Y-%m-%d %H:%M') if latest_version and latest_version.uploaded_at else '',
            '创建人': creator.name if creator else '',
            '创建日期': d.created_at.strftime('%Y-%m-%d') if d.created_at else ''
        })

    output.seek(0)

    return Response(
        message="导出成功",
        data={
            "filename": "drawings_export.csv",
            "content": output.getvalue(),
            "count": len(drawings)
        }
    )


@router.get("/export/backup")
async def export_full_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageUsers"))
):
    """管理员全量备份：导出所有系统数据和图纸版本文件"""
    from ..models.product import Product
    from ..models.project_group import ProjectGroup
    from ..models.user import User
    from ..models.role import Role
    from ..models.department import Department

    # 获取系统数据
    users_data = db.query(User).all()
    roles_data = db.query(Role).all()
    departments_data = db.query(Department).all()
    products_data = db.query(Product).all()
    project_groups_data = db.query(ProjectGroup).all()

    # 获取所有图纸（不筛选权限，因为是 admin）
    drawings_data = db.query(Drawing).all()

    # 获取所有版本文件
    all_versions = db.query(DrawingVersion).all()

    # 准备内存 ZIP
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 1. 写入 manifest.csv
        manifest = f"备份时间,总用户数,总角色数,总部门数,总产品数,总项目组数,总图纸数,总版本文件数\n"
        manifest += f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{len(users_data)},{len(roles_data)},{len(departments_data)},{len(products_data)},{len(project_groups_data)},{len(drawings_data)},{len(all_versions)}\n"
        zip_file.writestr("manifest.csv", manifest)

        # 2. 写入 summary.txt
        summary = f"=== 全量备份统计 ===\n"
        summary += f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary += f"用户数: {len(users_data)}\n"
        summary += f"角色数: {len(roles_data)}\n"
        summary += f"部门数: {len(departments_data)}\n"
        summary += f"产品数: {len(products_data)}\n"
        summary += f"项目组数: {len(project_groups_data)}\n"
        summary += f"图纸数: {len(drawings_data)}\n"
        summary += f"版本文件数: {len(all_versions)}\n"
        zip_file.writestr("summary.txt", summary)

        # 3. 写入 system_data/*.csv
        # users.csv
        if users_data:
            user_csv = io.StringIO()
            writer = csv.writer(user_csv)
            writer.writerow(['id', 'username', 'name', 'email', 'phone', 'role_id', 'department_id', 'status'])
            for u in users_data:
                writer.writerow([u.id, u.username, u.name, u.email or '', u.phone or '', u.role_id or '', u.department_id or '', u.status])
            zip_file.writestr("system_data/users.csv", user_csv.getvalue())

        # roles.csv
        if roles_data:
            roles_csv = io.StringIO()
            writer = csv.writer(roles_csv)
            writer.writerow(['id', 'name', 'code', 'description'])
            for r in roles_data:
                writer.writerow([r.id, r.name, r.code, getattr(r, 'description', '')])
            zip_file.writestr("system_data/roles.csv", roles_csv.getvalue())

        # departments.csv
        if departments_data:
            dept_csv = io.StringIO()
            writer = csv.writer(dept_csv)
            writer.writerow(['id', 'name', 'code'])
            for d in departments_data:
                writer.writerow([d.id, d.name, getattr(d, 'code', '')])
            zip_file.writestr("system_data/departments.csv", dept_csv.getvalue())

        # products.csv
        if products_data:
            prod_csv = io.StringIO()
            writer = csv.writer(prod_csv)
            writer.writerow(['id', 'name', 'code', 'status', 'project_group_id', 'manager', 'manager_id', 'start_date'])
            for p in products_data:
                writer.writerow([p.id, p.name, p.code, p.status, p.project_group_id or '', p.manager or '', p.manager_id or '', p.start_date.strftime('%Y-%m-%d') if p.start_date else ''])
            zip_file.writestr("system_data/products.csv", prod_csv.getvalue())

        # project_groups.csv
        if project_groups_data:
            pg_csv = io.StringIO()
            writer = csv.writer(pg_csv)
            writer.writerow(['id', 'name', 'code', 'description', 'status'])
            for pg in project_groups_data:
                writer.writerow([pg.id, pg.name, getattr(pg, 'code', ''), getattr(pg, 'description', ''), getattr(pg, 'status', '')])
            zip_file.writestr("system_data/project_groups.csv", pg_csv.getvalue())

        # 4. 写入 drawings/drawings.csv
        if drawings_data:
            drawings_csv = io.StringIO()
            writer = csv.writer(drawings_csv)
            writer.writerow(['id', 'drawing_no', 'name', 'product_id', 'department_id', 'confidentiality_level',
                             'is_core_part', 'status', 'review_status', 'creator_id', 'purpose',
                             'material', 'dimensions', 'secret_points', 'created_at', 'updated_at'])
            for d in drawings_data:
                writer.writerow([
                    d.id, d.drawing_no, d.name, d.product_id or '', d.department_id or '',
                    d.confidentiality_level.value if d.confidentiality_level else '',
                    '是' if d.is_core_part else '否', d.status.value if d.status else '',
                    d.review_status.value if d.review_status else '', d.creator_id or '',
                    d.purpose or '', d.material or '', d.dimensions or '', d.secret_points or '',
                    d.created_at.strftime('%Y-%m-%d %H:%M:%S') if d.created_at else '',
                    d.updated_at.strftime('%Y-%m-%d %H:%M:%S') if d.updated_at else ''
                ])
            zip_file.writestr("drawings/drawings.csv", drawings_csv.getvalue())

        # 5. 写入 drawings/versions.csv（包含版本变更说明）
        if all_versions:
            versions_csv = io.StringIO()
            writer = csv.writer(versions_csv)
            writer.writerow(['drawing_id', 'drawing_no', 'version_no', 'file_name', 'file_size', 'file_format',
                             'change_types', 'change_reason', 'uploader_id', 'uploaded_at', 'is_latest', 'file_path'])
            for v in all_versions:
                # 获取图纸号
                drawing_no = ''
                for d in drawings_data:
                    if d.id == v.drawing_id:
                        drawing_no = d.drawing_no
                        break
                writer.writerow([
                    v.drawing_id, drawing_no, v.version_no, v.file_name or '', v.file_size or '',
                    v.file_format or '', v.change_types or '', v.change_reason or '',
                    v.uploader_id or '', v.uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if v.uploaded_at else '',
                    '是' if v.is_latest else '否', v.file_path or ''
                ])
            zip_file.writestr("drawings/versions.csv", versions_csv.getvalue())

        # 6. 复制版本文件到 ZIP
        # 计算本地路径
        # FILE_STORAGE_PATH 是 ./data/drawings（相对于 backend/ 目录）
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # .../backend/
        file_storage_base = os.path.abspath(os.path.join(backend_dir, settings.FILE_STORAGE_PATH.lstrip('./')))

        for version in all_versions:
            if not version.file_path:
                continue

            # 确定文件真实路径
            file_path = version.file_path
            # 标准化路径：去除 ./ 前缀
            if file_path.startswith('./'):
                file_path = file_path[2:]

            # 如果是绝对路径，直接使用
            if os.path.isabs(file_path):
                full_path = file_path
            else:
                # 相对路径，基于 file_storage_base
                # 如果 file_path 已经包含 data/drawings 前缀，需要去除
                if file_path.startswith("data/drawings/"):
                    relative_path = file_path[len("data/drawings/"):]
                    full_path = os.path.join(file_storage_base, relative_path)
                else:
                    full_path = os.path.join(file_storage_base, file_path)

            if os.path.exists(full_path):
                # 计算在 ZIP 中的路径: drawings/files/{drawing_no}/{version_no}/{filename}
                filename = os.path.basename(full_path)
                # 获取图纸号作为目录名
                drawing_no = ''
                for d in drawings_data:
                    if d.id == version.drawing_id:
                        drawing_no = d.drawing_no
                        break
                if not drawing_no:
                    drawing_no = version.drawing_id
                arcname = f"drawings/files/{drawing_no}/{version.version_no}/{filename}"
                zip_file.write(full_path, arcname)

    # 准备响应
    zip_buffer.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"full_backup_{timestamp}.zip"

    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
