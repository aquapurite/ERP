from fastapi import APIRouter

from app.api.v1.endpoints import (
    # Access Control
    auth,
    roles,
    permissions,
    users,
    access_control,
    # Product Catalog
    categories,
    brands,
    products,
    # CRM & Orders
    customers,
    orders,
    # Inventory Management
    warehouses,
    inventory,
    transfers,
    # Service Management
    service_requests,
    technicians,
    installations,  # NEW - Installation & Warranty
    # Vendor & Procurement (NEW)
    vendors,
    purchase,
    # Accounting & Finance (NEW)
    accounting,
    billing,
    # Dealer/Distributor (NEW)
    dealers,
    # Commission & Incentives (NEW)
    commissions,
    # Promotions & Loyalty (NEW)
    promotions,
    # Multi-Channel Commerce (NEW)
    channels,
    # Company/Business Entity (NEW)
    company,
    # OMS/WMS (NEW)
    transporters,
    wms,
    picklists,
    shipments,
    manifests,
    serviceability,  # Pincode Serviceability & Order Allocation
    # Call Center CRM (NEW)
    call_center,
    # Lead Management (NEW)
    leads,
    # Escalation Management (NEW)
    escalations,
    # Campaign Management (NEW)
    campaigns,
    # Franchisee CRM (NEW)
    franchisees,
)


# Create main API router
api_router = APIRouter(prefix="/api/v1")

# ==================== Access Control ====================
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)
api_router.include_router(
    roles.router,
    prefix="/roles",
    tags=["Roles"]
)
api_router.include_router(
    permissions.router,
    prefix="/permissions",
    tags=["Permissions"]
)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)
api_router.include_router(
    access_control.router,
    prefix="/access-control",
    tags=["Access Control"]
)

# ==================== Product Catalog ====================
api_router.include_router(
    categories.router,
    prefix="/categories",
    tags=["Categories"]
)
api_router.include_router(
    brands.router,
    prefix="/brands",
    tags=["Brands"]
)
api_router.include_router(
    products.router,
    prefix="/products",
    tags=["Products"]
)

# ==================== CRM & Orders ====================
api_router.include_router(
    customers.router,
    prefix="/customers",
    tags=["Customers"]
)
api_router.include_router(
    orders.router,
    prefix="/orders",
    tags=["Orders"]
)

# ==================== Inventory Management ====================
api_router.include_router(
    warehouses.router,
    prefix="/warehouses",
    tags=["Warehouses"]
)
api_router.include_router(
    inventory.router,
    prefix="/inventory",
    tags=["Inventory"]
)
api_router.include_router(
    transfers.router,
    prefix="/transfers",
    tags=["Stock Transfers"]
)

# ==================== Service Management ====================
api_router.include_router(
    service_requests.router,
    prefix="/service-requests",
    tags=["Service Requests"]
)
api_router.include_router(
    technicians.router,
    prefix="/technicians",
    tags=["Technicians"]
)
api_router.include_router(
    installations.router,
    prefix="/installations",
    tags=["Installations & Warranty"]
)

# ==================== Vendor & Procurement (P2P) ====================
api_router.include_router(
    vendors.router,
    prefix="/vendors",
    tags=["Vendors/Suppliers"]
)
api_router.include_router(
    purchase.router,
    prefix="/purchase",
    tags=["Purchase/Procurement"]
)

# ==================== Accounting & Finance ====================
api_router.include_router(
    accounting.router,
    prefix="/accounting",
    tags=["Accounting"]
)
api_router.include_router(
    billing.router,
    prefix="/billing",
    tags=["Billing/E-Invoice"]
)

# ==================== Dealer/Distributor ====================
api_router.include_router(
    dealers.router,
    prefix="/dealers",
    tags=["Dealers/Distributors"]
)

# ==================== Commission & Incentives ====================
api_router.include_router(
    commissions.router,
    prefix="/commissions",
    tags=["Commissions"]
)

# ==================== Promotions & Loyalty ====================
api_router.include_router(
    promotions.router,
    prefix="/promotions",
    tags=["Promotions/Loyalty"]
)

# ==================== Multi-Channel Commerce ====================
api_router.include_router(
    channels.router,
    prefix="/channels",
    tags=["Sales Channels"]
)

# ==================== Company/Business Entity ====================
api_router.include_router(
    company.router,
    prefix="/company",
    tags=["Company/Business Entity"]
)

# ==================== OMS/WMS - Logistics & Fulfillment ====================
api_router.include_router(
    transporters.router,
    prefix="/transporters",
    tags=["Transporters/Carriers"]
)
api_router.include_router(
    wms.router,
    prefix="/wms",
    tags=["WMS (Zones/Bins/PutAway)"]
)
api_router.include_router(
    picklists.router,
    prefix="/picklists",
    tags=["Picklists (Order Picking)"]
)
api_router.include_router(
    shipments.router,
    prefix="/shipments",
    tags=["Shipments"]
)
api_router.include_router(
    manifests.router,
    prefix="/manifests",
    tags=["Manifests (Transporter Handover)"]
)
api_router.include_router(
    serviceability.router,
    tags=["Serviceability & Order Allocation"]
)

# ==================== Call Center CRM ====================
api_router.include_router(
    call_center.router,
    prefix="/call-center",
    tags=["Call Center CRM"]
)

# ==================== Lead Management ====================
api_router.include_router(
    leads.router,
    prefix="/leads",
    tags=["Lead Management"]
)

# ==================== Escalation Management ====================
api_router.include_router(
    escalations.router,
    prefix="/escalations",
    tags=["Escalation Management"]
)

# ==================== Campaign Management ====================
api_router.include_router(
    campaigns.router,
    prefix="/campaigns",
    tags=["Campaign Management"]
)

# ==================== Franchisee CRM ====================
api_router.include_router(
    franchisees.router,
    prefix="/franchisees",
    tags=["Franchisee CRM"]
)
