from sqlalchemy import Column, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Product(Base):
    """产品/项目表"""
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    name = Column(String(200), nullable=False, comment="产品/项目名称")
    code = Column(String(50), unique=True, nullable=False, comment="立项编号")
    status = Column(String(20), default="active", comment="状态：active/archived")
    project_group_id = Column(String(36), ForeignKey("project_groups.id"), comment="所属项目组 ID")
    department_id = Column(String(36), ForeignKey("departments.id"), comment="所属部门 ID")
    manager = Column(String(50), comment="负责人")
    manager_id = Column(String(36), ForeignKey("users.id"), comment="负责人 ID")
    start_date = Column(Date, comment="立项日期")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联
    department = relationship("Department", back_populates="products")
    project_group = relationship("ProjectGroup", back_populates="products")
    drawings = relationship("Drawing", back_populates="product")
    manager_user = relationship("User", foreign_keys=[manager_id])
