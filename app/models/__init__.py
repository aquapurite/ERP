from app.models.user import User, UserRole
from app.models.role import Role, RoleLevel
from app.models.permission import Permission, RolePermission
from app.models.module import Module
from app.models.region import Region, RegionType
from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.brand import Brand
from app.models.product import (
    Product,
    ProductStatus,
    ProductImage,
    ProductSpecification,
    ProductVariant,
    ProductDocument,
    DocumentType,
)
from app.models.customer import (
    Customer,
    CustomerAddress,
    CustomerType,
    CustomerSource,
    AddressType,
)
from app.models.order import (
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    Payment,
    PaymentStatus,
    PaymentMethod,
    OrderSource,
    Invoice,
)
from app.models.warehouse import Warehouse, WarehouseType
from app.models.inventory import (
    StockItem,
    StockItemStatus,
    InventorySummary,
    StockMovement,
    StockMovementType,
)
from app.models.stock_transfer import (
    StockTransfer,
    StockTransferItem,
    StockTransferSerial,
    TransferStatus,
    TransferType,
)
from app.models.stock_adjustment import (
    StockAdjustment,
    StockAdjustmentItem,
    AdjustmentType,
    AdjustmentStatus,
    InventoryAudit,
)
from app.models.technician import (
    Technician,
    TechnicianStatus,
    TechnicianType,
    SkillLevel,
    TechnicianJobHistory,
    TechnicianLeave,
)
from app.models.service_request import (
    ServiceRequest,
    ServiceType,
    ServicePriority,
    ServiceStatus,
    ServiceSource,
    ServiceStatusHistory,
    PartsRequest,
)
from app.models.amc import (
    AMCContract,
    AMCType,
    AMCStatus,
    AMCPlan,
)
from app.models.installation import (
    Installation,
    InstallationStatus,
    WarrantyClaim,
)

__all__ = [
    # Access Control
    "User",
    "UserRole",
    "Role",
    "RoleLevel",
    "Permission",
    "RolePermission",
    "Module",
    "Region",
    "RegionType",
    "AuditLog",
    # Products
    "Category",
    "Brand",
    "Product",
    "ProductStatus",
    "ProductImage",
    "ProductSpecification",
    "ProductVariant",
    "ProductDocument",
    "DocumentType",
    # Customers
    "Customer",
    "CustomerAddress",
    "CustomerType",
    "CustomerSource",
    "AddressType",
    # Orders
    "Order",
    "OrderItem",
    "OrderStatus",
    "OrderStatusHistory",
    "Payment",
    "PaymentStatus",
    "PaymentMethod",
    "OrderSource",
    "Invoice",
    # Inventory
    "Warehouse",
    "WarehouseType",
    "StockItem",
    "StockItemStatus",
    "InventorySummary",
    "StockMovement",
    "StockMovementType",
    "StockTransfer",
    "StockTransferItem",
    "StockTransferSerial",
    "TransferStatus",
    "TransferType",
    "StockAdjustment",
    "StockAdjustmentItem",
    "AdjustmentType",
    "AdjustmentStatus",
    "InventoryAudit",
    # Service
    "Technician",
    "TechnicianStatus",
    "TechnicianType",
    "SkillLevel",
    "TechnicianJobHistory",
    "TechnicianLeave",
    "ServiceRequest",
    "ServiceType",
    "ServicePriority",
    "ServiceStatus",
    "ServiceSource",
    "ServiceStatusHistory",
    "PartsRequest",
    "AMCContract",
    "AMCType",
    "AMCStatus",
    "AMCPlan",
    "Installation",
    "InstallationStatus",
    "WarrantyClaim",
]
