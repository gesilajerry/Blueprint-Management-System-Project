from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import uuid
from ..core.database import get_db
from ..models.user import User
from ..models.drawing import Drawing, ConfidentialityLevel, ReviewStatus, DrawingVersion
from ..schemas import Response
from .deps import get_current_user, require_permission, get_user_role_code
from ..core.logger import log_operation

router = APIRouter(prefix="/reviews", tags=["保密审核"])


@router.get("/pending", response_model=Response)
async def get_pending_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reviewConfidentiality"))
):
    drawings = db.query(Drawing).filter(
        Drawing.review_status == ReviewStatus.PENDING
    ).all()

    from ..models.product import Product
    from ..models.department import Department

    result = []
    for d in drawings:
        product = db.query(Product).filter(Product.id == d.product_id).first()
        department = db.query(Department).filter(Department.id == d.department_id).first()
        creator = db.query(User).filter(User.id == d.creator_id).first()
        latest_version = db.query(DrawingVersion).filter(
            DrawingVersion.drawing_id == d.id,
            DrawingVersion.is_latest == True
        ).first()

        result.append({
            "id": d.id,
            "drawing_no": d.drawing_no,
            "name": d.name,
            "product_name": product.name if product else "未知",
            "department_name": department.name if department else "未知",
            "creator_name": creator.name if creator else "未知",
            "confidentiality_level": d.confidentiality_level.value,
            "is_core_part": d.is_core_part,
            "version_no": latest_version.version_no if latest_version else "V1.0",
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "purpose": d.purpose,
            "material": d.material,
            "dimensions": d.dimensions,
            "secret_points": d.secret_points
        })

    return Response(data=result)


@router.get("/history/all", response_model=Response)
async def get_all_review_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reviewConfidentiality"))
):
    try:
        # 获取总数
        total_result = db.execute(
            text("SELECT COUNT(*) FROM review_history")
        ).scalar()

        # 获取分页数据
        offset_val = (page - 1) * size
        result = db.execute(
            text("""
                SELECT rh.id, rh.drawing_id, rh.old_level, rh.new_level, rh.reason,
                       rh.reviewer_id, rh.reviewer_name, rh.created_at,
                       d.drawing_no, d.name as drawing_name
                FROM review_history rh
                JOIN drawings d ON rh.drawing_id = d.id
                ORDER BY rh.created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"limit": size, "offset": offset_val}
        ).fetchall()

        history = []
        for row in result:
            # created_at 可能是字符串或 datetime 对象
            created_at = row[7]
            if created_at is None:
                created_at_str = None
            elif isinstance(created_at, str):
                created_at_str = created_at
            else:
                created_at_str = created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)

            history.append({
                "id": row[0],
                "drawing_id": row[1],
                "old_level": row[2],
                "new_level": row[3],
                "reason": row[4],
                "reviewer_id": row[5],
                "reviewer_name": row[6],
                "created_at": created_at_str,
                "drawing_no": row[8],
                "drawing_name": row[9]
            })

        return Response(data={
            "items": history,
            "total": total_result,
            "page": page,
            "size": size
        })
    except Exception as e:
        print(f"Error in get_all_review_history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{drawing_id}/history", response_model=Response)
async def get_review_history(
    drawing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reviewConfidentiality"))
):
    result = db.execute(
        text("SELECT * FROM review_history WHERE drawing_id = :drawing_id ORDER BY created_at DESC"),
        {"drawing_id": drawing_id}
    ).fetchall()

    history = []
    for row in result:
        created_at = row[7]
        if created_at is None:
            created_at_str = None
        elif isinstance(created_at, str):
            created_at_str = created_at
        else:
            created_at_str = created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)

        history.append({
            "id": row[0],
            "drawing_id": row[1],
            "old_level": row[2],
            "new_level": row[3],
            "reason": row[4],
            "reviewer_id": row[5],
            "reviewer_name": row[6],
            "created_at": created_at_str
        })

    return Response(data=history)


@router.post("/{drawing_id}/approve", response_model=Response)
async def approve_review(
    drawing_id: str,
    final_level: str = Form(...),
    reason: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reviewConfidentiality"))
):
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    old_level = drawing.confidentiality_level.value
    drawing.confidentiality_level = ConfidentialityLevel(final_level)
    drawing.review_status = ReviewStatus.APPROVED

    history_id = str(uuid.uuid4())
    db.execute(
        text("INSERT INTO review_history (id, drawing_id, old_level, new_level, reason, reviewer_id, reviewer_name, created_at) VALUES (:id, :drawing_id, :old_level, :new_level, :reason, :reviewer_id, :reviewer_name, :created_at)"),
        {
            "id": history_id,
            "drawing_id": drawing_id,
            "old_level": old_level,
            "new_level": final_level,
            "reason": reason or "无",
            "reviewer_id": current_user.id,
            "reviewer_name": current_user.name,
            "created_at": datetime.utcnow()
        }
    )

    db.commit()

    log_operation(
        user_id=current_user.id,
        action="APPROVE_REVIEW",
        resource_type="drawing",
        resource_id=drawing_id,
        description="审核通过: %s - %s" % (drawing.drawing_no, drawing.name),
        ip_address="unknown"
    )

    return Response(message="审核通过", data={
        "drawing_id": drawing_id,
        "old_level": old_level,
        "new_level": final_level
    })


@router.post("/{drawing_id}/reject", response_model=Response)
async def reject_review(
    drawing_id: str,
    reason: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reviewConfidentiality"))
):
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    drawing.review_status = ReviewStatus.REJECTED

    log_operation(
        user_id=current_user.id,
        action="REJECT_REVIEW",
        resource_type="drawing",
        resource_id=drawing_id,
        description="审核驳回: %s" % drawing.drawing_no,
        ip_address="unknown"
    )

    return Response(message="审核已驳回")
