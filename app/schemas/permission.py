from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class ModuleBasicInfo(BaseModel):
    """Basic module info for permission response."""
    id: uuid.UUID
    name: str
    code: str

    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    """Permission response schema."""
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    action: Optional[str] = None
    is_active: bool
    module: Optional[ModuleBasicInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PermissionListResponse(BaseModel):
    """Paginated permission list response."""
    items: List[PermissionResponse]
    total: int


class PermissionGroupItem(BaseModel):
    """Permission item within a module group."""
    id: uuid.UUID
    name: str
    code: str
    action: Optional[str] = None
    description: Optional[str] = None


class ModulePermissionGroup(BaseModel):
    """Module with its permissions."""
    module_id: uuid.UUID
    module_name: str
    module_code: str
    permissions: List[PermissionGroupItem]


class PermissionsByModule(BaseModel):
    """Permissions grouped by module."""
    modules: List[ModulePermissionGroup]
    total_permissions: int


class RolePermissionUpdate(BaseModel):
    """Schema for updating role permissions."""
    permission_ids: List[uuid.UUID] = Field(
        ...,
        description="Complete list of permission IDs for the role"
    )
