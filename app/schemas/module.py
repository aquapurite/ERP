from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class ModuleBase(BaseModel):
    """Base module schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Module name")
    code: str = Field(..., min_length=1, max_length=50, description="Unique module code")
    description: Optional[str] = Field(None, description="Module description")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name/class")
    sort_order: int = Field(default=0, description="Display order")


class ModuleResponse(BaseModel):
    """Module response schema."""
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModuleListResponse(BaseModel):
    """Module list response."""
    items: List[ModuleResponse]
    total: int
