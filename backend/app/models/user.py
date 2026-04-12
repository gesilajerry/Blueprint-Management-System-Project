from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    name = Column(String(50), nullable=False, comment="姓名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    department_id = Column(String(36), ForeignKey("departments.id"), comment="所属部门 ID")
    role_id = Column(String(36), ForeignKey("roles.id"), comment="角色 ID")
    email = Column(String(100), comment="邮箱")
    phone = Column(String(20), comment="手机")
    status = Column(String(20), default="active", comment="状态：active/disabled")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    last_login_at = Column(DateTime, comment="最后登录时间")

    # 关联
    department = relationship("Department", back_populates="users")
    role = relationship("Role", back_populates="users")
    project_groups = relationship("ProjectGroup", secondary="project_group_members", back_populates="members", lazy="noload")
    created_drawings = relationship("Drawing", back_populates="creator")
    uploaded_versions = relationship("DrawingVersion", back_populates="uploader")
    logs = relationship("SystemLog", back_populates="user")
    work_logs = relationship("WorkLog", back_populates="user")
