"""
Script to add expense and CAPEX permissions to the database.
Run: python scripts/add_expense_permissions.py
"""
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection settings from CLAUDE.md
DB_HOST = "db.aavjhutqzwusgdwrczds.supabase.co"
DB_PORT = 6543
DB_USER = "postgres"
DB_PASSWORD = "Aquapurite2026"
DB_NAME = "postgres"

# Module IDs (retrieved from /permissions/modules API)
FINANCE_MODULE_ID = "0cc2db4d-ed77-4924-a292-520ccd548a1a"
ASSETS_MODULE_ID = "d099fdd5-4e29-46b3-922f-cc1d303d550e"

# Expense Permissions (Finance Module)
EXPENSE_PERMISSIONS = [
    {"code": "EXPENSE_VIEW", "name": "View Expenses", "description": "View expense vouchers", "action": "read", "resource": "expenses"},
    {"code": "EXPENSE_CREATE", "name": "Create Expense", "description": "Create expense vouchers", "action": "create", "resource": "expenses"},
    {"code": "EXPENSE_EDIT", "name": "Edit Expense", "description": "Edit expense vouchers", "action": "update", "resource": "expenses"},
    {"code": "EXPENSE_DELETE", "name": "Delete Expense", "description": "Delete expense vouchers", "action": "delete", "resource": "expenses"},
    {"code": "EXPENSE_APPROVE", "name": "Approve Expense", "description": "Approve expense vouchers", "action": "approve", "resource": "expenses"},
    {"code": "EXPENSE_POST", "name": "Post Expense", "description": "Post expense vouchers to GL", "action": "post", "resource": "expenses"},
    {"code": "EXPENSE_CATEGORY_MANAGE", "name": "Manage Expense Categories", "description": "Create and edit expense categories", "action": "manage", "resource": "expense_categories"},
]

# CAPEX Permissions (Assets Module)
CAPEX_PERMISSIONS = [
    {"code": "CAPEX_VIEW", "name": "View CAPEX Requests", "description": "View capital expenditure requests", "action": "read", "resource": "capex"},
    {"code": "CAPEX_CREATE", "name": "Create CAPEX Request", "description": "Create capital expenditure requests", "action": "create", "resource": "capex"},
    {"code": "CAPEX_EDIT", "name": "Edit CAPEX Request", "description": "Edit capital expenditure requests", "action": "update", "resource": "capex"},
    {"code": "CAPEX_DELETE", "name": "Delete CAPEX Request", "description": "Delete capital expenditure requests", "action": "delete", "resource": "capex"},
    {"code": "CAPEX_APPROVE", "name": "Approve CAPEX Request", "description": "Approve capital expenditure requests", "action": "approve", "resource": "capex"},
]


def main():
    print("Connecting to Supabase...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
        sslmode='require'
    )
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Check if permissions already exist
        cur.execute("SELECT code FROM permissions WHERE code LIKE 'EXPENSE%' OR code LIKE 'CAPEX%'")
        existing = cur.fetchall()
        existing_codes = {r['code'] for r in existing}
        print(f"Existing permissions: {existing_codes}")

        # Insert Expense Permissions (Finance Module)
        print("\n--- Inserting Expense Permissions ---")
        for perm in EXPENSE_PERMISSIONS:
            if perm['code'] in existing_codes:
                print(f"  SKIP: {perm['code']} (already exists)")
                continue

            cur.execute("""
                INSERT INTO permissions (id, code, name, description, module_id, action, resource, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true, NOW(), NOW())
            """, (str(uuid.uuid4()), perm['code'], perm['name'], perm['description'],
                  FINANCE_MODULE_ID, perm['action'], perm['resource']))
            print(f"  ADDED: {perm['code']}")

        # Insert CAPEX Permissions (Assets Module)
        print("\n--- Inserting CAPEX Permissions ---")
        for perm in CAPEX_PERMISSIONS:
            if perm['code'] in existing_codes:
                print(f"  SKIP: {perm['code']} (already exists)")
                continue

            cur.execute("""
                INSERT INTO permissions (id, code, name, description, module_id, action, resource, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true, NOW(), NOW())
            """, (str(uuid.uuid4()), perm['code'], perm['name'], perm['description'],
                  ASSETS_MODULE_ID, perm['action'], perm['resource']))
            print(f"  ADDED: {perm['code']}")

        # Get Admin role ID
        print("\n--- Granting Permissions to Admin Role ---")
        cur.execute("SELECT id FROM roles WHERE name ILIKE '%admin%' ORDER BY created_at LIMIT 1")
        admin_role = cur.fetchone()

        if admin_role:
            admin_role_id = admin_role['id']
            print(f"Admin Role ID: {admin_role_id}")

            # Get all expense and capex permission IDs
            cur.execute("""
                SELECT id, code FROM permissions
                WHERE code LIKE 'EXPENSE%' OR code LIKE 'CAPEX%'
            """)
            new_perms = cur.fetchall()

            for perm in new_perms:
                # Check if already assigned
                cur.execute("""
                    SELECT 1 FROM role_permissions
                    WHERE role_id = %s AND permission_id = %s
                """, (admin_role_id, perm['id']))
                existing_rp = cur.fetchone()

                if existing_rp:
                    print(f"  SKIP: {perm['code']} (already assigned to Admin)")
                    continue

                cur.execute("""
                    INSERT INTO role_permissions (id, role_id, permission_id, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, (str(uuid.uuid4()), admin_role_id, perm['id']))
                print(f"  GRANTED: {perm['code']} to Admin role")
        else:
            print("WARNING: Admin role not found!")

        print("\n✅ Permissions setup complete!")

        # Verify
        print("\n--- Verification ---")
        cur.execute("""
            SELECT p.code, m.name as module_name
            FROM permissions p
            JOIN modules m ON p.module_id = m.id
            WHERE p.code LIKE 'EXPENSE%' OR p.code LIKE 'CAPEX%'
            ORDER BY p.code
        """)
        result = cur.fetchall()
        for r in result:
            print(f"  {r['code']} -> {r['module_name']}")

    finally:
        cur.close()
        conn.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()
