from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, date
from typing import Optional
from ..core.database import get_db
from ..models.user import User
from ..models.drawing import Drawing, DrawingVersion, DrawingStatus, ReviewStatus
from ..schemas import Response
from .deps import get_current_user, require_permission

router = APIRouter(prefix="/workload", tags=["工作量统计"])


@router.get("/stats", response_model=Response)
async def get_workload_stats(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("viewDashboard"))
):
    """获取工作量统计（所有用户可见全部数据）"""

    # 计算日期范围
    now = datetime.utcnow()
    if start_date and end_date:
        # 使用前端传递的日期范围
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            end_dt = end_dt.replace(hour=23, minute=59, second=59)  # 包含结束当天
        except ValueError:
            start_dt = now - timedelta(days=30)
            end_dt = now
    else:
        # 默认近30天
        start_dt = now - timedelta(days=30)
        end_dt = now

    # 获取所有活跃用户
    users = db.query(User).filter(User.status == "active").all()

    result = []
    for user in users:
        # 统计该用户创建的图纸数量
        created_drawings = db.query(Drawing).filter(
            Drawing.creator_id == user.id,
            Drawing.created_at >= start_dt,
            Drawing.created_at <= end_dt
        ).count()

        # 统计该用户上传的版本数量
        uploaded_versions = db.query(DrawingVersion).filter(
            DrawingVersion.uploader_id == user.id,
            DrawingVersion.uploaded_at >= start_dt,
            DrawingVersion.uploaded_at <= end_dt
        ).count()

        # 统计该用户审定的图纸数量
        from sqlalchemy import text
        reviewed_count = db.execute(
            text("""
                SELECT COUNT(*) FROM review_history
                WHERE reviewer_id = :user_id
                AND created_at >= :since
                AND created_at <= :end
            """),
            {"user_id": user.id, "since": start_dt, "end": end_dt}
        ).scalar() or 0

        result.append({
            "user_id": user.id,
            "user_name": user.name,
            "username": user.username,
            "role_id": user.role_id,
            "drawings_created": created_drawings,
            "versions_uploaded": uploaded_versions,
            "drawings_reviewed": reviewed_count,
            "total_contributions": created_drawings + uploaded_versions + reviewed_count
        })

    # 按总贡献排序
    result.sort(key=lambda x: x["total_contributions"], reverse=True)

    return Response(data=result)


@router.get("/summary", response_model=Response)
async def get_workload_summary(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("viewDashboard"))
):
    """获取工作量汇总统计（所有用户可见全部数据）"""

    # 计算日期范围
    now = datetime.utcnow()
    if start_date and end_date:
        # 使用前端传递的日期范围
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        except ValueError:
            start_dt = now - timedelta(days=30)
            end_dt = now
    else:
        # 默认近30天
        start_dt = now - timedelta(days=30)
        end_dt = now

    # 总上传版本数
    total_versions = db.query(DrawingVersion).filter(
        DrawingVersion.uploaded_at >= start_dt,
        DrawingVersion.uploaded_at <= end_dt
    ).count()

    # 总创建图纸数
    total_drawings = db.query(Drawing).filter(
        Drawing.created_at >= start_dt,
        Drawing.created_at <= end_dt
    ).count()

    # 总审核数
    from sqlalchemy import text
    total_reviews = db.execute(
        text("""
            SELECT COUNT(*) FROM review_history
            WHERE created_at >= :since
            AND created_at <= :end
        """),
        {"since": start_dt, "end": end_dt}
    ).scalar() or 0

    # 今日活跃用户数
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    active_users_today = db.query(DrawingVersion.uploader_id).filter(
        DrawingVersion.uploaded_at >= today_start
    ).distinct().count()

    return Response(data={
        "total_versions": total_versions,
        "total_drawings": total_drawings,
        "total_reviews": total_reviews,
        "active_users_today": active_users_today,
        "start_date": start_date,
        "end_date": end_date
    })
