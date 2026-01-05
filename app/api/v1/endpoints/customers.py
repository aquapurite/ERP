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
    AddressCreate,
    AddressUpdate,
    AddressResponse,
)
from app.services.order_service import OrderService


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
