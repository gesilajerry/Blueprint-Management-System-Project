from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    name = Column(String(50), nullable=False, comment="角色名称")
    code = Column(String(50), unique=True, nullable=False, comment="角色编码")
    permissions = Column(JSON, default=dict, comment="权限配置")
    status = Column(String(20), default="active", comment="状态：active/disabled")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联
    users = relationship("User", back_populates="role")
