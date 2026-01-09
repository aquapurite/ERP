"""
Seed script for RBAC system.
Creates 17 modules, 65 permissions, and 14 roles with appropriate permission assignments.

Usage:
    python -m scripts.seed_rbac
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import async_session_factory, engine, Base
from app.models.module import Module
from app.models.permission import Permission, RolePermission
from app.models.role import Role, RoleLevel
from app.models.region import Region, RegionType
from app.models.user import User, UserRole
from app.core.security import get_password_hash


# ==================== MODULE DEFINITIONS ====================
MODULES = [
    {"name": "Dashboard", "code": "dashboard", "description": "Main dashboard and analytics overview", "icon": "dashboard", "sort_order": 1},
    {"name": "Products", "code": "products", "description": "Product catalog management", "icon": "inventory", "sort_order": 2},
    {"name": "Orders", "code": "orders", "description": "Order management and processing", "icon": "shopping_cart", "sort_order": 3},
    {"name": "Inventory", "code": "inventory", "description": "Inventory and warehouse management", "icon": "warehouse", "sort_order": 4},
    {"name": "Service", "code": "service", "description": "Service requests and AMC management", "icon": "build", "sort_order": 5},
    {"name": "CRM", "code": "crm", "description": "Customer relationship management", "icon": "people", "sort_order": 6},
    {"name": "Complaints", "code": "complaints", "description": "Customer complaints and tickets", "icon": "report_problem", "sort_order": 7},
    {"name": "Vendors", "code": "vendors", "description": "Vendor and supplier management", "icon": "store", "sort_order": 8},
    {"name": "Logistics", "code": "logistics", "description": "Delivery and logistics management", "icon": "local_shipping", "sort_order": 9},
    {"name": "Procurement", "code": "procurement", "description": "Purchase orders and procurement", "icon": "receipt", "sort_order": 10},
    {"name": "Finance", "code": "finance", "description": "Financial management and accounting", "icon": "account_balance", "sort_order": 11},
    {"name": "HR", "code": "hr", "description": "Human resources management", "icon": "badge", "sort_order": 12},
    {"name": "Marketing", "code": "marketing", "description": "Marketing campaigns and promotions", "icon": "campaign", "sort_order": 13},
    {"name": "Reports", "code": "reports", "description": "Reports and analytics", "icon": "assessment", "sort_order": 14},
    {"name": "Notifications", "code": "notifications", "description": "System notifications", "icon": "notifications", "sort_order": 15},
    {"name": "Settings", "code": "settings", "description": "System configuration", "icon": "settings", "sort_order": 16},
    {"name": "Access Control", "code": "access_control", "description": "User roles and permissions", "icon": "security", "sort_order": 17},
]

# ==================== PERMISSION DEFINITIONS ====================
# Format: (module_code, action, name, description)
PERMISSIONS = [
    # Dashboard (1 permission)
    ("dashboard", "view", "View Dashboard", "View dashboard and analytics"),

    # Products (6 permissions)
    ("products", "view", "View Products", "View product catalog"),
    ("products", "create", "Create Products", "Add new products"),
    ("products", "update", "Update Products", "Modify product details"),
    ("products", "delete", "Delete Products", "Remove products"),
    ("products", "import", "Import Products", "Bulk import products"),
    ("products", "export", "Export Products", "Export product data"),

    # Orders (6 permissions)
    ("orders", "view", "View Orders", "View order list"),
    ("orders", "create", "Create Orders", "Create new orders"),
    ("orders", "update", "Update Orders", "Modify order details"),
    ("orders", "cancel", "Cancel Orders", "Cancel orders"),
    ("orders", "approve", "Approve Orders", "Approve order processing"),
    ("orders", "export", "Export Orders", "Export order data"),

    # Inventory (6 permissions)
    ("inventory", "view", "View Inventory", "View inventory levels"),
    ("inventory", "create", "Create Inventory", "Add inventory entries"),
    ("inventory", "update", "Update Inventory", "Modify inventory"),
    ("inventory", "transfer", "Transfer Inventory", "Transfer between warehouses"),
    ("inventory", "adjust", "Adjust Inventory", "Make inventory adjustments"),
    ("inventory", "export", "Export Inventory", "Export inventory data"),

    # Service (6 permissions)
    ("service", "view", "View Service Requests", "View service tickets"),
    ("service", "create", "Create Service Requests", "Create service requests"),
    ("service", "update", "Update Service Requests", "Modify service requests"),
    ("service", "assign", "Assign Service Requests", "Assign to technicians"),
    ("service", "close", "Close Service Requests", "Close service tickets"),
    ("service", "escalate", "Escalate Service Requests", "Escalate issues"),

    # CRM (5 permissions)
    ("crm", "view", "View Customers", "View customer data"),
    ("crm", "create", "Create Customers", "Add new customers"),
    ("crm", "update", "Update Customers", "Modify customer info"),
    ("crm", "delete", "Delete Customers", "Remove customers"),
    ("crm", "export", "Export Customers", "Export customer data"),

    # Complaints (6 permissions)
    ("complaints", "view", "View Complaints", "View complaint tickets"),
    ("complaints", "create", "Create Complaints", "Log new complaints"),
    ("complaints", "update", "Update Complaints", "Modify complaint details"),
    ("complaints", "assign", "Assign Complaints", "Assign to agents"),
    ("complaints", "resolve", "Resolve Complaints", "Mark as resolved"),
    ("complaints", "escalate", "Escalate Complaints", "Escalate to higher level"),

    # Vendors (5 permissions)
    ("vendors", "view", "View Vendors", "View vendor list"),
    ("vendors", "create", "Create Vendors", "Add new vendors"),
    ("vendors", "update", "Update Vendors", "Modify vendor details"),
    ("vendors", "delete", "Delete Vendors", "Remove vendors"),
    ("vendors", "approve", "Approve Vendors", "Approve vendor onboarding"),

    # Logistics (5 permissions)
    ("logistics", "view", "View Logistics", "View shipments"),
    ("logistics", "create", "Create Shipments", "Create shipments"),
    ("logistics", "update", "Update Shipments", "Modify shipment details"),
    ("logistics", "assign", "Assign Deliveries", "Assign to delivery agents"),
    ("logistics", "track", "Track Shipments", "Track delivery status"),

    # Procurement (5 permissions)
    ("procurement", "view", "View Procurement", "View purchase orders"),
    ("procurement", "create", "Create Purchase Orders", "Create POs"),
    ("procurement", "update", "Update Purchase Orders", "Modify POs"),
    ("procurement", "approve", "Approve Purchase Orders", "Approve POs"),
    ("procurement", "receive", "Receive Goods", "Mark goods as received"),

    # Finance (6 permissions)
    ("finance", "view", "View Finance", "View financial data"),
    ("finance", "create", "Create Transactions", "Record transactions"),
    ("finance", "update", "Update Transactions", "Modify transactions"),
    ("finance", "approve", "Approve Payments", "Approve payments"),
    ("finance", "reconcile", "Reconcile Accounts", "Perform reconciliation"),
    ("finance", "export", "Export Financial Data", "Export reports"),

    # HR (5 permissions)
    ("hr", "view", "View HR Data", "View employee data"),
    ("hr", "create", "Create Employees", "Add new employees"),
    ("hr", "update", "Update Employees", "Modify employee info"),
    ("hr", "delete", "Delete Employees", "Remove employees"),
    ("hr", "approve", "Approve HR Requests", "Approve leave/requests"),

    # Marketing (5 permissions)
    ("marketing", "view", "View Marketing", "View campaigns"),
    ("marketing", "create", "Create Campaigns", "Create marketing campaigns"),
    ("marketing", "update", "Update Campaigns", "Modify campaigns"),
    ("marketing", "delete", "Delete Campaigns", "Remove campaigns"),
    ("marketing", "publish", "Publish Campaigns", "Publish/activate campaigns"),

    # Reports (3 permissions)
    ("reports", "view", "View Reports", "View reports and analytics"),
    ("reports", "export", "Export Reports", "Export report data"),
    ("reports", "schedule", "Schedule Reports", "Schedule automated reports"),

    # Notifications (3 permissions)
    ("notifications", "view", "View Notifications", "View notifications"),
    ("notifications", "create", "Create Notifications", "Create system notifications"),
    ("notifications", "send", "Send Notifications", "Send notifications to users"),

    # Settings (2 permissions)
    ("settings", "view", "View Settings", "View system settings"),
    ("settings", "update", "Update Settings", "Modify system settings"),

    # Access Control (5 permissions)
    ("access_control", "view", "View Access Control", "View roles and permissions"),
    ("access_control", "create", "Create Roles", "Create new roles"),
    ("access_control", "update", "Update Roles", "Modify role permissions"),
    ("access_control", "delete", "Delete Roles", "Remove roles"),
    ("access_control", "assign", "Assign Roles", "Assign roles to users"),
]

# ==================== ROLE DEFINITIONS ====================
ROLES = [
    # Level 0: SUPER_ADMIN
    {
        "name": "Super Admin",
        "code": "super_admin",
        "level": RoleLevel.SUPER_ADMIN,
        "department": None,
        "description": "Full system access with all permissions",
        "is_system": True,
        "permissions": "ALL",  # Special marker for all permissions
    },

    # Level 1: DIRECTOR
    {
        "name": "CEO / Director",
        "code": "director",
        "level": RoleLevel.DIRECTOR,
        "department": None,
        "description": "Strategic oversight with view access to all modules and approval rights",
        "is_system": True,
        "permissions": [
            "dashboard:view",
            "products:view", "products:export",
            "orders:view", "orders:approve", "orders:export",
            "inventory:view", "inventory:export",
            "service:view", "service:escalate",
            "crm:view", "crm:export",
            "complaints:view", "complaints:escalate",
            "vendors:view", "vendors:approve",
            "logistics:view", "logistics:track",
            "procurement:view", "procurement:approve",
            "finance:view", "finance:approve", "finance:export",
            "hr:view", "hr:approve",
            "marketing:view", "marketing:publish",
            "reports:view", "reports:export", "reports:schedule",
            "notifications:view",
            "settings:view",
            "access_control:view",
        ],
    },

    # Level 2: HEAD
    {
        "name": "Sales Head",
        "code": "sales_head",
        "level": RoleLevel.HEAD,
        "department": "Sales",
        "description": "Head of Sales department with full sales access",
        "is_system": True,
        "permissions": [
            "dashboard:view",
            "products:view", "products:export",
            "orders:view", "orders:create", "orders:update", "orders:approve", "orders:export",
            "crm:view", "crm:create", "crm:update", "crm:export",
            "reports:view", "reports:export",
            "notifications:view",
        ],
    },
    {
        "name": "Service Head",
        "code": "service_head",
        "level": RoleLevel.HEAD,
        "department": "Service",
        "description": "Head of Service department with full service access",
        "is_system": True,
        "permissions": [
            "dashboard:view",
            "products:view",
            "service:view", "service:create", "service:update", "service:assign", "service:close", "service:escalate",
            "complaints:view", "complaints:create", "complaints:update", "complaints:assign", "complaints:resolve", "complaints:escalate",
            "crm:view", "crm:update",
            "inventory:view",
            "reports:view", "reports:export",
            "notifications:view",
        ],
    },
    {
        "name": "Finance Head",
        "code": "finance_head",
        "level": RoleLevel.HEAD,
        "department": "Finance",
        "description": "Head of Finance department with full finance access",
        "is_system": True,
        "permissions": [
            "dashboard:view",
            "orders:view", "orders:export",
            "finance:view", "finance:create", "finance:update", "finance:approve", "finance:reconcile", "finance:export",
            "procurement:view", "procurement:approve",
            "vendors:view", "vendors:approve",
            "reports:view", "reports:export", "reports:schedule",
            "notifications:view",
        ],
    },
    {
        "name": "Operations Head",
        "code": "operations_head",
        "level": RoleLevel.HEAD,
        "department": "Operations",
        "description": "Head of Operations with inventory and logistics access",
        "is_system": True,
        "permissions": [
            "dashboard:view",
            "products:view", "products:update",
            "orders:view", "orders:update",
            "inventory:view", "inventory:create", "inventory:update", "inventory:transfer", "inventory:adjust", "inventory:export",
            "logistics:view", "logistics:create", "logistics:update", "logistics:assign", "logistics:track",
            "procurement:view", "procurement:create", "procurement:update", "procurement:receive",
            "vendors:view", "vendors:create", "vendors:update",
            "reports:view", "reports:export",
            "notifications:view",
        ],
    },

    # Level 3: MANAGER
    {
        "name": "Regional Manager",
        "code": "regional_manager",
        "level": RoleLevel.MANAGER,
        "department": "Sales",
        "description": "Regional sales manager with limited territory access",
        "is_system": False,
        "permissions": [
            "dashboard:view",
            "products:view",
            "orders:view", "orders:create", "orders:update", "orders:export",
            "crm:view", "crm:create", "crm:update",
            "complaints:view", "complaints:update",
            "reports:view", "reports:export",
            "notifications:view",
        ],
    },
    {
        "name": "Warehouse Manager",
        "code": "warehouse_manager",
        "level": RoleLevel.MANAGER,
        "department": "Operations",
        "description": "Warehouse manager with inventory control",
        "is_system": False,
        "permissions": [
            "dashboard:view",
            "products:view",
            "inventory:view", "inventory:create", "inventory:update", "inventory:transfer", "inventory:adjust",
            "logistics:view", "logistics:create", "logistics:assign",
            "procurement:view", "procurement:receive",
            "reports:view",
            "notifications:view",
        ],
    },
    {
        "name": "Service Manager",
        "code": "service_manager",
        "level": RoleLevel.MANAGER,
        "department": "Service",
        "description": "Service center manager",
        "is_system": False,
        "permissions": [
            "dashboard:view",
            "products:view",
            "service:view", "service:create", "service:update", "service:assign", "service:close",
            "complaints:view", "complaints:update", "complaints:assign", "complaints:resolve",
            "crm:view", "crm:update",
            "inventory:view",
            "reports:view",
            "notifications:view",
        ],
    },
    {
        "name": "Marketing Manager",
        "code": "marketing_manager",
        "level": RoleLevel.MANAGER,
        "department": "Marketing",
        "description": "Marketing campaign manager",
        "is_system": False,
        "permissions": [
            "dashboard:view",
            "products:view",
            "marketing:view", "marketing:create", "marketing:update", "marketing:delete", "marketing:publish",
            "crm:view", "crm:export",
            "reports:view", "reports:export",
            "notifications:view", "notifications:create", "notifications:send",
        ],
    },

    # Level 4: EXECUTIVE
    {
        "name": "Customer Service Executive",
        "code": "customer_service_executive",
        "level": RoleLevel.EXECUTIVE,
        "department": "Service",
        "description": "Customer service representative",
        "is_system": False,
        "permissions": [
            "dashboard:view",
            "products:view",
            "service:view", "service:create", "service:update",
            "complaints:view", "complaints:create", "complaints:update",
            "crm:view", "crm:create", "crm:update",
            "orders:view",
            "notifications:view",
        ],
    },
    {
        "name": "Sales Executive",
        "code": "sales_executive",
        "level": RoleLevel.EXECUTIVE,
        "department": "Sales",
        "description": "Sales representative",
        "is_system": False,
        "permissions": [
            "dashboard:view",
            "products:view",
            "orders:view", "orders:create",
            "crm:view", "crm:create", "crm:update",
            "inventory:view",
            "notifications:view",
        ],
    },
    {
        "name": "Accounts Executive",
        "code": "accounts_executive",
        "level": RoleLevel.EXECUTIVE,
        "department": "Finance",
        "description": "Accounts and billing executive",
        "is_system": False,
        "permissions": [
            "dashboard:view",
            "orders:view",
            "finance:view", "finance:create", "finance:update",
            "vendors:view",
            "procurement:view",
            "notifications:view",
        ],
    },
    {
        "name": "Technician Supervisor",
        "code": "technician_supervisor",
        "level": RoleLevel.EXECUTIVE,
        "department": "Service",
        "description": "Field technician supervisor",
        "is_system": False,
        "permissions": [
            "dashboard:view",
            "products:view",
            "service:view", "service:update", "service:close",
            "complaints:view", "complaints:update",
            "inventory:view",
            "logistics:view", "logistics:track",
            "notifications:view",
        ],
    },
]

# ==================== REGION DEFINITIONS ====================
REGIONS = [
    # Country
    {"name": "India", "code": "IN", "type": RegionType.COUNTRY, "parent_code": None},

    # Zones
    {"name": "North Zone", "code": "NORTH", "type": RegionType.ZONE, "parent_code": "IN"},
    {"name": "South Zone", "code": "SOUTH", "type": RegionType.ZONE, "parent_code": "IN"},
    {"name": "East Zone", "code": "EAST", "type": RegionType.ZONE, "parent_code": "IN"},
    {"name": "West Zone", "code": "WEST", "type": RegionType.ZONE, "parent_code": "IN"},

    # States (sample)
    {"name": "Delhi", "code": "DL", "type": RegionType.STATE, "parent_code": "NORTH"},
    {"name": "Uttar Pradesh", "code": "UP", "type": RegionType.STATE, "parent_code": "NORTH"},
    {"name": "Maharashtra", "code": "MH", "type": RegionType.STATE, "parent_code": "WEST"},
    {"name": "Karnataka", "code": "KA", "type": RegionType.STATE, "parent_code": "SOUTH"},
    {"name": "Tamil Nadu", "code": "TN", "type": RegionType.STATE, "parent_code": "SOUTH"},
    {"name": "West Bengal", "code": "WB", "type": RegionType.STATE, "parent_code": "EAST"},

    # Cities (sample)
    {"name": "New Delhi", "code": "DEL", "type": RegionType.CITY, "parent_code": "DL"},
    {"name": "Mumbai", "code": "MUM", "type": RegionType.CITY, "parent_code": "MH"},
    {"name": "Bangalore", "code": "BLR", "type": RegionType.CITY, "parent_code": "KA"},
    {"name": "Chennai", "code": "CHE", "type": RegionType.CITY, "parent_code": "TN"},
    {"name": "Kolkata", "code": "KOL", "type": RegionType.CITY, "parent_code": "WB"},
]


async def seed_modules(session) -> dict:
    """Seed modules and return a mapping of code to module."""
    print("Seeding modules...")
    module_map = {}

    for module_data in MODULES:
        # Check if exists
        stmt = select(Module).where(Module.code == module_data["code"])
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing:
            module_map[module_data["code"]] = existing
            print(f"  Module '{module_data['name']}' already exists")
        else:
            module = Module(**module_data)
            session.add(module)
            await session.flush()
            module_map[module_data["code"]] = module
            print(f"  Created module: {module_data['name']}")

    return module_map


async def seed_permissions(session, module_map: dict) -> dict:
    """Seed permissions and return a mapping of code to permission."""
    print("\nSeeding permissions...")
    permission_map = {}

    for module_code, action, name, description in PERMISSIONS:
        code = f"{module_code}:{action}"
        module = module_map.get(module_code)

        if not module:
            print(f"  Warning: Module '{module_code}' not found for permission '{code}'")
            continue

        # Check if exists
        stmt = select(Permission).where(Permission.code == code)
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing:
            permission_map[code] = existing
        else:
            permission = Permission(
                name=name,
                code=code,
                description=description,
                module_id=module.id,
                action=action,
            )
            session.add(permission)
            await session.flush()
            permission_map[code] = permission
            print(f"  Created permission: {code}")

    print(f"  Total permissions: {len(permission_map)}")
    return permission_map


async def seed_roles(session, permission_map: dict) -> dict:
    """Seed roles with their permissions."""
    print("\nSeeding roles...")
    role_map = {}

    for role_data in ROLES:
        # Check if exists
        stmt = select(Role).where(Role.code == role_data["code"])
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing:
            role_map[role_data["code"]] = existing
            print(f"  Role '{role_data['name']}' already exists")
            continue

        # Create role
        role = Role(
            name=role_data["name"],
            code=role_data["code"],
            description=role_data["description"],
            level=role_data["level"],
            department=role_data["department"],
            is_system=role_data["is_system"],
        )
        session.add(role)
        await session.flush()
        role_map[role_data["code"]] = role
        print(f"  Created role: {role_data['name']} (Level: {role_data['level'].name})")

        # Assign permissions
        permissions_to_assign = role_data["permissions"]
        if permissions_to_assign == "ALL":
            # SUPER_ADMIN gets all permissions
            permissions_to_assign = list(permission_map.keys())

        for perm_code in permissions_to_assign:
            permission = permission_map.get(perm_code)
            if permission:
                role_perm = RolePermission(
                    role_id=role.id,
                    permission_id=permission.id,
                )
                session.add(role_perm)

        print(f"    Assigned {len(permissions_to_assign)} permissions")

    return role_map


async def seed_regions(session) -> dict:
    """Seed regions and return a mapping of code to region."""
    print("\nSeeding regions...")
    region_map = {}

    # First pass: create all regions without parent references
    for region_data in REGIONS:
        stmt = select(Region).where(Region.code == region_data["code"])
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing:
            region_map[region_data["code"]] = existing
            print(f"  Region '{region_data['name']}' already exists")
        else:
            region = Region(
                name=region_data["name"],
                code=region_data["code"],
                type=region_data["type"],
            )
            session.add(region)
            await session.flush()
            region_map[region_data["code"]] = region
            print(f"  Created region: {region_data['name']} ({region_data['type'].value})")

    # Second pass: set parent references
    for region_data in REGIONS:
        if region_data["parent_code"]:
            region = region_map[region_data["code"]]
            parent = region_map.get(region_data["parent_code"])
            if parent and region.parent_id != parent.id:
                region.parent_id = parent.id

    return region_map


async def seed_super_admin_user(session, role_map: dict, region_map: dict):
    """Create a default super admin user."""
    print("\nCreating Super Admin user...")

    stmt = select(User).where(User.email == "admin@aquapurite.com")
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing:
        print("  Super Admin user already exists")
        return existing

    # Create super admin user
    user = User(
        email="admin@aquapurite.com",
        phone="+919999999999",
        password_hash=get_password_hash("Admin@123"),
        first_name="Super",
        last_name="Admin",
        employee_code="EMP001",
        department="Administration",
        designation="System Administrator",
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    # Assign super admin role
    super_admin_role = role_map.get("super_admin")
    if super_admin_role:
        user_role = UserRole(
            user_id=user.id,
            role_id=super_admin_role.id,
        )
        session.add(user_role)

    print(f"  Created Super Admin: admin@aquapurite.com (password: Admin@123)")
    return user


async def main():
    """Main seed function."""
    print("=" * 60)
    print("RBAC Seed Script for Consumer Durable Backend")
    print("=" * 60)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        try:
            # Seed data
            module_map = await seed_modules(session)
            permission_map = await seed_permissions(session, module_map)
            role_map = await seed_roles(session, permission_map)
            region_map = await seed_regions(session)
            await seed_super_admin_user(session, role_map, region_map)

            # Commit all changes
            await session.commit()

            print("\n" + "=" * 60)
            print("Seeding completed successfully!")
            print("=" * 60)
            print(f"\nSummary:")
            print(f"  - Modules: {len(module_map)}")
            print(f"  - Permissions: {len(permission_map)}")
            print(f"  - Roles: {len(role_map)}")
            print(f"  - Regions: {len(region_map)}")
            print(f"\nDefault Super Admin:")
            print(f"  - Email: admin@aquapurite.com")
            print(f"  - Password: Admin@123")

        except Exception as e:
            await session.rollback()
            print(f"\nError during seeding: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
