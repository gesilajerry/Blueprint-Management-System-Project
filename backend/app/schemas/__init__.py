from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Any


# === 通用响应 ===
class Response(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


# === 用户相关 Schema ===
class UserBase(BaseModel):
    username: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str
    department_id: str
    role_id: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[str] = None
    role_id: Optional[str] = None
    status: Optional[str] = None


class UserResponse(UserBase):
    id: str
    department_id: Optional[str]
    role_id: Optional[str]
    status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None


# === 部门相关 Schema ===
class DepartmentBase(BaseModel):
    name: str
    code: str
    manager: Optional[str] = None
    sort: int = 0


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    manager: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# === 角色相关 Schema ===
class RoleBase(BaseModel):
    name: str
    code: str


class RoleCreate(RoleBase):
    permissions: Optional[dict] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[dict] = None
    status: Optional[str] = None


class RoleResponse(RoleBase):
    id: str
    permissions: dict = {}
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# === 产品相关 Schema ===
class ProductBase(BaseModel):
    name: str
    code: str
    manager: Optional[str] = None
    start_date: Optional[str] = None


class ProductCreate(ProductBase):
    department_id: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[str] = None
    manager: Optional[str] = None
    start_date: Optional[str] = None
    status: Optional[str] = None


class ProductResponse(ProductBase):
    id: str
    department_id: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# === 图纸相关 Schema ===
class DrawingBase(BaseModel):
    name: str
    product_id: str
    department_id: str
    is_core_part: bool = False
    confidentiality_level: str  # A, B, C


class DrawingCreate(DrawingBase):
    pass


class DrawingUpdate(BaseModel):
    name: Optional[str] = None
    purpose: Optional[str] = None
    material: Optional[str] = None
    dimensions: Optional[str] = None
    secret_points: Optional[str] = None


class DrawingResponse(DrawingBase):
    id: str
    drawing_no: str
    creator_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DrawingVersionCreate(BaseModel):
    change_types: Optional[str] = None
    change_reason: Optional[str] = None
    related_issue: Optional[str] = None


class DrawingVersionResponse(BaseModel):
    id: str
    drawing_id: str
    version_no: str
    file_name: str
    file_size: Optional[int]
    file_format: Optional[str]
    change_types: Optional[str]
    change_reason: Optional[str]
    related_issue: Optional[str]
    uploader_id: Optional[str]
    uploaded_at: datetime
    is_latest: bool

    class Config:
        from_attributes = True


# === 核心部件词库 Schema ===
class CorePartKeywordCreate(BaseModel):
    keyword: str


class CorePartKeywordResponse(BaseModel):
    id: str
    keyword: str
    created_at: datetime

    class Config:
        from_attributes = True


# === 系统日志 Schema ===
class SystemLogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    description: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# === 分页参数 ===
class PageParams(BaseModel):
    page: int = 1
    size: int = 10


class PageResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int


# === 工作日志 Schema ===
class WorkLogCreate(BaseModel):
    content: str


class WorkLogUpdate(BaseModel):
    content: Optional[str] = None


class WorkLogResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
