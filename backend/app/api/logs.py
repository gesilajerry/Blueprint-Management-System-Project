from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..core.database import get_db
from ..models.user import User
from ..models.system_log import SystemLog
from ..schemas import Response, PageResponse
from .deps import get_current_user, require_permission

router = APIRouter(prefix="/logs", tags=["系统日志"])


@router.get("", response_model=Response)
async def get_logs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("viewLogs"))
):
    """获取系统日志列表"""
    query = db.query(SystemLog)

    if user_id:
        query = query.filter(SystemLog.user_id == user_id)
    if action:
        query = query.filter(SystemLog.action == action)
    if resource_type:
        query = query.filter(SystemLog.resource_type == resource_type)
    if start_date:
        query = query.filter(SystemLog.created_at >= start_date)
    if end_date:
        query = query.filter(SystemLog.created_at <= end_date)

    total = query.count()
    items = query.order_by(SystemLog.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return Response(
        data=PageResponse(
            items=[{
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "description": log.description,
                "ip_address": log.ip_address,
                "created_at": log.created_at
            } for log in items],
            total=total,
            page=page,
            size=size
        )
    )
