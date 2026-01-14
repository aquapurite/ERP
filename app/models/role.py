import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, Boolean, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import UserRole
    from app.models.permission import RolePermission


class RoleLevel(int, Enum):
    """
    Role hierarchy levels.
    Lower number = Higher authority.
    SUPER_ADMIN (0) has all permissions automatically.
    """
    SUPER_ADMIN = 0
    DIRECTOR = 1
    HEAD = 2
    MANAGER = 3
    EXECUTIVE = 4


class Role(Base):
    """
    Role model for RBAC.
    14 Roles across 5 levels:
    - SUPER_ADMIN: Super Admin
    - DIRECTOR: CEO / Director
    - HEAD: Sales Head, Service Head, Finance Head, Operations Head
    - MANAGER: Regional Manager, Warehouse Manager, Service Manager, Marketing Manager
    - EXECUTIVE: Customer Service Executive, Sales Executive, Accounts Executive, Technician Supervisor
    """
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Hierarchy level
    level: Mapped[RoleLevel] = mapped_column(
        SQLEnum(RoleLevel),
        nullable=False,
        default=RoleLevel.EXECUTIVE
    )

    # Department association (for HEAD/MANAGER roles)
    department: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # System role (cannot be deleted)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan"
    )

    @property
    def is_super_admin(self) -> bool:
        """Check if this role is SUPER_ADMIN level."""
        return self.level == RoleLevel.SUPER_ADMIN

    def has_higher_level_than(self, other_role: "Role") -> bool:
        """Check if this role has higher authority than another role."""
        return self.level.value < other_role.level.value

    def __repr__(self) -> str:
        return f"<Role(name='{self.name}', code='{self.code}', level='{self.level.name}')>"
