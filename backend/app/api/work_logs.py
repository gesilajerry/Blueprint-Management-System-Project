from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..core.database import get_db
from ..models.user import User
from ..models.work_log import WorkLog
from ..schemas import Response, PageResponse, WorkLogCreate, WorkLogUpdate
from .deps import get_current_user, require_permission, check_user_permission
from ..core.logger import log_operation

router = APIRouter(prefix="/work-logs", tags=["工作日志"])


@router.get("", response_model=Response)
async def get_work_logs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作日志列表"""
    # 基础查询
    query = db.query(WorkLog)

    # 根据权限过滤：只有有 viewLogs 权限（管理员/CTO）才能查看所有日志
    if check_user_permission(current_user, "viewLogs", db):
        # 管理员/CTO 可以查看指定用户的日志
        if user_id:
            query = query.filter(WorkLog.user_id == user_id)
    else:
        # 其他用户只能查看自己的日志
        if user_id and user_id != current_user.id:
            raise HTTPException(status_code=403, detail="您没有权限查看其他用户的工作日志")
        query = query.filter(WorkLog.user_id == current_user.id)

    if start_date:
        query = query.filter(WorkLog.created_at >= start_date)
    if end_date:
        query = query.filter(WorkLog.created_at <= end_date)

    total = query.count()
    items = query.order_by(WorkLog.created_at.desc()).offset((page - 1) * size).limit(size).all()

    # 获取用户信息
    result_items = []
    for log in items:
        user = db.query(User).filter(User.id == log.user_id).first()
        result_items.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_name": user.name if user else "未知",
            "content": log.content,
            "created_at": log.created_at,
            "updated_at": log.updated_at
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
async def create_work_log(
    log_data: WorkLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("workLog"))
):
    """创建工作日志"""
    work_log = WorkLog(
        user_id=current_user.id,
        content=log_data.content
    )

    db.add(work_log)
    db.commit()
    db.refresh(work_log)

    log_operation(
        user_id=current_user.id,
        action="CREATE_WORK_LOG",
        resource_type="work_log",
        resource_id=work_log.id,
        description=f"创建工作日志",
        ip_address="unknown"
    )

    return Response(message="工作日志创建成功", data={"id": work_log.id})


@router.get("/my", response_model=Response)
async def get_my_work_logs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("workLog"))
):
    """获取当前用户的工作日志"""
    query = db.query(WorkLog).filter(WorkLog.user_id == current_user.id)

    total = query.count()
    items = query.order_by(WorkLog.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return Response(
        data=PageResponse(
            items=[{
                "id": log.id,
                "user_id": log.user_id,
                "content": log.content,
                "created_at": log.created_at,
                "updated_at": log.updated_at
            } for log in items],
            total=total,
            page=page,
            size=size
        )
    )


@router.delete("/{log_id}", response_model=Response)
async def delete_work_log(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除工作日志"""
    work_log = db.query(WorkLog).filter(WorkLog.id == log_id).first()
    if not work_log:
        raise HTTPException(status_code=404, detail="日志不存在")

    # 只能删除自己的日志，或者有 manageUsers 权限（管理员）可以删除任何人的
    if work_log.user_id != current_user.id and not check_user_permission(current_user, "manageUsers", db):
        raise HTTPException(status_code=403, detail="无权限删除该日志")

    db.delete(work_log)
    db.commit()

    return Response(message="工作日志已删除")
