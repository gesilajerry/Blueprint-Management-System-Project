from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base


class ConfidentialityLevel(str, enum.Enum):
    """保密等级枚举"""
    A = "A"  # 核心机密
    B = "B"  # 重要
    C = "C"  # 一般


class DrawingStatus(str, enum.Enum):
    """图纸状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ReviewStatus(str, enum.Enum):
    """审核状态枚举"""
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已审核
    REJECTED = "rejected"    # 已驳回


class Drawing(Base):
    """图纸表"""
    __tablename__ = "drawings"

    id = Column(String(36), primary_key=True, default=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    drawing_no = Column(String(50), unique=True, nullable=False, index=True, comment="图号")
    name = Column(String(200), nullable=False, comment="图纸名称")
    product_id = Column(String(36), ForeignKey("products.id"), comment="所属产品 ID")
    department_id = Column(String(36), ForeignKey("departments.id"), comment="所属部门 ID")
    confidentiality_level = Column(Enum(ConfidentialityLevel), nullable=False, comment="保密等级")
    is_core_part = Column(Boolean, default=False, comment="是否核心部件")
    creator_id = Column(String(36), ForeignKey("users.id"), comment="创建人 ID")
    status = Column(Enum(DrawingStatus), default=DrawingStatus.ACTIVE, comment="状态")
    review_status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, comment="审核状态")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 技术参数（可选）
    purpose = Column(Text, comment="用途背景")
    material = Column(String(200), comment="关键材料")
    dimensions = Column(String(200), comment="关键尺寸")
    secret_points = Column(Text, comment="保密要点")

    # 关联
    product = relationship("Product", back_populates="drawings")
    department = relationship("Department", back_populates="drawings")
    creator = relationship("User", back_populates="created_drawings")
    versions = relationship("DrawingVersion", back_populates="drawing", cascade="all, delete-orphan")
    core_part_keywords = relationship("CorePartKeyword", secondary="drawing_core_parts", back_populates="drawings")

    # 关联图纸（上游/下游）
    related_drawings = relationship("DrawingRelation", foreign_keys="DrawingRelation.source_id", back_populates="source")


class DrawingVersion(Base):
    """图纸版本表"""
    __tablename__ = "drawing_versions"

    id = Column(String(36), primary_key=True, default=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    drawing_id = Column(String(36), ForeignKey("drawings.id"), nullable=False, index=True)
    version_no = Column(String(20), nullable=False, comment="版本号")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_name = Column(String(200), comment="文件名")
    file_size = Column(Integer, comment="文件大小 (字节)")
    file_format = Column(String(20), comment="文件格式")
    change_types = Column(String(500), comment="变更类型（逗号分隔）")
    change_reason = Column(Text, comment="变更原因")
    related_issue = Column(String(50), comment="关联问题单号")
    uploader_id = Column(String(36), ForeignKey("users.id"), comment="上传人 ID")
    uploaded_at = Column(DateTime, default=datetime.utcnow, comment="上传时间")
    is_latest = Column(Boolean, default=True, comment="是否最新版本")

    # 关联
    drawing = relationship("Drawing", back_populates="versions")
    uploader = relationship("User", back_populates="uploaded_versions")


class DrawingRelation(Base):
    """图纸关联关系表"""
    __tablename__ = "drawing_relations"

    id = Column(String(36), primary_key=True, default=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    source_id = Column(String(36), ForeignKey("drawings.id"), nullable=False, comment="源图纸 ID")
    target_id = Column(String(36), ForeignKey("drawings.id"), nullable=False, comment="目标图纸 ID")
    relation_type = Column(String(20), comment="关系类型：upstream/downstream")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联
    source = relationship("Drawing", foreign_keys=[source_id], back_populates="related_drawings")
    target = relationship("Drawing", foreign_keys=[target_id])
