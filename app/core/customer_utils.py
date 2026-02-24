"""
Centralized customer code generation utility.
All customer creation paths must use this to ensure consistent CUST-XXXXX format.
"""
import re
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer


async def generate_customer_code(db: AsyncSession) -> str:
    """
    Generate unique customer code in CUST-XXXXX format.
    Uses MAX(customer_code) on CUST-XXXXX pattern to find next sequential number.
    """
    # Find the highest existing CUST-XXXXX code
    stmt = select(Customer.customer_code).where(
        Customer.customer_code.regexp_match(r'^CUST-\d{5}$')
    ).order_by(Customer.customer_code.desc()).limit(1)

    result = await db.execute(stmt)
    last_code = result.scalar_one_or_none()

    if last_code:
        # Extract number from CUST-XXXXX
        match = re.search(r'CUST-(\d{5})', last_code)
        next_num = int(match.group(1)) + 1 if match else 1
    else:
        # No CUST-XXXXX codes exist yet, start from 1
        # But check total customer count to avoid collision with legacy codes
        count_stmt = select(func.count(Customer.id))
        count = (await db.execute(count_stmt)).scalar() or 0
        next_num = count + 1

    return f"CUST-{next_num:05d}"
