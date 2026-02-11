"""
Script to add expense and CAPEX permissions via Supabase REST API.
"""
import requests
import uuid
import json

# Supabase settings
SUPABASE_URL = "https://aavjhutqzwusgdwrczds.supabase.co"
SUPABASE_SERVICE_KEY = None  # We'll use anon key + postgres password instead

# PostgreSQL connection info
DB_PASSWORD = "Aquapurite2026"

# Module IDs
FINANCE_MODULE_ID = "0cc2db4d-ed77-4924-a292-520ccd548a1a"
ASSETS_MODULE_ID = "d099fdd5-4e29-46b3-922f-cc1d303d550e"

# Permissions to add
EXPENSE_PERMISSIONS = [
    {"code": "EXPENSE_VIEW", "name": "View Expenses", "description": "View expense vouchers", "action": "read", "resource": "expenses", "module_id": FINANCE_MODULE_ID},
    {"code": "EXPENSE_CREATE", "name": "Create Expense", "description": "Create expense vouchers", "action": "create", "resource": "expenses", "module_id": FINANCE_MODULE_ID},
    {"code": "EXPENSE_EDIT", "name": "Edit Expense", "description": "Edit expense vouchers", "action": "update", "resource": "expenses", "module_id": FINANCE_MODULE_ID},
    {"code": "EXPENSE_DELETE", "name": "Delete Expense", "description": "Delete expense vouchers", "action": "delete", "resource": "expenses", "module_id": FINANCE_MODULE_ID},
    {"code": "EXPENSE_APPROVE", "name": "Approve Expense", "description": "Approve expense vouchers", "action": "approve", "resource": "expenses", "module_id": FINANCE_MODULE_ID},
    {"code": "EXPENSE_POST", "name": "Post Expense", "description": "Post expense vouchers to GL", "action": "post", "resource": "expenses", "module_id": FINANCE_MODULE_ID},
    {"code": "EXPENSE_CATEGORY_MANAGE", "name": "Manage Expense Categories", "description": "Create and edit expense categories", "action": "manage", "resource": "expense_categories", "module_id": FINANCE_MODULE_ID},
]

CAPEX_PERMISSIONS = [
    {"code": "CAPEX_VIEW", "name": "View CAPEX Requests", "description": "View capital expenditure requests", "action": "read", "resource": "capex", "module_id": ASSETS_MODULE_ID},
    {"code": "CAPEX_CREATE", "name": "Create CAPEX Request", "description": "Create capital expenditure requests", "action": "create", "resource": "capex", "module_id": ASSETS_MODULE_ID},
    {"code": "CAPEX_EDIT", "name": "Edit CAPEX Request", "description": "Edit capital expenditure requests", "action": "update", "resource": "capex", "module_id": ASSETS_MODULE_ID},
    {"code": "CAPEX_DELETE", "name": "Delete CAPEX Request", "description": "Delete capital expenditure requests", "action": "delete", "resource": "capex", "module_id": ASSETS_MODULE_ID},
    {"code": "CAPEX_APPROVE", "name": "Approve CAPEX Request", "description": "Approve capital expenditure requests", "action": "approve", "resource": "capex", "module_id": ASSETS_MODULE_ID},
]


def get_supabase_service_key():
    """Read the Supabase service key from environment or config."""
    # Try reading from .env.local
    try:
        with open("/Users/mantosh/Desktop/Consumer durable 2/.env.local", "r") as f:
            for line in f:
                if line.startswith("SUPABASE_SERVICE_KEY="):
                    return line.strip().split("=", 1)[1].strip('"').strip("'")
    except FileNotFoundError:
        pass

    # Try environment variable
    import os
    return os.environ.get("SUPABASE_SERVICE_KEY")


def main():
    service_key = get_supabase_service_key()
    if not service_key:
        print("ERROR: Could not find SUPABASE_SERVICE_KEY")
        print("Please set it in .env.local or as an environment variable")
        return

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    # Check existing permissions
    print("Checking existing permissions...")
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/permissions",
        headers=headers,
        params={"select": "code", "or": "(code.like.EXPENSE%,code.like.CAPEX%)"}
    )

    if resp.status_code == 200:
        existing = resp.json()
        existing_codes = {p['code'] for p in existing}
        print(f"Existing permissions: {existing_codes}")
    else:
        print(f"Warning: Could not fetch existing permissions: {resp.status_code} - {resp.text}")
        existing_codes = set()

    # Add permissions
    all_perms = EXPENSE_PERMISSIONS + CAPEX_PERMISSIONS

    print(f"\n--- Adding {len(all_perms)} permissions ---")
    for perm in all_perms:
        if perm['code'] in existing_codes:
            print(f"  SKIP: {perm['code']} (already exists)")
            continue

        data = {
            "id": str(uuid.uuid4()),
            "code": perm['code'],
            "name": perm['name'],
            "description": perm['description'],
            "module_id": perm['module_id'],
            "action": perm['action'],
            "resource": perm['resource'],
            "is_active": True,
        }

        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/permissions",
            headers=headers,
            json=data
        )

        if resp.status_code in [200, 201]:
            print(f"  ADDED: {perm['code']}")
        else:
            print(f"  FAILED: {perm['code']} - {resp.status_code} - {resp.text[:200]}")

    # Get Admin role
    print("\n--- Granting permissions to Admin role ---")
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/roles",
        headers=headers,
        params={"select": "id,name", "name": "ilike.*admin*", "limit": 1}
    )

    if resp.status_code == 200 and resp.json():
        admin_role = resp.json()[0]
        admin_role_id = admin_role['id']
        print(f"Admin Role ID: {admin_role_id}")

        # Get all expense and capex permission IDs
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/permissions",
            headers=headers,
            params={"select": "id,code", "or": "(code.like.EXPENSE%,code.like.CAPEX%)"}
        )

        if resp.status_code == 200:
            perms = resp.json()

            for perm in perms:
                # Check if already assigned
                resp = requests.get(
                    f"{SUPABASE_URL}/rest/v1/role_permissions",
                    headers=headers,
                    params={
                        "select": "id",
                        "role_id": f"eq.{admin_role_id}",
                        "permission_id": f"eq.{perm['id']}"
                    }
                )

                if resp.status_code == 200 and resp.json():
                    print(f"  SKIP: {perm['code']} (already assigned)")
                    continue

                # Assign permission to role
                data = {
                    "id": str(uuid.uuid4()),
                    "role_id": admin_role_id,
                    "permission_id": perm['id'],
                }
                resp = requests.post(
                    f"{SUPABASE_URL}/rest/v1/role_permissions",
                    headers=headers,
                    json=data
                )

                if resp.status_code in [200, 201]:
                    print(f"  GRANTED: {perm['code']} to Admin")
                elif "duplicate key" in resp.text.lower() or resp.status_code == 409:
                    print(f"  SKIP: {perm['code']} (already assigned)")
                else:
                    print(f"  FAILED: {perm['code']} - {resp.status_code} - {resp.text[:100]}")
    else:
        print(f"Admin role not found or error: {resp.status_code}")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
