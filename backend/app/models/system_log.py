from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"

    id = Column(String(36), primary_key=True, default=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, comment="操作人 ID")
    action = Column(String(50), nullable=False, index=True, comment="操作类型")
    resource_type = Column(String(50), index=True, comment="资源类型")
    resource_id = Column(String(36), comment="资源 ID")
    description = Column(Text, comment="操作描述")
    ip_address = Column(String(50), comment="IP 地址")
    user_agent = Column(String(500), comment="浏览器信息")
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")

    # 关联
    user = relationship("User", back_populates="logs")
