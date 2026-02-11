"""
SKU Migration Script

Migrates old SKU format to new standardized format:
- Old FG: WPRAOPT001 → New: AP-WP-RU-FG-OPT-001
- Old SP: SPECPOC001 → New: AP-SP-EC-POC-001

New SKU Format:
- FG: BRAND-PRODUCTLINE-SUBCAT-ITEMTYPE-MODEL-SEQ (e.g., AP-WP-RU-FG-OPT-001)
- SP: BRAND-PRODUCTLINE-SUBCAT-MODEL-SEQ (e.g., AP-SP-EC-POC-001)

Note: Spare Parts (SP) don't include item_type since the product line IS SP.

Usage:
    python scripts/migrate_sku.py --dry-run    # Preview changes
    python scripts/migrate_sku.py              # Execute migration
"""

import asyncio
import argparse
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, '/Users/mantosh/Desktop/Consumer durable 2')


async def get_category_hierarchy(db):
    """Build category hierarchy map: subcategory_id -> (parent_code, subcat_code)"""
    from sqlalchemy import select, text

    result = await db.execute(text('''
        SELECT
            c.id as cat_id,
            c.code as cat_code,
            c.name as cat_name,
            p.id as parent_id,
            p.code as parent_code,
            p.name as parent_name
        FROM categories c
        LEFT JOIN categories p ON c.parent_id = p.id
    '''))

    hierarchy = {}
    for row in result.fetchall():
        cat_id = str(row[0])
        cat_code = row[1] or 'XX'
        parent_code = row[4] or cat_code  # If no parent, use own code
        hierarchy[cat_id] = {
            'cat_code': cat_code,
            'parent_code': parent_code,
            'cat_name': row[2],
            'parent_name': row[5] or row[2]
        }
    return hierarchy


async def get_brand_codes(db):
    """Get brand code map: brand_id -> brand_code"""
    from sqlalchemy import text

    result = await db.execute(text('SELECT id, code, name FROM brands'))
    return {str(row[0]): row[1] or 'XX' for row in result.fetchall()}


async def get_products_to_migrate(db):
    """Get all products that need SKU migration"""
    from sqlalchemy import text

    result = await db.execute(text('''
        SELECT
            p.id,
            p.sku,
            p.name,
            p.model_code,
            p.item_type,
            p.category_id,
            p.brand_id,
            c.code as cat_code,
            c.name as cat_name,
            b.code as brand_code,
            b.name as brand_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        JOIN brands b ON p.brand_id = b.id
        WHERE p.sku NOT LIKE 'AP-%-%-%-%-___'
          AND p.sku NOT LIKE 'AP-%-%-%-___'
        ORDER BY p.created_at
    '''))

    return result.fetchall()


def generate_new_sku(product, category_hierarchy, brand_codes, sku_counters):
    """
    Generate new SKU for a product.

    Format:
    - FG: BRAND-PRODUCTLINE-SUBCAT-ITEMTYPE-MODEL-SEQ
    - SP: BRAND-PRODUCTLINE-SUBCAT-MODEL-SEQ (no item type)
    """
    product_id = str(product[0])
    old_sku = product[1]
    model_code = product[3] or 'XXX'
    item_type = product[4] or 'FG'
    category_id = str(product[5])
    brand_id = str(product[6])

    # Get brand code
    brand_code = brand_codes.get(brand_id, 'XX')

    # Get category hierarchy
    cat_info = category_hierarchy.get(category_id, {})
    parent_code = cat_info.get('parent_code', 'XX')
    subcat_code = cat_info.get('cat_code', 'XX')

    # Build SKU prefix
    if parent_code == 'SP' or item_type == 'SP':
        # Spare Parts: No item_type in SKU (product line IS SP)
        sku_prefix = f"{brand_code}-{parent_code}-{subcat_code}-{model_code}"
    else:
        # Finished Goods: Include item_type
        sku_prefix = f"{brand_code}-{parent_code}-{subcat_code}-{item_type}-{model_code}"

    # Get next sequence number for this prefix
    if sku_prefix not in sku_counters:
        sku_counters[sku_prefix] = 0
    sku_counters[sku_prefix] += 1
    seq = sku_counters[sku_prefix]

    new_sku = f"{sku_prefix}-{str(seq).zfill(3)}"

    return new_sku


async def update_product_sku(db, product_id, new_sku):
    """Update product SKU in database"""
    from sqlalchemy import text

    await db.execute(text('''
        UPDATE products
        SET sku = :new_sku, updated_at = NOW()
        WHERE id = :product_id
    '''), {'new_sku': new_sku, 'product_id': product_id})


async def update_serialization_tables(db, product_id, new_sku):
    """Update SKU in serialization-related tables"""
    from sqlalchemy import text

    # Update model_code_references
    await db.execute(text('''
        UPDATE model_code_references
        SET product_sku = :new_sku, updated_at = NOW()
        WHERE product_id = :product_id
    '''), {'new_sku': new_sku, 'product_id': product_id})

    # Update product_serial_sequences
    await db.execute(text('''
        UPDATE product_serial_sequences
        SET product_sku = :new_sku, updated_at = NOW()
        WHERE product_id = :product_id
    '''), {'new_sku': new_sku, 'product_id': product_id})


async def run_migration(dry_run=True):
    """Run the SKU migration"""
    from app.database import async_session_maker

    print(f"\n{'='*80}")
    print(f"SKU MIGRATION {'(DRY RUN)' if dry_run else '(LIVE)'}")
    print(f"{'='*80}")
    print(f"Started at: {datetime.now().isoformat()}\n")

    async with async_session_maker() as db:
        # Get lookup data
        print("Loading category hierarchy...")
        category_hierarchy = await get_category_hierarchy(db)

        print("Loading brand codes...")
        brand_codes = await get_brand_codes(db)

        # Get products to migrate
        print("Finding products to migrate...\n")
        products = await get_products_to_migrate(db)

        if not products:
            print("✓ No products need migration. All SKUs are already in new format.")
            return

        print(f"Found {len(products)} products to migrate:\n")

        # Track SKU counters for sequence numbers
        sku_counters = {}

        # Migration report
        migration_report = []

        print(f"{'Old SKU':<25} {'→':<3} {'New SKU':<30} {'Product Name':<40}")
        print("-" * 100)

        for product in products:
            product_id = str(product[0])
            old_sku = product[1]
            product_name = product[2]

            new_sku = generate_new_sku(product, category_hierarchy, brand_codes, sku_counters)

            migration_report.append({
                'product_id': product_id,
                'old_sku': old_sku,
                'new_sku': new_sku,
                'product_name': product_name
            })

            print(f"{old_sku:<25} {'→':<3} {new_sku:<30} {product_name[:40]:<40}")

            if not dry_run:
                await update_product_sku(db, product_id, new_sku)
                await update_serialization_tables(db, product_id, new_sku)

        if not dry_run:
            await db.commit()
            print(f"\n✓ Migration complete! {len(products)} products updated.")
        else:
            print(f"\n⚠ DRY RUN - No changes made. Run without --dry-run to apply changes.")

        # Print summary
        print(f"\n{'='*80}")
        print("MIGRATION SUMMARY")
        print(f"{'='*80}")
        print(f"Total products migrated: {len(products)}")
        print(f"Unique SKU prefixes: {len(sku_counters)}")
        print(f"\nSKU Prefix Counts:")
        for prefix, count in sorted(sku_counters.items()):
            print(f"  {prefix}: {count} product(s)")

        return migration_report


def main():
    parser = argparse.ArgumentParser(description='Migrate product SKUs to new format')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    args = parser.parse_args()

    asyncio.run(run_migration(dry_run=args.dry_run))


if __name__ == '__main__':
    main()
