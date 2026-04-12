from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


# 图纸 - 核心部件关键词关联表
drawing_core_parts = Table(
    'drawing_core_parts',
    Base.metadata,
    Column('drawing_id', String(36), ForeignKey('drawings.id'), primary_key=True),
    Column('keyword_id', String(36), ForeignKey('core_part_keywords.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class CorePartKeyword(Base):
    """核心部件词库表"""
    __tablename__ = "core_part_keywords"

    id = Column(String(36), primary_key=True, default=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
    keyword = Column(String(100), nullable=False, index=True, comment="关键词")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联
    drawings = relationship("Drawing", secondary="drawing_core_parts", back_populates="core_part_keywords")
