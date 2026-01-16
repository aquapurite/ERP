from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

from app.models.role import RoleLevel


class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    code: str = Field(..., min_length=1, max_length=50, description="Unique role code")
    description: Optional[str] = Field(None, description="Role description")
    level: RoleLevel = Field(..., description="Role hierarchy level")
    department: Optional[str] = Field(None, max_length=50, description="Department association")


class RoleCreate(RoleBase):
    """Role creation schema."""
    permission_ids: Optional[List[uuid.UUID]] = Field(
        default=[],
        description="Permission IDs to assign"
    )


class RoleUpdate(BaseModel):
    """Role update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    level: Optional[RoleLevel] = None
    department: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class PermissionBasicInfo(BaseModel):
    """Basic permission info for role response."""
    id: uuid.UUID
    name: str
    code: str
    action: str
    module_name: Optional[str] = None

    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    """Role response schema."""
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    level: str
    department: Optional[str] = None
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleWithPermissions(RoleResponse):
    """Role response with permissions."""
    permissions: List[PermissionBasicInfo] = []


class RoleListResponse(BaseModel):
    """Paginated role list response."""
    items: List[RoleResponse]
    total: int
    page: int
    size: int
    pages: int
