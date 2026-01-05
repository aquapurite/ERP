from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    roles,
    permissions,
    users,
    access_control,
    categories,
    brands,
    products,
    customers,
    orders,
    warehouses,
    inventory,
    transfers,
    service_requests,
    technicians,
)


# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Access Control endpoints
api_router.include_router(auth.router)
api_router.include_router(roles.router)
api_router.include_router(permissions.router)
api_router.include_router(users.router)
api_router.include_router(access_control.router)

# Product Catalog endpoints
api_router.include_router(categories.router)
api_router.include_router(brands.router)
api_router.include_router(products.router)

# CRM & Orders endpoints
api_router.include_router(customers.router)
api_router.include_router(orders.router)

# Inventory Management endpoints
api_router.include_router(warehouses.router)
api_router.include_router(inventory.router)
api_router.include_router(transfers.router)

# Service Management endpoints
api_router.include_router(service_requests.router)
api_router.include_router(technicians.router)
