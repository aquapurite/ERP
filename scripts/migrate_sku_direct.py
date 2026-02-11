"""
SKU Migration Script (Direct Database Connection)

Migrates old SKU format to new standardized format.
Uses asyncpg directly without requiring full app setup.

Usage:
    python3 scripts/migrate_sku_direct.py --dry-run    # Preview changes
    python3 scripts/migrate_sku_direct.py              # Execute migration
"""

import asyncio
import argparse
from datetime import datetime

# Database connection string (Supabase production)
DATABASE_URL = "postgresql://postgres:Aquapurite2026@db.aavjhutqzwusgdwrczds.supabase.co:6543/postgres"


async def run_migration(dry_run=True):
    """Run the SKU migration"""
    try:
        import asyncpg
    except ImportError:
        print("Installing asyncpg...")
        import subprocess
        subprocess.run(['pip3', 'install', 'asyncpg'], check=True)
        import asyncpg

    print(f"\n{'='*80}")
    print(f"SKU MIGRATION {'(DRY RUN)' if dry_run else '(LIVE)'}")
    print(f"{'='*80}")
    print(f"Started at: {datetime.now().isoformat()}\n")

    conn = await asyncpg.connect(DATABASE_URL, statement_cache_size=0)

    try:
        # Get category hierarchy
        print("Loading category hierarchy...")
        cat_rows = await conn.fetch('''
            SELECT
                c.id as cat_id,
                c.code as cat_code,
                c.name as cat_name,
                p.id as parent_id,
                p.code as parent_code,
                p.name as parent_name
            FROM categories c
            LEFT JOIN categories p ON c.parent_id = p.id
        ''')

        category_hierarchy = {}
        for row in cat_rows:
            cat_id = str(row['cat_id'])
            cat_code = row['cat_code'] or 'XX'
            parent_code = row['parent_code'] or cat_code
            category_hierarchy[cat_id] = {
                'cat_code': cat_code,
                'parent_code': parent_code,
                'cat_name': row['cat_name'],
                'parent_name': row['parent_name'] or row['cat_name']
            }

        # Get brand codes
        print("Loading brand codes...")
        brand_rows = await conn.fetch('SELECT id, code, name FROM brands')
        brand_codes = {str(row['id']): row['code'] or 'XX' for row in brand_rows}

        # Get products to migrate (those NOT in new format)
        print("Finding products to migrate...\n")
        products = await conn.fetch('''
            SELECT
                p.id,
                p.sku,
                p.name,
                p.model_code,
                p.item_type,
                p.category_id,
                p.brand_id
            FROM products p
            WHERE p.sku NOT LIKE 'AP-%-%-%-%-___'
              AND p.sku NOT LIKE 'AP-%-%-%-___'
            ORDER BY p.created_at
        ''')

        if not products:
            print("✓ No products need migration. All SKUs are already in new format.")
            return []

        print(f"Found {len(products)} products to migrate:\n")

        # Track SKU counters for sequence numbers
        sku_counters = {}

        # Migration report
        migration_report = []

        print(f"{'Old SKU':<25} {'→':<3} {'New SKU':<30} {'Product Name':<40}")
        print("-" * 100)

        for product in products:
            product_id = str(product['id'])
            old_sku = product['sku']
            product_name = product['name']
            model_code = product['model_code'] or 'XXX'
            item_type = product['item_type'] or 'FG'
            category_id = str(product['category_id'])
            brand_id = str(product['brand_id'])

            # Get brand code
            brand_code = brand_codes.get(brand_id, 'XX')

            # Get category hierarchy
            cat_info = category_hierarchy.get(category_id, {})
            parent_code = cat_info.get('parent_code', 'XX')
            subcat_code = cat_info.get('cat_code', 'XX')

            # Build SKU prefix
            if parent_code == 'SP' or item_type == 'SP':
                # Spare Parts: No item_type in SKU
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

            migration_report.append({
                'product_id': product_id,
                'old_sku': old_sku,
                'new_sku': new_sku,
                'product_name': product_name
            })

            print(f"{old_sku:<25} {'→':<3} {new_sku:<30} {product_name[:40]:<40}")

            if not dry_run:
                # Update product SKU
                await conn.execute('''
                    UPDATE products
                    SET sku = $1, updated_at = NOW()
                    WHERE id = $2
                ''', new_sku, product['id'])

                # Update model_code_references
                await conn.execute('''
                    UPDATE model_code_references
                    SET product_sku = $1, updated_at = NOW()
                    WHERE product_id = $2
                ''', new_sku, product['id'])

                # Update product_serial_sequences
                await conn.execute('''
                    UPDATE product_serial_sequences
                    SET product_sku = $1, updated_at = NOW()
                    WHERE product_id = $2
                ''', new_sku, product['id'])

        if not dry_run:
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

        # Print migration table for records
        print(f"\n{'='*80}")
        print("MIGRATION MAPPING TABLE (for your records)")
        print(f"{'='*80}")
        print(f"| {'Old SKU':<25} | {'New SKU':<30} |")
        print(f"|{'-'*27}|{'-'*32}|")
        for item in migration_report:
            print(f"| {item['old_sku']:<25} | {item['new_sku']:<30} |")

        return migration_report

    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser(description='Migrate product SKUs to new format')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    args = parser.parse_args()

    asyncio.run(run_migration(dry_run=args.dry_run))


if __name__ == '__main__':
    main()
