"""
Script to add expense and CAPEX permissions via the production API.
"""
import requests
import json

# API settings
BASE_URL = "https://aquapurite-erp-api.onrender.com"
EMAIL = "themanagingdirector@aquapurite.com"
PASSWORD = "Admin@123"

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


def main():
    # Login
    print("Logging in...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} - {resp.text}")
        return

    data = resp.json()
    token = data.get("access_token")
    if not token:
        print(f"No access token in response: {data}")
        return
    print(f"Login successful. Token: {token[:30]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # Check existing permissions
    print("\nFetching existing permissions...")
    resp = requests.get(f"{BASE_URL}/api/v1/permissions", headers=headers)
    if resp.status_code == 200:
        existing = resp.json()
        existing_codes = {p.get('code') for p in existing if isinstance(p, dict)}
        print(f"Found {len(existing_codes)} existing permissions")
    else:
        existing_codes = set()
        print(f"Could not fetch permissions: {resp.status_code}")

    # Add permissions
    all_perms = EXPENSE_PERMISSIONS + CAPEX_PERMISSIONS

    print(f"\n--- Adding {len(all_perms)} permissions ---")
    for perm in all_perms:
        if perm['code'] in existing_codes:
            print(f"  SKIP: {perm['code']} (already exists)")
            continue

        resp = requests.post(f"{BASE_URL}/api/v1/permissions", json=perm, headers=headers)
        if resp.status_code in [200, 201]:
            print(f"  ADDED: {perm['code']}")
        else:
            print(f"  FAILED: {perm['code']} - {resp.status_code} - {resp.text[:100]}")

    # Get Admin role
    print("\n--- Granting permissions to Admin role ---")
    resp = requests.get(f"{BASE_URL}/api/v1/roles", headers=headers)
    if resp.status_code == 200:
        result = resp.json()
        # Handle both list and dict with 'items' key
        if isinstance(result, dict) and 'items' in result:
            roles = result['items']
        elif isinstance(result, list):
            roles = result
        else:
            print(f"Unexpected roles response format: {type(result)}")
            roles = []

        admin_role = None
        for role in roles:
            if isinstance(role, dict) and 'admin' in role.get('name', '').lower():
                admin_role = role
                break

        if admin_role:
            admin_role_id = admin_role['id']
            print(f"Admin Role ID: {admin_role_id}")

            # Get all new permissions
            resp = requests.get(f"{BASE_URL}/api/v1/permissions", headers=headers)
            if resp.status_code == 200:
                all_permissions = resp.json()
                expense_capex_perms = [p for p in all_permissions if p.get('code', '').startswith(('EXPENSE', 'CAPEX'))]

                for perm in expense_capex_perms:
                    # Assign to role
                    resp = requests.post(
                        f"{BASE_URL}/api/v1/roles/{admin_role_id}/permissions",
                        json={"permission_id": perm['id']},
                        headers=headers
                    )
                    if resp.status_code in [200, 201]:
                        print(f"  GRANTED: {perm['code']} to Admin")
                    elif resp.status_code == 409:
                        print(f"  SKIP: {perm['code']} (already assigned)")
                    else:
                        print(f"  FAILED: {perm['code']} - {resp.status_code}")
        else:
            print("Admin role not found!")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
