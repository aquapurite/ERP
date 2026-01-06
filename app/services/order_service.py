from typing import List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from math import ceil
import uuid

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer, CustomerAddress
from app.models.order import (
    Order, OrderItem, OrderStatus, OrderStatusHistory,
    Payment, PaymentStatus, PaymentMethod, OrderSource, Invoice
)
from app.models.product import Product, ProductVariant
from app.schemas.order import OrderCreate, OrderUpdate, OrderItemCreate


class OrderService:
    """Service for managing orders and related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== ORDER NUMBER GENERATION ====================

    async def generate_order_number(self) -> str:
        """Generate unique order number: ORD-YYYYMMDD-XXXX"""
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"ORD-{today}-"

        # Get count of orders today
        stmt = select(func.count(Order.id)).where(
            Order.order_number.like(f"{prefix}%")
        )
        count = (await self.db.execute(stmt)).scalar() or 0

        return f"{prefix}{(count + 1):04d}"

    async def generate_invoice_number(self) -> str:
        """Generate unique invoice number: INV-YYYYMMDD-XXXX"""
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"INV-{today}-"

        stmt = select(func.count(Invoice.id)).where(
            Invoice.invoice_number.like(f"{prefix}%")
        )
        count = (await self.db.execute(stmt)).scalar() or 0

        return f"{prefix}{(count + 1):04d}"

    # ==================== CUSTOMER METHODS ====================

    async def generate_customer_code(self) -> str:
        """Generate unique customer code: CUST-XXXXX"""
        stmt = select(func.count(Customer.id))
        count = (await self.db.execute(stmt)).scalar() or 0
        return f"CUST-{(count + 1):05d}"

    async def get_customers(
        self,
        search: Optional[str] = None,
        customer_type: Optional[str] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Customer], int]:
        """Get paginated customers."""
        stmt = (
            select(Customer)
            .options(selectinload(Customer.addresses))
            .order_by(Customer.created_at.desc())
        )

        filters = []
        if is_active is not None:
            filters.append(Customer.is_active == is_active)

        if customer_type:
            filters.append(Customer.customer_type == customer_type)

        if search:
            search_filter = f"%{search}%"
            filters.append(
                or_(
                    Customer.first_name.ilike(search_filter),
                    Customer.last_name.ilike(search_filter),
                    Customer.phone.ilike(search_filter),
                    Customer.email.ilike(search_filter),
                    Customer.customer_code.ilike(search_filter),
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        # Count
        count_stmt = select(func.count(Customer.id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total = (await self.db.execute(count_stmt)).scalar()

        # Paginate
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        customers = result.scalars().unique().all()

        return list(customers), total

    async def get_customer_by_id(self, customer_id: uuid.UUID) -> Optional[Customer]:
        """Get customer by ID."""
        stmt = (
            select(Customer)
            .options(selectinload(Customer.addresses))
            .where(Customer.id == customer_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Get customer by phone."""
        stmt = (
            select(Customer)
            .options(selectinload(Customer.addresses))
            .where(Customer.phone == phone)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_customer(self, data: dict) -> Customer:
        """Create a new customer."""
        addresses_data = data.pop("addresses", [])
        customer_code = await self.generate_customer_code()

        customer = Customer(customer_code=customer_code, **data)
        self.db.add(customer)
        await self.db.flush()

        # Add addresses
        for addr_data in addresses_data:
            address = CustomerAddress(customer_id=customer.id, **addr_data)
            self.db.add(address)

        await self.db.commit()
        return await self.get_customer_by_id(customer.id)

    async def update_customer(
        self,
        customer_id: uuid.UUID,
        data: dict
    ) -> Optional[Customer]:
        """Update a customer."""
        customer = await self.get_customer_by_id(customer_id)
        if not customer:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(customer, key, value)

        await self.db.commit()
        return await self.get_customer_by_id(customer_id)

    # ==================== ORDER METHODS ====================

    async def get_orders(
        self,
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[OrderStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        source: Optional[OrderSource] = None,
        region_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Order], int]:
        """Get paginated orders with filters."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.items),
            )
        )

        filters = []

        if customer_id:
            filters.append(Order.customer_id == customer_id)

        if status:
            filters.append(Order.status == status)

        if payment_status:
            filters.append(Order.payment_status == payment_status)

        if source:
            filters.append(Order.source == source)

        if region_id:
            filters.append(Order.region_id == region_id)

        if date_from:
            filters.append(Order.created_at >= date_from)

        if date_to:
            filters.append(Order.created_at <= date_to)

        if search:
            search_filter = f"%{search}%"
            filters.append(
                or_(
                    Order.order_number.ilike(search_filter),
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        # Count
        count_stmt = select(func.count(Order.id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total = (await self.db.execute(count_stmt)).scalar()

        # Sort
        sort_column = getattr(Order, sort_by, Order.created_at)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Paginate
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        orders = result.scalars().unique().all()

        return list(orders), total

    async def get_order_by_id(
        self,
        order_id: uuid.UUID,
        include_all: bool = False
    ) -> Optional[Order]:
        """Get order by ID."""
        stmt = select(Order).where(Order.id == order_id)

        if include_all:
            stmt = stmt.options(
                selectinload(Order.customer),
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.status_history),
                selectinload(Order.payments),
                selectinload(Order.invoice),
            )
        else:
            stmt = stmt.options(
                selectinload(Order.customer),
                selectinload(Order.items),
            )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.items),
                selectinload(Order.status_history),
                selectinload(Order.payments),
                selectinload(Order.invoice),
            )
            .where(Order.order_number == order_number)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_order(
        self,
        data: OrderCreate,
        created_by: Optional[uuid.UUID] = None
    ) -> Order:
        """Create a new order."""
        # Generate order number
        order_number = await self.generate_order_number()

        # Get customer
        customer = await self.get_customer_by_id(data.customer_id)
        if not customer:
            raise ValueError("Customer not found")

        # Process shipping address
        shipping_address = await self._process_address(
            data.shipping_address,
            customer
        )

        # Process billing address
        billing_address = None
        if data.billing_address:
            billing_address = await self._process_address(
                data.billing_address,
                customer
            )

        # Calculate totals
        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")
        items_data = []

        for item_data in data.items:
            product = await self._get_product(item_data.product_id)
            if not product:
                raise ValueError(f"Product {item_data.product_id} not found")

            variant = None
            if item_data.variant_id:
                variant = await self._get_variant(item_data.variant_id)

            # Determine prices
            unit_price = item_data.unit_price or product.selling_price
            unit_mrp = product.mrp

            if variant:
                if variant.selling_price:
                    unit_price = item_data.unit_price or variant.selling_price
                if variant.mrp:
                    unit_mrp = variant.mrp

            # Calculate item totals
            item_subtotal = unit_price * item_data.quantity
            item_tax_rate = product.gst_rate or Decimal("18.00")
            item_tax = (item_subtotal * item_tax_rate) / 100
            item_total = item_subtotal + item_tax

            items_data.append({
                "product": product,
                "variant": variant,
                "quantity": item_data.quantity,
                "unit_price": unit_price,
                "unit_mrp": unit_mrp,
                "tax_rate": item_tax_rate,
                "tax_amount": item_tax,
                "total_amount": item_total,
            })

            subtotal += item_subtotal
            tax_amount += item_tax

        total_amount = subtotal + tax_amount

        # Create order
        order = Order(
            order_number=order_number,
            customer_id=data.customer_id,
            source=data.source,
            status=OrderStatus.NEW,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=Decimal("0.00"),
            shipping_amount=Decimal("0.00"),
            total_amount=total_amount,
            discount_code=data.discount_code,
            payment_method=data.payment_method,
            payment_status=PaymentStatus.PENDING,
            shipping_address=shipping_address,
            billing_address=billing_address,
            customer_notes=data.customer_notes,
            internal_notes=data.internal_notes,
            region_id=data.region_id,
            created_by=created_by,
        )
        self.db.add(order)
        await self.db.flush()

        # Create order items
        for item in items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product"].id,
                variant_id=item["variant"].id if item["variant"] else None,
                product_name=item["product"].name,
                product_sku=item["product"].sku,
                variant_name=item["variant"].name if item["variant"] else None,
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                unit_mrp=item["unit_mrp"],
                tax_rate=item["tax_rate"],
                tax_amount=item["tax_amount"],
                total_amount=item["total_amount"],
                hsn_code=item["product"].hsn_code,
                warranty_months=item["product"].warranty_months,
            )
            self.db.add(order_item)

        # Create initial status history
        status_history = OrderStatusHistory(
            order_id=order.id,
            from_status=None,
            to_status=OrderStatus.NEW,
            changed_by=created_by,
            notes="Order created",
        )
        self.db.add(status_history)

        await self.db.commit()
        return await self.get_order_by_id(order.id, include_all=True)

    async def update_order_status(
        self,
        order_id: uuid.UUID,
        new_status: OrderStatus,
        changed_by: Optional[uuid.UUID] = None,
        notes: Optional[str] = None
    ) -> Optional[Order]:
        """Update order status."""
        order = await self.get_order_by_id(order_id)
        if not order:
            return None

        old_status = order.status
        order.status = new_status

        # Update timestamps based on status
        if new_status == OrderStatus.CONFIRMED:
            order.confirmed_at = datetime.utcnow()
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.utcnow()
        elif new_status == OrderStatus.CANCELLED:
            order.cancelled_at = datetime.utcnow()

        # Create status history
        status_history = OrderStatusHistory(
            order_id=order.id,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            notes=notes,
        )
        self.db.add(status_history)

        await self.db.commit()
        return await self.get_order_by_id(order_id, include_all=True)

    async def add_payment(
        self,
        order_id: uuid.UUID,
        amount: Decimal,
        method: PaymentMethod,
        transaction_id: Optional[str] = None,
        gateway: Optional[str] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Payment:
        """Add a payment to an order."""
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        payment = Payment(
            order_id=order_id,
            amount=amount,
            method=method,
            status=PaymentStatus.CAPTURED,
            transaction_id=transaction_id,
            gateway=gateway,
            reference_number=reference_number,
            notes=notes,
            completed_at=datetime.utcnow(),
        )
        self.db.add(payment)

        # Update order payment status
        order.amount_paid += amount
        if order.amount_paid >= order.total_amount:
            order.payment_status = PaymentStatus.PAID
        elif order.amount_paid > 0:
            order.payment_status = PaymentStatus.PARTIALLY_PAID

        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def generate_invoice(self, order_id: uuid.UUID) -> Invoice:
        """Generate invoice for an order."""
        order = await self.get_order_by_id(order_id, include_all=True)
        if not order:
            raise ValueError("Order not found")

        if order.invoice:
            return order.invoice

        invoice_number = await self.generate_invoice_number()

        # Calculate tax split (assuming same state = CGST+SGST, else IGST)
        cgst = order.tax_amount / 2
        sgst = order.tax_amount / 2
        igst = Decimal("0.00")

        invoice = Invoice(
            order_id=order.id,
            invoice_number=invoice_number,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            cgst_amount=cgst,
            sgst_amount=sgst,
            igst_amount=igst,
            invoice_date=datetime.utcnow(),
        )
        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    # ==================== HELPER METHODS ====================

    async def _process_address(self, address_input, customer: Customer) -> dict:
        """Process address input and return address dict."""
        if address_input.address_id:
            # Find existing address
            for addr in customer.addresses:
                if addr.id == address_input.address_id:
                    return {
                        "contact_name": addr.contact_name or customer.full_name,
                        "contact_phone": addr.contact_phone or customer.phone,
                        "address_line1": addr.address_line1,
                        "address_line2": addr.address_line2,
                        "landmark": addr.landmark,
                        "city": addr.city,
                        "state": addr.state,
                        "pincode": addr.pincode,
                        "country": addr.country,
                    }

        # Use provided address data
        return {
            "contact_name": address_input.contact_name or customer.full_name,
            "contact_phone": address_input.contact_phone or customer.phone,
            "address_line1": address_input.address_line1,
            "address_line2": address_input.address_line2,
            "landmark": address_input.landmark,
            "city": address_input.city,
            "state": address_input.state,
            "pincode": address_input.pincode,
            "country": "India",
        }

    async def _get_product(self, product_id: uuid.UUID) -> Optional[Product]:
        """Get product by ID."""
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_variant(self, variant_id: uuid.UUID) -> Optional[ProductVariant]:
        """Get variant by ID."""
        stmt = select(ProductVariant).where(ProductVariant.id == variant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ==================== STATISTICS ====================

    async def get_order_stats(
        self,
        region_id: Optional[uuid.UUID] = None
    ) -> dict:
        """Get order statistics."""
        base_filter = []
        if region_id:
            base_filter.append(Order.region_id == region_id)

        # Total orders
        total_stmt = select(func.count(Order.id))
        if base_filter:
            total_stmt = total_stmt.where(and_(*base_filter))
        total_orders = (await self.db.execute(total_stmt)).scalar() or 0

        # By status
        status_counts = {}
        for status in [OrderStatus.NEW, OrderStatus.CONFIRMED,
                       OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            stmt = select(func.count(Order.id)).where(Order.status == status)
            if base_filter:
                stmt = stmt.where(and_(*base_filter))
            status_counts[status.value] = (await self.db.execute(stmt)).scalar() or 0

        # Revenue
        revenue_stmt = select(func.sum(Order.total_amount)).where(
            Order.payment_status == PaymentStatus.PAID
        )
        if base_filter:
            revenue_stmt = revenue_stmt.where(and_(*base_filter))
        total_revenue = (await self.db.execute(revenue_stmt)).scalar() or Decimal("0.00")

        # Average order value
        avg_stmt = select(func.avg(Order.total_amount))
        if base_filter:
            avg_stmt = avg_stmt.where(and_(*base_filter))
        avg_order_value = (await self.db.execute(avg_stmt)).scalar() or Decimal("0.00")

        return {
            "total_orders": total_orders,
            "pending_orders": status_counts.get("PENDING", 0),
            "processing_orders": status_counts.get("PROCESSING", 0),
            "delivered_orders": status_counts.get("DELIVERED", 0),
            "cancelled_orders": status_counts.get("CANCELLED", 0),
            "total_revenue": float(total_revenue),
            "average_order_value": float(avg_order_value),
        }
