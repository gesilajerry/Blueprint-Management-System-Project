from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


# 项目组成员关系表
project_group_members = Table(
    'project_group_members', Base.metadata,
    Column('group_id', String(36), ForeignKey('project_groups.id'), primary_key=True),
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('role_type', String(20), comment="成员角色：manager/engineer"),
    Column('created_at', DateTime, default=datetime.utcnow),
    Index('idx_group_user', 'group_id', 'user_id')
)


class ProjectGroup(Base):
    """项目组表"""
    __tablename__ = "project_groups"

    id = Column(String(36), primary_key=True, default=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    name = Column(String(100), nullable=False, comment="项目组名称")
    code = Column(String(50), unique=True, nullable=False, comment="项目组编号")
    leader_id = Column(String(36), ForeignKey("users.id"), comment="项目负责人 ID")
    department_id = Column(String(36), ForeignKey("departments.id"), comment="所属部门 ID")
    status = Column(String(20), default="active", comment="状态：active/disabled")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联
    leader = relationship("User", foreign_keys=[leader_id])
    department = relationship("Department")
    members = relationship("User", secondary=project_group_members, back_populates="project_groups")
    products = relationship("Product", back_populates="project_group")
