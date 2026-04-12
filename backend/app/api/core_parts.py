from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
import csv
import io
from fastapi.responses import StreamingResponse
from ..core.database import get_db
from ..models.user import User
from ..models.core_part import CorePartKeyword
from ..schemas import Response, PageResponse
from .deps import get_current_user, require_permission
from ..core.logger import log_operation

router = APIRouter(prefix="/core-parts", tags=["核心部件词库"])


@router.get("", response_model=Response)
async def get_core_parts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取核心部件词库列表（任何登录用户都可查看）"""
    query = db.query(CorePartKeyword)

    if keyword:
        query = query.filter(CorePartKeyword.keyword.contains(keyword))

    total = query.count()
    items = query.order_by(CorePartKeyword.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return Response(
        data=PageResponse(
            items=[{
                "id": item.id,
                "keyword": item.keyword,
                "created_at": item.created_at
            } for item in items],
            total=total,
            page=page,
            size=size
        )
    )


@router.post("", response_model=Response)
async def create_core_part(
    keyword: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageCoreParts"))
):
    """添加核心部件关键词"""
    existing = db.query(CorePartKeyword).filter(CorePartKeyword.keyword == keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail="关键词已存在")

    item = CorePartKeyword(keyword=keyword)
    db.add(item)
    db.commit()
    db.refresh(item)

    log_operation(
        user_id=current_user.id,
        action="CREATE_CORE_PART",
        resource_type="core_part",
        resource_id=item.id,
        description=f"添加核心部件关键词：{keyword}",
        ip_address="unknown"
    )

    return Response(message="关键词添加成功", data={"id": item.id})


@router.get("/export")
async def export_keywords(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageCoreParts"))
):
    """导出核心部件关键词为 CSV"""
    keywords = db.query(CorePartKeyword).order_by(CorePartKeyword.created_at.desc()).all()

    output = io.StringIO()
    # 写入 UTF-8 BOM，让 Excel 正确识别中文
    output.write('\ufeff')
    fieldnames = ['keyword', 'created_at']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for kw in keywords:
        writer.writerow({
            'keyword': kw.keyword,
            'created_at': kw.created_at.strftime('%Y-%m-%d %H:%M:%S') if kw.created_at else ''
        })

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=core_parts_keywords.csv"
        }
    )


@router.post("/import")
async def import_keywords(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageCoreParts"))
):
    """批量导入核心部件关键词（合并模式，不覆盖）"""
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="仅支持 CSV 格式文件")

    content = await file.read()
    try:
        # 尝试多种编码
        try:
            decoded = content.decode('utf-8-sig')  # UTF-8 BOM
        except:
            decoded = content.decode('gbk')  # 中文 Windows 常用
    except:
        raise HTTPException(status_code=400, detail="文件编码不支持，请使用 UTF-8 或 GBK 编码的 CSV")

    reader = csv.DictReader(io.StringIO(decoded))
    success_count = 0
    skipped_count = 0

    for row in reader:
        keyword = row.get('keyword', '').strip()
        if not keyword:
            skipped_count += 1
            continue

        # 检查是否已存在
        existing = db.query(CorePartKeyword).filter(
            CorePartKeyword.keyword == keyword
        ).first()
        if existing:
            skipped_count += 1
            continue

        # 创建新关键词
        item = CorePartKeyword(keyword=keyword)
        db.add(item)
        success_count += 1

    db.commit()

    log_operation(
        user_id=current_user.id,
        action="IMPORT_CORE_PARTS",
        resource_type="core_part",
        resource_id="bulk",
        description=f"批量导入关键词：成功{success_count}条，跳过{skipped_count}条",
        ip_address="unknown"
    )

    return Response(message="导入完成", data={
        "success_count": success_count,
        "skipped_count": skipped_count
    })


@router.delete("/{part_id}", response_model=Response)
async def delete_core_part(
    part_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manageCoreParts"))
):
    """删除核心部件关键词"""
    item = db.query(CorePartKeyword).filter(CorePartKeyword.id == part_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="关键词不存在")

    db.delete(item)
    db.commit()

    log_operation(
        user_id=current_user.id,
        action="DELETE_CORE_PART",
        resource_type="core_part",
        resource_id=part_id,
        description=f"删除核心部件关键词：{item.keyword}",
        ip_address="unknown"
    )

    return Response(message="关键词已删除")
