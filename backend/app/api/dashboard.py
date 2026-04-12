from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from ..core.database import get_db
from ..models.user import User
from ..models.drawing import Drawing, DrawingVersion, DrawingStatus, ConfidentialityLevel, ReviewStatus
from ..models.product import Product
from ..schemas import Response
from .deps import get_current_user, require_permission

router = APIRouter(prefix="/dashboard", tags=["统计看板"])


@router.get("/stats", response_model=Response)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("viewDashboard"))
):
    """获取看板统计数据（所有用户可见全部数据）"""

    now = datetime.utcnow()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 图纸总量（排除已删除的）
    total_drawings = db.query(Drawing).filter(
        Drawing.status != DrawingStatus.DELETED
    ).count()

    # 各级别数量
    level_a = db.query(Drawing).filter(
        Drawing.status != DrawingStatus.DELETED,
        Drawing.confidentiality_level == ConfidentialityLevel.A
    ).count()

    level_b = db.query(Drawing).filter(
        Drawing.status != DrawingStatus.DELETED,
        Drawing.confidentiality_level == ConfidentialityLevel.B
    ).count()

    level_c = db.query(Drawing).filter(
        Drawing.status != DrawingStatus.DELETED,
        Drawing.confidentiality_level == ConfidentialityLevel.C
    ).count()

    # 待审核图纸数量
    pending_reviews = db.query(Drawing).filter(
        Drawing.status != DrawingStatus.DELETED,
        Drawing.review_status == ReviewStatus.PENDING
    ).count()

    # 本月新增图纸
    this_month_new = db.query(Drawing).filter(
        Drawing.status != DrawingStatus.DELETED,
        Drawing.created_at >= this_month_start
    ).count()

    # 本月版本更新数量
    this_month_versions = db.query(DrawingVersion).join(
        Drawing, DrawingVersion.drawing_id == Drawing.id
    ).filter(
        Drawing.status != DrawingStatus.DELETED,
        DrawingVersion.uploaded_at >= this_month_start
    ).count()

    return Response(data={
        "totalDrawings": total_drawings,
        "levelA": level_a,
        "levelB": level_b,
        "levelC": level_c,
        "pendingReviews": pending_reviews,
        "thisMonthNew": this_month_new,
        "thisMonthVersions": this_month_versions
    })


@router.get("/product-stats", response_model=Response)
async def get_product_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取各产品图纸统计（不过滤权限，显示全部数据）"""
    # 获取所有产品及其图纸统计
    products = db.query(Product).filter(Product.status == "active").all()

    result = []
    for product in products:
        drawings_query = db.query(Drawing).filter(
            Drawing.product_id == product.id,
            Drawing.status != DrawingStatus.DELETED
        )

        total = drawings_query.count()
        level_a = drawings_query.filter(Drawing.confidentiality_level == "A").count()
        level_b = drawings_query.filter(Drawing.confidentiality_level == "B").count()
        level_c = drawings_query.filter(Drawing.confidentiality_level == "C").count()

        # 获取最新版本日期
        latest_version = db.query(DrawingVersion).filter(
            DrawingVersion.drawing_id.in_(
                db.query(Drawing.id).filter(
                    Drawing.product_id == product.id,
                    Drawing.status != DrawingStatus.DELETED
                )
            )
        ).order_by(DrawingVersion.uploaded_at.desc()).first()

        result.append({
            "id": product.id,
            "code": product.code,
            "name": product.name,
            "total": total,
            "levelA": level_a,
            "levelB": level_b,
            "levelC": level_c,
            "latestVersion": latest_version.uploaded_at.strftime("%Y-%m-%d") if latest_version and latest_version.uploaded_at else None
        })

    return Response(data=result)


@router.get("/weekly-trend", response_model=Response)
async def get_weekly_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取近7天图纸上传趋势（不过滤权限，显示全部数据）"""
    from ..models.product import Product

    now = datetime.utcnow()
    days = []
    products = db.query(Product).filter(Product.status == "active").all()

    # 获取近7天的日期范围
    date_range = []
    for i in range(6, -1, -1):
        d = now - timedelta(days=i)
        date_range.append({
            "date": d.strftime("%Y-%m-%d"),
            "label": d.strftime("%m-%d"),
            "weekday": ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.weekday()]
        })

    # 构建每天每个项目的上传统计
    result = []
    for day_info in date_range:
        day_start = datetime.strptime(day_info["date"], "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)

        day_data = {
            "date": day_info["date"],
            "label": day_info["label"],
            "weekday": day_info["weekday"],
            "total": 0,
            "byProduct": []
        }

        for product in products:
            # 统计该产品在该日期的版本数量
            count = db.query(DrawingVersion).join(
                Drawing, DrawingVersion.drawing_id == Drawing.id
            ).filter(
                Drawing.product_id == product.id,
                Drawing.status != DrawingStatus.DELETED,
                DrawingVersion.uploaded_at >= day_start,
                DrawingVersion.uploaded_at <= day_end
            ).count()

            if count > 0:
                day_data["byProduct"].append({
                    "productId": product.id,
                    "productName": product.name,
                    "count": count
                })
            day_data["total"] += count

        result.append(day_data)

    # 计算百分比用于显示
    max_total = max(day["total"] for day in result) if result else 1
    for day in result:
        day["percentage"] = max(20, round((day["total"] / max_total) * 100)) if max_total > 0 else 20

    return Response(data=result)


@router.get("/recent-uploads", response_model=Response)
async def get_recent_uploads(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取最近上传记录（不过滤权限，显示全部数据）"""
    versions = db.query(DrawingVersion, Drawing).join(
        Drawing, DrawingVersion.drawing_id == Drawing.id
    ).filter(
        Drawing.status != DrawingStatus.DELETED
    ).order_by(
        DrawingVersion.uploaded_at.desc()
    ).limit(limit).all()

    result = []
    for version, drawing in versions:
        result.append({
            "drawing_no": drawing.drawing_no,
            "name": drawing.name,
            "version": version.version_no,
            "created_at": version.uploaded_at.isoformat() if version.uploaded_at else None
        })

    return Response(data=result)
