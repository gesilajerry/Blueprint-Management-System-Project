from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Department(Base):
    """部门表"""
    __tablename__ = "departments"

    id = Column(String(36), primary_key=True, default=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    name = Column(String(100), nullable=False, comment="部门名称")
    code = Column(String(50), unique=True, nullable=False, comment="部门编码")
    manager = Column(String(50), comment="负责人")
    sort = Column(Integer, default=0, comment="排序")
    status = Column(String(20), default="active", comment="状态：active/disabled")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联
    users = relationship("User", back_populates="department")
    products = relationship("Product", back_populates="department")
    drawings = relationship("Drawing", back_populates="department")
