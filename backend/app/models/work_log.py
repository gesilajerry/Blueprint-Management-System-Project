from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class WorkLog(Base):
    """工作日志表"""
    __tablename__ = "work_logs"

    id = Column(String(36), primary_key=True, default=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, comment="填写人 ID")
    content = Column(Text, nullable=False, comment="日志内容")
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联
    user = relationship("User", back_populates="work_logs")
