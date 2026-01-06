from typing import Optional
import uuid
from math import ceil

from fastapi import APIRouter, HTTPException, status, Query, Depends

from app.api.deps import DB, CurrentUser, Permissions, require_permissions
from app.models.customer import CustomerType
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    Customer360Response,
    AddressCreate,
    AddressUpdate,
    AddressResponse,
)
from app.services.order_service import OrderService
from app.services.customer360_service import Customer360Service


router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get(
    "",
    response_model=CustomerListResponse,
    dependencies=[Depends(require_permissions("crm:view"))]
)
async def list_customers(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, phone, email"),
    customer_type: Optional[CustomerType] = Query(None),
    is_active: bool = Query(True),
):
    """
    Get paginated list of customers.
    Requires: crm:view permission
    """
    service = OrderService(db)
    skip = (page - 1) * size

    customers, total = await service.get_customers(
        search=search,
        customer_type=customer_type.value if customer_type else None,
        is_active=is_active,
        skip=skip,
        limit=size,
    )

    return CustomerListResponse(
        items=[CustomerResponse.model_validate(c) for c in customers],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    dependencies=[Depends(require_permissions("crm:view"))]
)
async def get_customer(
    customer_id: uuid.UUID,
    db: DB,
):
    """Get a customer by ID."""
    service = OrderService(db)
    customer = await service.get_customer_by_id(customer_id)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return CustomerResponse.model_validate(customer)


@router.get(
    "/phone/{phone}",
    response_model=CustomerResponse,
    dependencies=[Depends(require_permissions("crm:view"))]
)
async def get_customer_by_phone(
    phone: str,
    db: DB,
):
    """Get a customer by phone number."""
    service = OrderService(db)
    customer = await service.get_customer_by_phone(phone)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return CustomerResponse.model_validate(customer)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("crm:create"))]
)
async def create_customer(
    data: CustomerCreate,
    db: DB,
    current_user: CurrentUser,
):
    """
    Create a new customer.
    Requires: crm:create permission
    """
    service = OrderService(db)

    # Check if phone already exists
    existing = await service.get_customer_by_phone(data.phone)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this phone number already exists"
        )

    customer = await service.create_customer(data.model_dump())
    return CustomerResponse.model_validate(customer)


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
    dependencies=[Depends(require_permissions("crm:update"))]
)
async def update_customer(
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """
    Update a customer.
    Requires: crm:update permission
    """
    service = OrderService(db)

    customer = await service.get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    updated = await service.update_customer(
        customer_id,
        data.model_dump(exclude_unset=True)
    )
    return CustomerResponse.model_validate(updated)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("crm:delete"))]
)
async def delete_customer(
    customer_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """
    Deactivate a customer.
    Requires: crm:delete permission
    """
    service = OrderService(db)

    customer = await service.get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    await service.update_customer(customer_id, {"is_active": False})


# ==================== CUSTOMER 360 ENDPOINT ====================

@router.get(
    "/{customer_id}/360",
    response_model=Customer360Response,
    dependencies=[Depends(require_permissions("crm:view"))],
    summary="Get Customer 360 View",
    description="""
    Get a comprehensive 360-degree view of the customer including:

    - **Customer Profile**: Basic info and addresses
    - **Statistics**: Order totals, service counts, ratings
    - **Timeline**: Chronological journey events
    - **Orders**: All orders with status history
    - **Shipments**: Delivery tracking
    - **Installations**: Product installations and warranty
    - **Service Requests**: Support tickets and repairs
    - **Calls**: Call center interactions
    - **Payments**: Payment history
    - **AMC Contracts**: Active maintenance contracts
    - **Lead Info**: Original lead data if converted
    """
)
async def get_customer_360(
    customer_id: uuid.UUID,
    db: DB,
    include_timeline: bool = Query(True, description="Include chronological timeline"),
    limit: int = Query(50, ge=1, le=200, description="Max records per section"),
):
    """
    Get complete Customer 360 view with all journey data.

    Requires: crm:view permission
    """
    service = Customer360Service(db)

    result = await service.get_customer_360(
        customer_id=customer_id,
        include_timeline=include_timeline,
        limit_per_section=limit,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return result


@router.get(
    "/phone/{phone}/360",
    response_model=Customer360Response,
    dependencies=[Depends(require_permissions("crm:view"))],
    summary="Get Customer 360 View by Phone",
)
async def get_customer_360_by_phone(
    phone: str,
    db: DB,
    include_timeline: bool = Query(True, description="Include chronological timeline"),
    limit: int = Query(50, ge=1, le=200, description="Max records per section"),
):
    """
    Get complete Customer 360 view by phone number.

    Requires: crm:view permission
    """
    # First find customer by phone
    order_service = OrderService(db)
    customer = await order_service.get_customer_by_phone(phone)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    service = Customer360Service(db)
    result = await service.get_customer_360(
        customer_id=customer.id,
        include_timeline=include_timeline,
        limit_per_section=limit,
    )

    return result
